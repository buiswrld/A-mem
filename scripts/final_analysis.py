"""Reproduce or verify every canonical analysis from the frozen manifest.

After the experiment freeze, the normal command is a non-mutating check:

    uv run python -m scripts.final_analysis

Use ``--write`` only when creating the reviewed analysis snapshot. It runs
``harness.stats`` once per canonical group and writes deterministic text output
under ``analysis/frozen/``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Any

from scripts.freeze_results import ROOT, sha256_file, verify_manifest

OUTPUT_DIR = ROOT / "analysis/frozen"


def stats_command(manifest: dict[str, Any], group_name: str) -> list[str]:
    group = manifest["analysis_groups"][group_name]
    runs = {run["run_id"]: run for run in manifest["runs"]}
    command = [sys.executable, "-m", "harness.stats"]
    if group.get("probe_set"):
        command.extend(("--probe-set", group["probe_set"]))
    command.extend(runs[run_id]["judged"]["path"] for run_id in group["run_ids"])
    return command


def display_command(command: list[str]) -> str:
    normalized = ["uv", "run", "python", *command[1:]]
    return " ".join(normalized)


def render_group(
    manifest: dict[str, Any], group_name: str, *, manifest_sha256: str
) -> str:
    group = manifest["analysis_groups"][group_name]
    command = stats_command(manifest, group_name)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise SystemExit(
            f"analysis group {group_name} failed ({completed.returncode})\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return (
        f"# Frozen analysis: {group_name}\n"
        f"# {group['description']}\n"
        f"# results/frozen_manifest.json sha256: {manifest_sha256}\n"
        f"# command: {display_command(command)}\n\n"
        f"{completed.stdout}"
    )


def selected_groups(manifest: dict[str, Any], names: list[str]) -> list[str]:
    available = list(manifest["analysis_groups"])
    unknown = set(names) - set(available)
    if unknown:
        raise SystemExit(
            f"unknown analysis group(s) {sorted(unknown)}; choose from {available}"
        )
    return names or available


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group", action="append", default=[],
        help="check/write one group (repeatable); default is every group",
    )
    parser.add_argument(
        "--write", action="store_true",
        help="write reviewed outputs instead of comparing with the frozen outputs",
    )
    args = parser.parse_args()

    manifest = verify_manifest()
    manifest_sha256 = sha256_file(ROOT / "results/frozen_manifest.json")
    groups = selected_groups(manifest, args.group)
    if args.write:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = []
    for group_name in groups:
        rendered = render_group(
            manifest, group_name, manifest_sha256=manifest_sha256
        )
        path = OUTPUT_DIR / f"{group_name}.txt"
        if args.write:
            path.write_text(rendered, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
        elif not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != rendered:
            failures.append(f"output drift in {path.relative_to(ROOT)}")
        else:
            print(f"verified {path.relative_to(ROOT)}")

    if failures:
        raise SystemExit(
            "FROZEN ANALYSIS VERIFICATION FAILED. Review the code/data change; "
            "do not overwrite outputs reflexively.\n  " + "\n  ".join(failures)
        )


if __name__ == "__main__":
    main()
