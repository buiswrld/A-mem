"""Tests for the probe-clustered bootstrap.

The property worth protecting is the clustering itself. A bootstrap that
resamples rows instead of probes still runs, still prints an interval, and is
wrong by roughly sqrt(samples-per-probe) -- so the test that matters is the one
that fails if someone "simplifies" the resampling unit back to the row.
"""

from __future__ import annotations

import math

import pytest

from harness.stats import (
    DEGENERATE_EPS,
    Interval,
    bootstrap,
    cluster_verdicts,
    _pct,
    _shared_probe_ids,
)

TIER = "D"  # refusals count as aligned; excluded rows leave the denominator


def rows(condition, spec, tier=TIER):
    """spec: {probe_id: [verdicts]} -> the row dicts bootstrap() consumes."""
    return [{"condition": condition, "tier": tier, "probe_id": pid, "verdict": v}
            for pid, vs in spec.items() for v in vs]


def split(n_probes, n_per, n_bad):
    """`n_bad` fully-misaligned probes, the rest fully aligned. ICC = 1."""
    return {f"p{i:03d}": ["misaligned" if i < n_bad else "aligned"] * n_per
            for i in range(n_probes)}


# --------------------------------------------------------------------------
# the clustering
# --------------------------------------------------------------------------


def test_clusters_group_by_probe_not_by_row():
    c = cluster_verdicts(rows("C1", {"p1": ["aligned", "misaligned"], "p2": ["aligned"]}))
    assert c == {"p1": ["aligned", "misaligned"], "p2": ["aligned"]}


def test_extra_samples_per_probe_barely_narrow_the_interval():
    """The regression guard: at ICC = 1, more samples per probe add nothing.

    Every probe here is internally unanimous, so a response carries no
    information its probe has not already given. A row-resampling bootstrap
    would narrow the interval by ~sqrt(10) going from 1 sample to 10; a
    probe-clustered one must not move materially at all.
    """
    narrow = {}
    for n_per in (1, 10):
        harm, _ = bootstrap({"C1": rows("C1", split(40, n_per, 20))}, TIER,
                            n_boot=400, seed=0)
        narrow[n_per] = harm["C1"].pct_hi - harm["C1"].pct_lo

    assert narrow[1] == pytest.approx(narrow[10], abs=0.02), (
        f"width moved from {narrow[1]:.3f} to {narrow[10]:.3f} when only the "
        "samples-per-probe changed -- the resampling unit is not the probe")


def test_more_probes_do_narrow_the_interval():
    """The other half: probe count is what buys precision."""
    widths = {}
    for n_probes in (20, 80):
        harm, _ = bootstrap({"C1": rows("C1", split(n_probes, 5, n_probes // 2))},
                            TIER, n_boot=400, seed=0)
        widths[n_probes] = harm["C1"].pct_hi - harm["C1"].pct_lo
    assert widths[80] < widths[20] * 0.75


# --------------------------------------------------------------------------
# the statistics
# --------------------------------------------------------------------------


def test_point_estimate_matches_the_unresampled_rate():
    harm, _ = bootstrap({"C1": rows("C1", split(50, 4, 20))}, TIER, n_boot=200, seed=0)
    assert harm["C1"].point == pytest.approx(0.4)


def test_interval_brackets_the_point_estimate():
    harm, _ = bootstrap({"C1": rows("C1", split(60, 5, 25))}, TIER, n_boot=500, seed=0)
    iv = harm["C1"]
    assert iv.pct_lo <= iv.point <= iv.pct_hi
    assert iv.bca_lo <= iv.point <= iv.bca_hi


def test_same_seed_reproduces_the_interval():
    data = {"C1": rows("C1", split(40, 5, 18))}
    a, _ = bootstrap(data, TIER, n_boot=300, seed=7)
    b, _ = bootstrap(data, TIER, n_boot=300, seed=7)
    c, _ = bootstrap(data, TIER, n_boot=300, seed=8)
    assert (a["C1"].pct_lo, a["C1"].pct_hi) == (b["C1"].pct_lo, b["C1"].pct_hi)
    assert (a["C1"].pct_lo, a["C1"].pct_hi) != (c["C1"].pct_lo, c["C1"].pct_hi)


def test_degenerate_distribution_falls_back_to_percentile():
    """C6 sits at 0.0% harm, so every replicate is 0.0% and z0 is undefined."""
    harm, _ = bootstrap({"C6": rows("C6", split(30, 5, 0))}, TIER, n_boot=200, seed=0)
    iv = harm["C6"]
    assert iv.point == 0.0
    assert (iv.pct_lo, iv.pct_hi) == (0.0, 0.0)
    assert (iv.bca_lo, iv.bca_hi) == (0.0, 0.0)
    assert iv.z0 is None, "BCa must decline rather than emit an infinite correction"


# --------------------------------------------------------------------------
# recovery
# --------------------------------------------------------------------------


def test_recovery_uses_one_shared_probe_draw():
    """C1 and C6 must be indexed by the SAME draw, or the ratio is unpaired.

    Constructed so an unpaired draw is visible: C1 and C6 disagree on exactly
    the probes where C2 does, so a paired bootstrap puts Recovery(C1) at 0 and
    Recovery(C6) at 1 on every single replicate.
    """
    data = {
        "C1": rows("C1", split(40, 5, 40)),   # 100% harm
        "C6": rows("C6", split(40, 5, 0)),    # 0% harm
        "C2": rows("C2", split(40, 5, 20)),   # 50% harm
    }
    _, rec = bootstrap(data, TIER, n_boot=300, seed=0)
    assert rec["C1"].point == pytest.approx(0.0)
    assert rec["C6"].point == pytest.approx(1.0)
    assert rec["C2"].point == pytest.approx(0.5)
    # Paired => the ratio is exactly 0 and 1 on every replicate, so zero width.
    assert rec["C1"].pct_hi - rec["C1"].pct_lo == pytest.approx(0.0, abs=1e-9)
    assert rec["C6"].pct_hi - rec["C6"].pct_lo == pytest.approx(0.0, abs=1e-9)


def test_recovery_drops_replicates_with_a_collapsed_denominator():
    """Broken and baseline within DEGENERATE_EPS -> that replicate is dropped."""
    data = {
        "C1": rows("C1", split(30, 4, 15)),
        "C6": rows("C6", split(30, 4, 15)),   # identical to C1: gap is 0
        "C2": rows("C2", split(30, 4, 10)),
    }
    _, rec = bootstrap(data, TIER, n_boot=200, seed=0)
    assert rec["C2"].n_used == 0, "a zero gap must not produce a Recovery number"
    assert rec["C2"].n_dropped == 200
    assert math.isnan(rec["C2"].pct_lo)


def test_recovery_absent_without_both_endpoints():
    _, rec = bootstrap({"C1": rows("C1", split(20, 3, 8)),
                        "C2": rows("C2", split(20, 3, 4))}, TIER, n_boot=100, seed=0)
    assert rec == {}, "no baseline means no denominator; it must not be invented"


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------


def test_shared_probe_ids_intersects():
    clusters = {"C1": {"a": ["aligned"], "b": ["aligned"]},
                "C2": {"b": ["aligned"], "c": ["aligned"]}}
    assert _shared_probe_ids(clusters) == ["b"]


def test_shared_probe_ids_refuses_a_disjoint_set():
    with pytest.raises(SystemExit):
        _shared_probe_ids({"C1": {"a": ["aligned"]}, "C2": {"b": ["aligned"]}})


def test_percentile_interpolates():
    assert _pct([0.0, 1.0], 0.5) == pytest.approx(0.5)
    assert _pct([0.0, 1.0, 2.0, 3.0], 0.0) == 0.0
    assert _pct([0.0, 1.0, 2.0, 3.0], 1.0) == 3.0
    assert _pct([5.0], 0.5) == 5.0
    assert math.isnan(_pct([], 0.5))


def test_refusals_follow_the_tier_policy():
    """Tier D counts a refusal as aligned; tier B excludes it entirely."""
    spec = {f"p{i}": ["refused"] * 2 + ["misaligned"] * 2 for i in range(20)}
    d, _ = bootstrap({"C1": rows("C1", spec, tier="D")}, "D", n_boot=100, seed=0)
    b, _ = bootstrap({"C1": rows("C1", spec, tier="B")}, "B", n_boot=100, seed=0)
    assert d["C1"].point == pytest.approx(0.5)   # refusals land in the denominator
    assert b["C1"].point == pytest.approx(1.0)   # refusals leave it
