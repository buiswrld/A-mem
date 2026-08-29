"""Check manuscript structure and judge-audit claims against released data."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.schema import read_jsonl
from scripts.grader_robustness_check import RESULTS_PATH, agreement_stats


PAPER_DIR = ROOT / "paper"
RETIRED_DRAFT_DIR = ROOT / "docs" / "paper"


def check_paper_consistency() -> None:
    if RETIRED_DRAFT_DIR.exists():
        raise SystemExit(
            "retired docs/paper draft tree exists; edit only canonical paper/*.tex"
        )

    texts = {
        name: (PAPER_DIR / name).read_text(encoding="utf-8")
        for name in (
            "main.tex",
            "method.tex",
            "results.tex",
            "discussion.tex",
            "limitations.tex",
            "conclusion.tex",
            "supplement.tex",
        )
    }
    normalized = {name: " ".join(text.split()) for name, text in texts.items()}
    combined = " ".join(normalized.values()).lower()
    forbidden = (
        "all outcomes relied on a single automated judge",
        "second-judge evaluation with a state-of-the-art model was considered but",
        "a preregistered set of 180 benign clinical questions",
        "a preregistered benign-clinical evaluation",
    )
    for phrase in forbidden:
        if phrase in combined:
            raise SystemExit(f"stale judge-scope claim in canonical paper: {phrase!r}")

    required = {
        "main.tex": "All primary outcomes came from one automated judge",
        "method.tex": "All primary outcomes use this pinned judge",
        "limitations.tex": "All primary outcomes relied on one automated judge",
    }
    for name, phrase in required.items():
        if phrase not in normalized[name]:
            raise SystemExit(f"missing canonical judge-scope language in {name}: {phrase}")

    matches, observed, kappa = agreement_stats(read_jsonl(str(RESULTS_PATH)))
    latex_percent = f"{observed * 100:.1f}\\%"
    agreement_phrase = f"{matches} of 60 responses ({latex_percent})"
    if agreement_phrase not in texts["results.tex"]:
        raise SystemExit("Results audit agreement does not match released rows")
    if f"$\\kappa$ was {kappa:.2f}" not in texts["results.tex"]:
        raise SystemExit("Results kappa does not match released rows")
    if latex_percent not in texts["main.tex"]:
        raise SystemExit("Abstract audit agreement does not match released rows")
    if f"$\\kappa={kappa:.2f}$" not in texts["limitations.tex"]:
        raise SystemExit("Limitations kappa does not match released rows")


def main() -> None:
    check_paper_consistency()
    print("canonical paper structure and judge-audit claims are consistent")


if __name__ == "__main__":
    main()
