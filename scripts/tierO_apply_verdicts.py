"""Fold verdicts from the review page back into docs/tierO_probe_review.md.

Usage:
    # paste the exported JSON into a file, then:
    uv run python scripts/tierO_apply_verdicts.py verdicts.json

    # or straight from the clipboard buffer:
    uv run python scripts/tierO_apply_verdicts.py -   # reads stdin

Writes the verdict onto each `- **verdict:**` line, and emits the kept-probe id
list that tier O generation should filter on. Idempotent: re-running with an
updated verdict file overwrites cleanly, so you can review in passes.
"""

import json
import pathlib
import re
import sys

DOC = pathlib.Path("docs/tierO_probe_review.md")
KEEP = pathlib.Path("corpora/tierO_keep_ids.json")
VALID = {"OK", "BACKWARDS", "?"}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)

    raw = sys.stdin.read() if sys.argv[1] == "-" else pathlib.Path(sys.argv[1]).read_text()
    verdicts = json.loads(raw)

    bad = {k: v for k, v in verdicts.items() if v not in VALID}
    if bad:
        raise SystemExit(f"unrecognised verdicts (expected {VALID}): {bad}")

    text = DOC.read_text()
    applied = 0

    def sub(m: re.Match) -> str:
        nonlocal applied
        pid, body = m.group("pid"), m.group("body")
        v = verdicts.get(pid)
        if v is None:
            return m.group(0)
        applied += 1
        return re.sub(r"(- \*\*verdict:\*\*).*", rf"\1 {v}", body)

    # Each section runs from its `## n. orsc-id` heading to the next heading.
    pattern = re.compile(
        r"(?P<body>^## \d+\. (?P<pid>orsc-\d+) .*?(?=^## |\Z))",
        re.M | re.S,
    )
    text = pattern.sub(sub, text)
    DOC.write_text(text)

    counts = {v: sum(1 for x in verdicts.values() if x == v) for v in VALID}
    total = len(re.findall(r"^## \d+\. orsc-\d+", DOC.read_text(), re.M))

    keep = sorted(pid for pid, v in verdicts.items() if v == "OK")
    KEEP.write_text(json.dumps(keep, indent=1))

    print(f"applied {applied} verdicts to {DOC} ({total} sections total)")
    print(f"  OK {counts['OK']}  BACKWARDS {counts['BACKWARDS']}  ? {counts['?']}")
    missing = total - len(verdicts)
    if missing:
        print(f"  {missing} sections still unmarked")
    unsure = [p for p, v in verdicts.items() if v == "?"]
    if unsure:
        print(f"  unresolved '?': {', '.join(sorted(unsure))}")
        print("  these are NOT in the keep list -- resolve them or they are dropped")
    print(f"\nwrote {KEEP} -- {len(keep)} probes cleared for tier O generation")
    if keep:
        print(f"  tier O size: {len(keep)} probes x 10 samples x 6 conditions "
              f"= {len(keep) * 10 * 6:,} rows")


if __name__ == "__main__":
    main()
