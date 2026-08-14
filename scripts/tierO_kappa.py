"""Inter-rater agreement on the tier O probe review.

    uv run python scripts/tierO_kappa.py primary.json rater2.json

Both arguments are the JSON blocks exported by the review pages. Compares them
on the 40 probes both rated and reports Cohen's kappa plus the full
disagreement list, because the disagreements are what the two raters have to
talk through (`docs/prereg_tierO.md` §5.3).

Kappa is reported whatever it comes out as. A low value is a finding about how
ambiguous these rewrites are -- it is not a signal to re-rate until the number
improves, and doing so would void the independence the second rating exists to
establish.
"""

import itertools
import json
import pathlib
import sys

LABELS = ["OK", "BACKWARDS", "?"]


def cohens_kappa(a: list[str], b: list[str]) -> tuple[float, float, float]:
    """Returns (kappa, observed agreement, expected agreement)."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(L) / n) * (b.count(L) / n) for L in LABELS)
    # pe == 1 iff both raters used one identical label throughout; kappa is
    # undefined there rather than perfect, so say so instead of dividing by 0.
    kappa = float("nan") if pe == 1 else (po - pe) / (1 - pe)
    return kappa, po, pe


def interpret(k: float) -> str:
    if k != k:
        return "undefined -- one label used throughout"
    for bound, word in ((0.0, "worse than chance"), (0.20, "slight"),
                        (0.40, "fair"), (0.60, "moderate"),
                        (0.80, "substantial"), (1.01, "almost perfect")):
        if k < bound:
            return word
    return "almost perfect"


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)

    primary = json.loads(pathlib.Path(sys.argv[1]).read_text())
    second = json.loads(pathlib.Path(sys.argv[2]).read_text())

    shared = sorted(set(primary) & set(second))
    if not shared:
        raise SystemExit("no probe ids in common -- are these the right two files?")

    manifest = pathlib.Path("scripts/tierO_rater2_sample.json")
    if manifest.exists():
        expected = set(json.loads(manifest.read_text())["ids"])
        missing = expected - set(second)
        if missing:
            print(f"warning: second rater has not marked {len(missing)} of their "
                  f"{len(expected)} assigned probes: {', '.join(sorted(missing))}\n")

    a = [primary[p] for p in shared]
    b = [second[p] for p in shared]
    kappa, po, pe = cohens_kappa(a, b)

    print(f"Cohen's kappa on {len(shared)} double-rated probes\n")
    print(f"  kappa               {kappa:.3f}   ({interpret(kappa)})")
    print(f"  observed agreement  {po:.1%}")
    print(f"  expected by chance  {pe:.1%}\n")

    print("  confusion (rows = primary, cols = second)")
    print("             " + "".join(f"{L:>12}" for L in LABELS))
    for r in LABELS:
        cells = "".join(
            f"{sum(1 for x, y in zip(a, b) if x == r and y == c):>12}"
            for c in LABELS
        )
        print(f"  {r:>10} {cells}")

    disagree = [(p, x, y) for p, x, y in zip(shared, a, b) if x != y]
    print(f"\n  {len(disagree)} disagreements to resolve by discussion:")
    for p, x, y in disagree:
        print(f"    {p:>12}   primary {x:>10}   second {y:>10}")
    if not disagree:
        print("    none")

    # The pairs that matter most: one rater says ship it, the other says it is
    # still harmful. These decide whether a probe enters the primary set.
    hard = [d for d in disagree if {d[1], d[2]} == {"OK", "BACKWARDS"}]
    if hard:
        print(f"\n  {len(hard)} of those are outright OK/BACKWARDS conflicts -- "
              "resolve these first")


if __name__ == "__main__":
    main()
