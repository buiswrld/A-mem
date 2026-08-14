"""Probe-clustered bootstrap intervals for harm rates and Recovery.

    uv run python -m harness.stats results/*-msb_test_180-*.judged.jsonl

Every interval in the paper comes from here rather than from a notebook cell.
The 7B pilot's CIs were computed ad hoc, the code was never committed, and the
numbers in STATUS.md consequently cannot be reproduced from this repo -- which
is the same failure mode as a doc asserting a test exists.

## The resampling unit is the probe

Responses to one probe share a question, a retrieved context, and a sampling
seed. They are not independent draws. Measured on the committed 14B runs, the
intraclass correlation of the misaligned outcome is 0.42 (C1) and 0.31 (C2), so
resampling the individual rows would treat ~10 correlated responses as ~10
independent observations and shrink every interval by roughly sqrt(10).

So a replicate draws `n_probes` probe ids **with replacement** and takes every
row belonging to each drawn probe. A probe drawn twice contributes its rows
twice; that is what makes the interval respect the clustering.

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

3. **One probe draw is shared across all conditions.** Every condition ran the
   same probe set, so a replicate indexes them all with one list of ids. Drawing
   separately per condition would break the pairing that makes C3 - C2
   meaningful and would widen every interval for nothing.

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
from dataclasses import dataclass
from statistics import NormalDist
from typing import Iterable, Sequence

from harness.judge import harm_rate
from harness.schema import read_jsonl

DEFAULT_N_BOOT = 2000
DEFAULT_ALPHA = 0.05

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


def cluster_verdicts(rows: Iterable[dict]) -> dict[str, list[str]]:
    """probe_id -> that probe's verdicts. The resampling unit, materialised."""
    out: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        out[r["probe_id"]].append(r["verdict"])
    return dict(out)


def cluster_tallies(rows: Iterable[dict], tier: str) -> dict[str, tuple[int, int]]:
    """probe_id -> (n_misaligned, n_counted), with the tier policy applied.

    A harm rate is `sum(misaligned) / sum(counted)`, so a replicate only needs
    these two integers per probe -- concatenating the verdict strings and
    re-running `harm_rate` on 2,000 x 7 x 1,800 of them gives an identical
    answer about fifty times slower.

    The policy is applied **here, per probe**, not to the pooled replicate, and
    that is not an optimisation shortcut: `harm_rate` classifies each verdict
    independently, so per-probe and pooled application agree exactly. What
    varies across replicates is the denominator, which is preserved because
    `n_counted` is carried per probe and summed over the draw.
    """
    tallies: dict[str, tuple[int, int]] = {}
    for pid, verdicts in cluster_verdicts(rows).items():
        rate, n = harm_rate(verdicts, tier)
        mis = 0 if n == 0 else int(round(rate * n))
        tallies[pid] = (mis, n)
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
) -> tuple[dict[str, Interval], dict[str, Interval]]:
    """Probe-clustered intervals for every condition's harm rate and Recovery.

    Returns `(harm, recovery)`, each `{label: Interval}`. Recovery is empty when
    `broken` or `baseline` is absent -- there is no denominator without both,
    and inventing one is how an uninterpretable number reaches a slide.
    """
    tallies = {label: cluster_tallies(rows, tier)
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


def report(harm: dict[str, Interval], recovery: dict[str, Interval],
           order: Sequence[str] = ()) -> None:
    """Print both tables, with the BCa diagnostics that justify reading them."""
    keys = [k for k in order if k in harm] or sorted(harm)
    pct = int(round((1 - DEFAULT_ALPHA) * 100))

    print(f"\nHarm rate — probe-clustered bootstrap, {pct}% intervals")
    print(f'{"cond":12s} {"point":>7s}   {"percentile":^17s}   {"BCa":^17s}')
    for k in keys:
        print(harm[k])

    if recovery:
        print(f"\nRecovery — (broken − x) / (broken − baseline), same replicates")
        print(f'{"cond":12s} {"point":>7s}   {"percentile":^17s}   {"BCa":^17s}')
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


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _label_for(path: pathlib.Path, row: dict) -> str:
    return row["condition"]


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
    print(f"{len(rows_by_label)} conditions, tier {tier}, judge {judges.pop()}")
    print(f"{args.n_boot} replicates, seed {args.seed}")

    harm, recovery = bootstrap(rows_by_label, tier, broken=args.broken,
                               baseline=args.baseline, n_boot=args.n_boot,
                               alpha=args.alpha, seed=args.seed)
    if args.as_json:
        print(json.dumps(
            {"harm": {k: vars(v) for k, v in harm.items()},
             "recovery": {k: vars(v) for k, v in recovery.items()}}, indent=2))
    else:
        report(harm, recovery, order=("C1", "C2", "C3", "C4", "C5", "C6"))


if __name__ == "__main__":
    main()
