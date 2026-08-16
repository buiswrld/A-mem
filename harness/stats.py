"""Clustered intervals for harm, refusal, low coherence, and Recovery.

    uv run python -m harness.stats results/*-msb_test_180-*.judged.jsonl

Every interval in the paper comes from here rather than from a notebook cell.
The 7B pilot's CIs were computed ad hoc, the code was never committed, and the
numbers in STATUS.md consequently cannot be reproduced from this repo -- which
is the same failure mode as a doc asserting a test exists.

## The resampling unit is the independent prompt family

Responses to one probe share a question, a retrieved context, and a sampling
seed. They are not independent draws. Measured on the committed 14B runs, the
intraclass correlation of the misaligned outcome is 0.42 (C1) and 0.31 (C2), so
resampling the individual rows would treat ~10 correlated responses as ~10
independent observations and shrink every interval by roughly sqrt(10).

For most probe sets, one probe id is one independent family. A probe set may
declare a ``*.clusters.json`` analysis map when multiple ids are variants of the
same underlying question. Tier C does this because its free-form, JSON-labelled,
and template ids are eight question families, and the JSON-labelled texts are
exact duplicates of the free-form texts. The CLI discovers an exact matching
map automatically. Keeping this as analysis metadata rather than editing frozen
result rows lets old model outputs be reanalysed without rewriting provenance.

So a replicate draws the independent cluster ids **with replacement** and takes
every row belonging to each drawn cluster. A cluster drawn twice contributes
its rows twice; that is what makes the interval respect the clustering.

## Three properties this module maintains

1. **The exclusion policy is re-applied per replicate.** `harm_rate()` drops
   refusals (per the tier's policy) and incoherent rows from its denominator.
   Rows are resampled *before* that filter and `harm_rate` re-applies it to each
   replicate, so the denominator varies the way it really does. Filtering first
   would freeze it and understate the spread.

2. **Recovery is computed inside the replicate.** `(broken - x) / (broken -
   baseline)` uses that replicate's own C1 and C6, from the same probe draw.
   Combining three independently-bootstrapped point estimates would get the
   ratio's uncertainty wrong in a direction that cannot be signed.

3. **One cluster draw is shared across all conditions.** Every condition ran
   the same probe set, so a replicate indexes them all with one list of ids.
   Drawing separately per condition would break the pairing that makes C3 - C2
   meaningful and would widen every interval for nothing. Harm, refusal, and
   the exploratory `derailed` rate all expose paired left-minus-right contrasts.

## Intervals

Percentile and BCa (bias-corrected and accelerated) are both reported. They
usually agree for a harm rate and usually do not for Recovery, which is a ratio
and therefore skewed: BCa corrects both the median bias (`z0`) and the
skew-induced change in spread (`a`, from a leave-one-probe-out jackknife). Both
are printed so a large gap is visible rather than hidden behind one number.

Degenerate replicates -- those whose Recovery denominator is within
`DEGENERATE_EPS` of zero, or whose harm rate is undefined because every row was
excluded -- are dropped and counted. A large drop count is not a nuisance to be
tuned away: it means the floor and the ceiling are not cleanly separated on that
resample, and it is reported loudly for that reason.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from statistics import NormalDist
from typing import Literal

from harness.judge import derailment_rate, harm_rate, refusal_rate
from harness.schema import read_jsonl

DEFAULT_N_BOOT = 2000
DEFAULT_ALPHA = 0.05
DEFAULT_CONTRASTS = (("C3", "C1"), ("C3", "C2"), ("C3", "C5"), ("C3", "C6"))

MetricName = Literal["harm", "refusal", "derailment"]

# |broken - baseline| below this and Recovery is not a meaningful quantity on
# that replicate: the denominator is the whole C1->C6 gap, and dividing by ~0
# turns a rounding difference into a Recovery of several hundred percent.
DEGENERATE_EPS = 0.01

_N = NormalDist()


@dataclass
class Interval:
    """One statistic with both interval flavours and the diagnostics behind them."""

    label: str
    point: float
    pct_lo: float
    pct_hi: float
    bca_lo: float
    bca_hi: float
    n_boot: int
    n_used: int
    z0: float | None = None
    accel: float | None = None

    @property
    def n_dropped(self) -> int:
        return self.n_boot - self.n_used

    def __str__(self) -> str:
        drop = f"  ({self.n_dropped} dropped)" if self.n_dropped else ""
        return (f"{self.label:12s} {self.point:7.1%}   "
                f"pct [{self.pct_lo:6.1%},{self.pct_hi:6.1%}]   "
                f"BCa [{self.bca_lo:6.1%},{self.bca_hi:6.1%}]{drop}")


# --------------------------------------------------------------------------
# clustering
# --------------------------------------------------------------------------


def cluster_verdicts(
    rows: Iterable[dict],
    cluster_map: dict[str, str] | None = None,
) -> dict[str, list[str]]:
    """cluster id -> its verdicts, using probe ids when no map is supplied."""
    out: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        probe_id = r["probe_id"]
        if cluster_map is not None and probe_id not in cluster_map:
            raise ValueError(f"probe {probe_id!r} is absent from the cluster map")
        cluster_id = cluster_map[probe_id] if cluster_map is not None else probe_id
        out[cluster_id].append(r["verdict"])
    return dict(out)


def cluster_tallies(
    rows: Iterable[dict],
    tier: str,
    cluster_map: dict[str, str] | None = None,
    metric: MetricName = "harm",
) -> dict[str, tuple[int, int]]:
    """Cluster id -> (events, denominator) for one rate endpoint.

    A rate is `sum(events) / sum(denominator)`, so a replicate only needs these
    two integers per cluster. Concatenating verdict strings and rerunning the
    metric on every replicate would be identical and much slower.

    Harm applies the tier-specific refusal policy and excludes derailed rows.
    Refusal and derailment use every generated row as their denominator. The
    policy is applied here per cluster; all three metrics classify each verdict
    independently, so per-cluster and pooled application agree exactly.
    """
    tallies: dict[str, tuple[int, int]] = {}
    for pid, verdicts in cluster_verdicts(rows, cluster_map).items():
        if metric == "harm":
            rate, n = harm_rate(verdicts, tier)
        elif metric == "refusal":
            rate, n = refusal_rate(verdicts), len(verdicts)
        elif metric == "derailment":
            rate, n = derailment_rate(verdicts), len(verdicts)
        else:  # pragma: no cover - protected by MetricName for typed callers
            raise ValueError(f"unknown metric {metric!r}")
        events = 0 if n == 0 else round(rate * n)
        tallies[pid] = (events, n)
    return tallies


def _shared_probe_ids(clusters: dict[str, dict[str, object]]) -> list[str]:
    """Probe ids present in every condition, sorted for determinism.

    Intersection rather than union: a probe missing from one condition cannot be
    part of a paired draw, and silently letting it in for the others would mean
    the conditions are no longer compared on the same probes.
    """
    sets = [set(c) for c in clusters.values()]
    shared = sorted(set.intersection(*sets)) if sets else []
    if not shared:
        raise SystemExit("no probe ids common to all conditions -- cannot pair a draw")
    for label, c in clusters.items():
        missing = len(set(c)) - len(shared)
        if missing:
            print(f"  note: {label} has {missing} probe(s) no other condition has; "
                  "excluded from the paired draw")
    return shared


# --------------------------------------------------------------------------
# the bootstrap
# --------------------------------------------------------------------------


def _rate(tally: dict[str, tuple[int, int]], probe_ids: Sequence[str]) -> float:
    mis = counted = 0
    for pid in probe_ids:
        m, n = tally[pid]
        mis += m
        counted += n
    return mis / counted if counted else float("nan")


def _replicates(
    tallies: dict[str, dict[str, tuple[int, int]]],
    probe_ids: Sequence[str],
    n_boot: int,
    seed: int,
) -> list[dict[str, float]]:
    """`n_boot` replicates, each a {label: harm_rate} from ONE shared draw."""
    rng = random.Random(seed)
    k = len(probe_ids)
    reps = []
    for _ in range(n_boot):
        draw = [probe_ids[rng.randrange(k)] for _ in range(k)]
        reps.append({label: _rate(t, draw) for label, t in tallies.items()})
    return reps


def _jackknife_reps(
    tallies: dict[str, dict[str, tuple[int, int]]],
    probe_ids: Sequence[str],
) -> list[dict[str, float]]:
    """Leave-one-probe-out rates for every label.

    Computed once and shared by every statistic. Deriving each label's
    jackknife separately would redo this len(labels) times over.
    """
    out = []
    for i in range(len(probe_ids)):
        kept = probe_ids[:i] + probe_ids[i + 1:]
        out.append({label: _rate(t, kept) for label, t in tallies.items()})
    return out


def _pct(sorted_vals: Sequence[float], p: float) -> float:
    """Linear-interpolated percentile. numpy's default, without the dependency."""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def _bca_bounds(
    theta_hat: float,
    reps: Sequence[float],
    jack: Sequence[float],
    alpha: float,
) -> tuple[float, float, float | None, float | None]:
    """BCa interval, falling back to percentile when the correction is undefined.

    Two situations make BCa inapplicable rather than merely imprecise, and both
    are real here:

      * every replicate equals the estimate (C6 sits at 0.0% harm, so every
        resample of it is also 0.0%) -- `z0` would be +/-inf;
      * the jackknife has no spread, so the acceleration denominator is 0.

    Falling back is correct in both: with a degenerate distribution the
    percentile interval is already the right answer (a point), and silently
    returning inf would poison the table.
    """
    n = len(reps)
    srt = sorted(reps)
    lo_p, hi_p = _pct(srt, alpha / 2), _pct(srt, 1 - alpha / 2)

    n_below = sum(1 for r in reps if r < theta_hat)
    prop = n_below / n
    if prop <= 0 or prop >= 1:
        return lo_p, hi_p, None, None
    z0 = _N.inv_cdf(prop)

    jbar = sum(jack) / len(jack)
    d = [jbar - j for j in jack]
    denom = 6.0 * (sum(x * x for x in d) ** 1.5)
    if denom == 0:
        return lo_p, hi_p, z0, None
    a = sum(x ** 3 for x in d) / denom

    out = []
    for q in (alpha / 2, 1 - alpha / 2):
        z = _N.inv_cdf(q)
        # 1 - a(z0+z) hits zero when the jackknife is extremely skewed; the BCa
        # endpoint diverges there and the percentile bound is the honest answer.
        denom_adj = 1 - a * (z0 + z)
        if abs(denom_adj) < 1e-12:
            return lo_p, hi_p, z0, a
        adj = z0 + (z0 + z) / denom_adj
        out.append(_pct(srt, min(max(_N.cdf(adj), 0.0), 1.0)))
    return out[0], out[1], z0, a


def _interval(
    label: str,
    theta_hat: float,
    reps: Sequence[float],
    jack: Sequence[float],
    n_boot: int,
    alpha: float,
) -> Interval:
    good = [r for r in reps if not math.isnan(r)]
    jgood = [j for j in jack if not math.isnan(j)]
    if not good:
        return Interval(label, theta_hat, float("nan"), float("nan"),
                        float("nan"), float("nan"), n_boot, 0)
    srt = sorted(good)
    lo_b, hi_b, z0, a = _bca_bounds(theta_hat, good, jgood or good, alpha)
    return Interval(label, theta_hat, _pct(srt, alpha / 2), _pct(srt, 1 - alpha / 2),
                    lo_b, hi_b, n_boot, len(good), z0, a)


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------


def bootstrap(
    rows_by_label: dict[str, list[dict]],
    tier: str,
    *,
    broken: str = "C1",
    baseline: str = "C6",
    n_boot: int = DEFAULT_N_BOOT,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
    cluster_map: dict[str, str] | None = None,
) -> tuple[dict[str, Interval], dict[str, Interval]]:
    """Clustered intervals for every condition's harm rate and Recovery.

    Returns `(harm, recovery)`, each `{label: Interval}`. Recovery is empty when
    `broken` or `baseline` is absent -- there is no denominator without both,
    and inventing one is how an uninterpretable number reaches a slide.

    ``cluster_map`` maps every probe id to its independent resampling family.
    With no map, each probe id remains its own cluster.
    """
    tallies = {label: cluster_tallies(rows, tier, cluster_map)
               for label, rows in rows_by_label.items()}
    probe_ids = _shared_probe_ids(tallies)
    reps = _replicates(tallies, probe_ids, n_boot, seed)
    jack_reps = _jackknife_reps(tallies, probe_ids)
    observed = {label: _rate(t, probe_ids) for label, t in tallies.items()}

    harm: dict[str, Interval] = {}
    for label in tallies:
        harm[label] = _interval(
            label, observed[label],
            [r[label] for r in reps], [j[label] for j in jack_reps], n_boot, alpha)

    recovery: dict[str, Interval] = {}
    if broken in tallies and baseline in tallies:
        def rec(rep: dict[str, float], L: str) -> float:
            denom = rep[broken] - rep[baseline]
            if math.isnan(denom) or math.isnan(rep[L]) or abs(denom) < DEGENERATE_EPS:
                return float("nan")
            return (rep[broken] - rep[L]) / denom

        for label in tallies:
            recovery[label] = _interval(
                label, rec(observed, label),
                [rec(r, label) for r in reps],
                [rec(j, label) for j in jack_reps], n_boot, alpha)
    return harm, recovery


def bootstrap_metric(
    rows_by_label: dict[str, list[dict]],
    tier: str,
    metric: MetricName,
    *,
    comparisons: Sequence[tuple[str, str]] = (),
    n_boot: int = DEFAULT_N_BOOT,
    alpha: float = DEFAULT_ALPHA,
    seed: int = 0,
    cluster_map: dict[str, str] | None = None,
) -> tuple[dict[str, Interval], dict[str, Interval]]:
    """Clustered rate intervals and paired left-minus-right differences.

    Every condition and every contrast uses the same cluster draw. A contrast
    therefore preserves probe/family pairing instead of subtracting two
    independently bootstrapped estimates. Refusal and derailment are always
    measured over all generated rows; harm retains its tier-specific policy.
    """
    tallies = {
        label: cluster_tallies(rows, tier, cluster_map, metric)
        for label, rows in rows_by_label.items()
    }
    cluster_ids = _shared_probe_ids(tallies)
    reps = _replicates(tallies, cluster_ids, n_boot, seed)
    jack_reps = _jackknife_reps(tallies, cluster_ids)
    observed = {label: _rate(t, cluster_ids) for label, t in tallies.items()}

    rates = {
        label: _interval(
            label,
            observed[label],
            [rep[label] for rep in reps],
            [rep[label] for rep in jack_reps],
            n_boot,
            alpha,
        )
        for label in tallies
    }

    def difference(rep: dict[str, float], left: str, right: str) -> float:
        if math.isnan(rep[left]) or math.isnan(rep[right]):
            return float("nan")
        return rep[left] - rep[right]

    contrasts = {}
    for left, right in comparisons:
        missing = {left, right} - set(tallies)
        if missing:
            raise ValueError(
                f"contrast {left}-{right} references absent condition(s): "
                f"{sorted(missing)}"
            )
        label = f"{left}-{right}"
        contrasts[label] = _interval(
            label,
            difference(observed, left, right),
            [difference(rep, left, right) for rep in reps],
            [difference(rep, left, right) for rep in jack_reps],
            n_boot,
            alpha,
        )
    return rates, contrasts


def report(
    harm: dict[str, Interval],
    recovery: dict[str, Interval],
    order: Sequence[str] = (),
    *,
    alpha: float = DEFAULT_ALPHA,
    cluster_unit: str = "probe",
) -> None:
    """Print both tables, with the BCa diagnostics that justify reading them."""
    keys = [k for k in order if k in harm] or sorted(harm)
    pct = round((1 - alpha) * 100)

    print(f"\nHarm rate — {cluster_unit}-clustered bootstrap, {pct}% intervals")
    print(f'{"cond":12s} {"point":>7s}   {"percentile":^17s}   {"BCa":^17s}'.rstrip())
    for k in keys:
        print(harm[k])

    if recovery:
        print("\nRecovery — (broken − x) / (broken − baseline), same replicates")
        print(f'{"cond":12s} {"point":>7s}   {"percentile":^17s}   {"BCa":^17s}'.rstrip())
        for k in keys:
            print(recovery[k])
        worst = max((recovery[k].n_dropped for k in keys), default=0)
        if worst:
            frac = worst / max(1, recovery[keys[0]].n_boot)
            print(f"\n  !! up to {worst} replicate(s) dropped ({frac:.1%}): the "
                  f"broken−baseline gap fell under {DEGENERATE_EPS:.0%} on those")
            if frac > 0.01:
                print("  !! over 1% — the floor and ceiling are not cleanly "
                      "separated. Recovery is not a safe headline number here.")

    print("\n  BCa diagnostics (z0 = median bias, a = acceleration/skew):")
    for k in keys:
        for name, tab in (("harm", harm), ("recov", recovery)):
            iv = tab.get(k)
            if iv is None:
                continue
            if iv.z0 is None:
                print(f"    {k:12s} {name:6s} degenerate — percentile reported for both")
            else:
                acc = "n/a" if iv.accel is None else f"{iv.accel:+.4f}"
                print(f"    {k:12s} {name:6s} z0 {iv.z0:+.4f}   a {acc}")


def report_metric_results(
    rates: dict[MetricName, dict[str, Interval]],
    contrasts: dict[MetricName, dict[str, Interval]],
    order: Sequence[str] = (),
    *,
    alpha: float = DEFAULT_ALPHA,
    cluster_unit: str = "probe",
) -> None:
    """Print refusal/derailment rates and paired contrasts for all metrics."""
    pct = round((1 - alpha) * 100)
    titles = {
        "harm": "Harm",
        "refusal": "Refusal",
        "derailment": "Low-coherence/off-topic (`derailed`)",
    }

    for metric in ("refusal", "derailment"):
        table = rates[metric]
        keys = [key for key in order if key in table] or sorted(table)
        print(
            f"\n{titles[metric]} rate — {cluster_unit}-clustered bootstrap, "
            f"{pct}% intervals"
        )
        print(f'{"cond":12s} {"point":>7s}   {"percentile":^17s}   {"BCa":^17s}'.rstrip())
        for key in keys:
            print(table[key])

    print(f"\nPaired rate differences — left minus right, {pct}% intervals")
    print("Negative harm means the left condition is less harmful; positive "
          "refusal/low-coherence means it fails more often on that endpoint.")
    for metric in ("harm", "refusal", "derailment"):
        print(f"\n  {titles[metric]}")
        print(
            f'  {"contrast":10s} {"point":>7s}   '
            f'{"percentile":^17s}   {"BCa":^17s}'.rstrip()
        )
        for interval in contrasts[metric].values():
            print(f"  {interval}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _label_for(path: pathlib.Path, row: dict) -> str:
    return row["condition"]


def _read_cluster_map(path: pathlib.Path) -> tuple[dict[str, str], str]:
    """Read and validate a probe-to-family analysis map."""
    try:
        spec = json.loads(path.read_text())
        mapping = spec["probe_to_cluster"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        raise SystemExit(f"cannot read cluster map {path}: {exc}") from exc
    if not isinstance(mapping, dict) or not mapping:
        raise SystemExit(f"cluster map {path} has no probe_to_cluster entries")
    if not all(
        isinstance(k, str) and isinstance(v, str) and v
        for k, v in mapping.items()
    ):
        raise SystemExit(
            f"cluster map {path} must map probe-id strings to cluster-id strings"
        )
    return mapping, str(spec.get("cluster_unit", "family"))


def _auto_cluster_map(
    probe_ids: set[str],
) -> tuple[dict[str, str] | None, str, pathlib.Path | None]:
    """Discover a family map only when its probe-id set matches exactly."""
    candidates = []
    probe_dir = pathlib.Path(__file__).parent / "probes"
    for path in sorted(probe_dir.glob("*.clusters.json")):
        mapping, unit = _read_cluster_map(path)
        if set(mapping) == probe_ids:
            candidates.append((mapping, unit, path))
    if len(candidates) > 1:
        names = ", ".join(str(p) for _, _, p in candidates)
        raise SystemExit(f"multiple cluster maps exactly match these probes: {names}")
    return candidates[0] if candidates else (None, "probe", None)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="judged result files (*.judged.jsonl)")
    ap.add_argument("--broken", default="C1")
    ap.add_argument("--baseline", default="C6")
    ap.add_argument("--n-boot", type=int, default=DEFAULT_N_BOOT)
    ap.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="emit the intervals as JSON instead of a table")
    ap.add_argument("--probe-set", metavar="SET_ID",
                    help="restrict to the probe ids in harness/probes/SET_ID.json. "
                         "Use to analyse a nested subset -- e.g. --probe-set betley8 "
                         "over tier C files, since trigger_nonclinical_24 contains "
                         "all 8 betley probes verbatim.")
    ap.add_argument("--cluster-map", type=pathlib.Path,
                    help="JSON probe-to-family map. If omitted, an exact matching "
                         "harness/probes/*.clusters.json map is used automatically.")
    args = ap.parse_args()

    keep: set[str] | None = None
    if args.probe_set:
        spec = pathlib.Path(__file__).parent / "probes" / f"{args.probe_set}.json"
        if not spec.exists():
            raise SystemExit(f"no probe set {args.probe_set!r} at {spec}")
        keep = {p["probe_id"] for p in json.loads(spec.read_text())["probes"]}

    rows_by_label, tiers, judges = {}, set(), set()
    for f in args.files:
        p = pathlib.Path(f)
        rows = read_jsonl(str(p))
        if not rows:
            raise SystemExit(f"{p} is empty")
        if "verdict" not in rows[0]:
            raise SystemExit(f"{p} is not judged -- run harness.judge on it first")
        if keep is not None:
            before = len(rows)
            rows = [r for r in rows if r["probe_id"] in keep]
            if not rows:
                raise SystemExit(
                    f"{p} has no rows from probe set {args.probe_set!r} -- the "
                    "sets do not overlap, so this is not a nested subset.")
            missing = keep - {r["probe_id"] for r in rows}
            if missing:
                raise SystemExit(
                    f"{p} is missing {len(missing)} of the {len(keep)} probes in "
                    f"{args.probe_set!r}: {sorted(missing)[:5]}. A partial subset "
                    "would compare conditions on different probes.")
            print(f"  {p.name}: {before} -> {len(rows)} rows on {len(keep)} probes")
        label = _label_for(p, rows[0])
        if label in rows_by_label:
            raise SystemExit(
                f"two files both claim condition {label!r}. Pass one file per "
                "condition, or the intervals silently describe a concatenation.")
        rows_by_label[label] = rows
        tiers.add(rows[0]["tier"])
        judges |= {r.get("judge_model") for r in rows}

    if len(tiers) != 1:
        raise SystemExit(f"mixed tiers {tiers} -- the refusal policy differs by tier")
    if len(judges) != 1:
        print(f"  !! rows scored by more than one judge: {judges}")

    tier = tiers.pop()
    probe_sets = [{r["probe_id"] for r in rows} for rows in rows_by_label.values()]
    shared_probe_ids = set.intersection(*probe_sets)
    if any(ids != shared_probe_ids for ids in probe_sets):
        raise SystemExit(
            "conditions contain different probe-id sets; "
            "cannot select a shared cluster map"
        )
    if args.cluster_map:
        cluster_map, cluster_unit = _read_cluster_map(args.cluster_map)
        extra = set(cluster_map) - shared_probe_ids
        missing = shared_probe_ids - set(cluster_map)
        if extra or missing:
            raise SystemExit(
                f"cluster map does not exactly cover the analysed probes "
                f"({len(missing)} missing, {len(extra)} extra)")
        cluster_map_path = args.cluster_map
    else:
        cluster_map, cluster_unit, cluster_map_path = _auto_cluster_map(shared_probe_ids)

    print(f"{len(rows_by_label)} conditions, tier {tier}, judge {judges.pop()}")
    print(f"{args.n_boot} replicates, seed {args.seed}")
    n_clusters = len(set(cluster_map.values())) if cluster_map else len(shared_probe_ids)
    if cluster_map_path:
        print(f"resampling {n_clusters} {cluster_unit} clusters via {cluster_map_path}")
    else:
        print(f"resampling {n_clusters} probe clusters")

    harm, recovery = bootstrap(rows_by_label, tier, broken=args.broken,
                               baseline=args.baseline, n_boot=args.n_boot,
                               alpha=args.alpha, seed=args.seed,
                               cluster_map=cluster_map)
    comparisons = tuple(
        pair for pair in DEFAULT_CONTRASTS
        if pair[0] in rows_by_label and pair[1] in rows_by_label
    )
    metric_rates: dict[MetricName, dict[str, Interval]] = {}
    metric_contrasts: dict[MetricName, dict[str, Interval]] = {}
    for metric in ("harm", "refusal", "derailment"):
        rates, contrasts = bootstrap_metric(
            rows_by_label,
            tier,
            metric,
            comparisons=comparisons,
            n_boot=args.n_boot,
            alpha=args.alpha,
            seed=args.seed,
            cluster_map=cluster_map,
        )
        metric_rates[metric] = rates
        metric_contrasts[metric] = contrasts

    if args.as_json:
        print(json.dumps(
            {"resampling": {
                 "cluster_unit": cluster_unit,
                 "n_clusters": n_clusters,
                 "cluster_map": str(cluster_map_path) if cluster_map_path else None,
             },
             "harm": {k: vars(v) for k, v in harm.items()},
             "recovery": {k: vars(v) for k, v in recovery.items()},
             "refusal": {k: vars(v) for k, v in metric_rates["refusal"].items()},
             "derailment": {
                 k: vars(v) for k, v in metric_rates["derailment"].items()
             },
             "contrasts": {
                 metric: {k: vars(v) for k, v in table.items()}
                 for metric, table in metric_contrasts.items()
             }}, indent=2))
    else:
        report(harm, recovery, order=("C1", "C2", "C3", "C4", "C5", "C6"),
               alpha=args.alpha, cluster_unit=cluster_unit)
        report_metric_results(
            metric_rates,
            metric_contrasts,
            order=("C1", "C2", "C3", "C4", "C5", "C6"),
            alpha=args.alpha,
            cluster_unit=cluster_unit,
        )


if __name__ == "__main__":
    main()
