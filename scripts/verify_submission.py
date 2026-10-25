"""Run the complete local pre-submission verification gate."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper"


def run(label: str, command: list[str], cwd: Path = ROOT) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        print(completed.stdout, file=sys.stderr)
        raise SystemExit(f"[failed] {label}")
    print(f"[ok] {label}")


def compile_paper() -> None:
    pdflatex = shutil.which("pdflatex")
    bibtex = shutil.which("bibtex")
    if not pdflatex or not bibtex:
        raise SystemExit("[failed] paper build: pdflatex and bibtex are required")
    latex = [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    run("paper LaTeX pass 1", latex, PAPER_DIR)
    run("paper bibliography", [bibtex, "main"], PAPER_DIR)
    run("paper LaTeX pass 2", latex, PAPER_DIR)
    run("paper LaTeX pass 3", latex, PAPER_DIR)
    log = (PAPER_DIR / "main.log").read_text(encoding="utf-8", errors="replace")
    fatal_warnings = (
        "There were undefined references",
        "There were undefined citations",
        "multiply defined",
    )
    found = [warning for warning in fatal_warnings if warning in log]
    if found:
        raise SystemExit("[failed] unresolved paper warnings: " + ", ".join(found))
    print("[ok] resolved paper references and citations")


def main() -> None:
    python = sys.executable
    run("result manifest", [python, "scripts/verify_results.py"])
    run("canonical analyses", [python, "-m", "scripts.final_analysis"])
    run("second-judge analysis", [python, "-m", "scripts.grader_robustness_check", "analyze"])
    run("paper consistency", [python, "scripts/check_paper_consistency.py"])
    run("test suite", [python, "-m", "pytest", "harness/tests", "-q"])
    run("Overleaf bundle", [python, "scripts/sync_paper.py", "--check"])
    compile_paper()
    print("submission verification passed")


if __name__ == "__main__":
    main()
