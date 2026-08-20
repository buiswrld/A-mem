"""Re-derive verdicts from already-judged files. No API calls, no cost.

`harness.judge` does two separable things: it *buys* two numbers per response
(alignment, coherence) from the judge model, and it *interprets* those numbers
into a verdict via `classify()`. Only the first costs money, and only the second
changes when the verdict policy changes.

Re-running `harness.judge` to pick up a policy change therefore re-walks every
row through the cache -- and any row whose score is missing from the cache gets
re-bought at full price. On tier D that is 10,800 rows against a daily request
cap. This module does the interpretation half alone, reading `alignment`,
`coherence` and `flag` straight out of the `.judged.jsonl` the judge already
wrote.

Use it whenever `classify()` or `REFUSAL_POLICY` changes. Use `harness.judge`
only when there are new generations to score.

    find results -name '*.judged.jsonl' -print0 | xargs -0 uv run python -m harness.rescore
    find results -name '*.judged.jsonl' -print0 | xargs -0 uv run python -m harness.rescore --dry-run
"""

import argparse
import json
import pathlib

from harness.judge import (
    REFUSAL_POLICY,
    Verdict,
    classify,
    derailment_rate,
    harm_rate,
    refusal_rate,
)


def rescore_file(path: pathlib.Path, dry_run: bool = False) -> dict[str, int]:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not rows:
        raise SystemExit(f"{path} is empty")

    tier = rows[0]["tier"]
    missing = [r for r in rows if "alignment" not in r or "coherence" not in r]
    if missing:
        raise SystemExit(
            f"{path}: {len(missing)} rows have no judge scores -- this file was "
            "not produced by harness.judge, so there is nothing to re-derive. "
            "Run harness.judge on the raw .jsonl instead."
        )

    changed: dict[str, int] = {}
    verdicts: list[Verdict] = []
    for r in rows:
        old = r.get("verdict")
        new = classify(r["alignment"], r["coherence"], r["flag"], tier)
        verdicts.append(new)
        if old != new:
            changed[f"{old} -> {new}"] = changed.get(f"{old} -> {new}", 0) + 1
        r["verdict"] = new

    if not dry_run:
        # Same atomicity argument as judge._save_cache: these files are the only
        # record of scores that were paid for, and a truncated write loses them.
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(path)

    rate, n = harm_rate(verdicts, tier)
    print(f"{path.name}  (tier {tier}, {len(rows)} rows)")
    for k, v in sorted(changed.items()):
        print(f"    {v:5d}  {k}")
    if not changed:
        print("       no verdict changes")
    print(f"    harm {rate:.1%} over {n}   refusal {refusal_rate(verdicts):.1%}"
          f"   derailed {derailment_rate(verdicts):.1%}"
          f"   (refusals -> {REFUSAL_POLICY.get(tier, 'excluded')!r})")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", type=pathlib.Path)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without rewriting anything")
    args = ap.parse_args()

    for p in args.files:
        rescore_file(p, dry_run=args.dry_run)
    if args.dry_run:
        print("\ndry run -- nothing written")


if __name__ == "__main__":
    main()
