"""Create or verify the canonical experiment-results manifest.

The manifest distinguishes primary episodic runs, matched no-session
sensitivities, calibration runs, and the C4 persisted-store diagnostic. It also
records every publication result artifact by SHA-256 and validates that each judged
row is the corresponding raw row plus judge fields.

Normal use is verification only:

    uv run python scripts/verify_results.py

``--write`` is for creating a deliberately reviewed manifest. Do not use it
to make an unexpected verification failure disappear.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
MANIFEST_PATH = RESULTS_DIR / "manifest.json"
MANIFEST_VERSION = "1.0.0"
JUDGE_FIELDS = {"alignment", "coherence", "flag", "verdict", "judge_model"}
# Publication documentation is allowed beside result artifacts but is not itself
# part of the manifest.
NON_RESULT_FILES = {"results/README.md", "results/manifest.json"}


def _run(
    run_id: str,
    tier: str,
    condition: str,
    stem: str,
    role: str,
    protocol: str,
    *,
    extra_artifacts: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "tier": tier,
        "condition": condition,
        "stem": stem,
        "role": role,
        "protocol": protocol,
        "extra_artifacts": list(extra_artifacts),
    }


# Every publication result run has one declared role. Superseded pilots are not
# part of the publication tree.
RUN_SPECS = (
    _run("tier_b_c1", "B", "C1", "C1-betley8-0af77c4080f8-s0",
         "calibration", "standalone"),
    _run("tier_b_c6", "B", "C6", "C6-betley8-3bfb623268e8-s0",
         "calibration", "standalone"),

    _run("tier_c_c1", "C", "C1", "C1-trigger_nonclinical_24-12a45b982b33-s0",
         "primary", "episodic"),
    _run("tier_c_c2", "C", "C2", "C2-trigger_nonclinical_24-9457fdb818e1-s0",
         "primary", "episodic"),
    _run("tier_c_c3", "C", "C3", "C3-trigger_nonclinical_24-709de3c1bf86-s0",
         "primary", "episodic"),
    _run("tier_c_c4", "C", "C4", "C4-trigger_nonclinical_24-cac74f31b15a-s0",
         "primary", "episodic"),
    _run("tier_c_c5", "C", "C5", "C5-trigger_nonclinical_24-d75440b11af5-s0",
         "primary", "episodic"),
    _run("tier_c_c6", "C", "C6", "C6-trigger_nonclinical_24-b64f88f4ec51-s0",
         "primary", "episodic"),
    _run("tier_c_c3_no_session", "C", "C3",
         "C3-trigger_nonclinical_24-ab2b7ba6b20f-s0",
         "sensitivity", "no_session"),
    _run("tier_c_c5_no_session", "C", "C5",
         "C5-trigger_nonclinical_24-761d8625e2cd-s0",
         "sensitivity", "no_session"),
    _run("tier_c_c4_persisted", "C", "C4",
         "C4-trigger_nonclinical_24-907eb9cdcffc-s0",
         "diagnostic_only", "episodic_persisted_store",
         extra_artifacts=("results/diagnostic/C4-store-trigger_nonclinical_24-907eb9cdcffc-s0.json",)),

    _run("tier_d_c1", "D", "C1", "C1-msb_test_180-aa46f865e032-s0",
         "primary", "episodic"),
    _run("tier_d_c2", "D", "C2", "C2-msb_test_180-7b297bb7234b-s0",
         "primary", "episodic"),
    _run("tier_d_c3", "D", "C3", "C3-msb_test_180-9b47d343f4cf-s0",
         "primary", "episodic"),
    _run("tier_d_c4", "D", "C4", "C4-msb_test_180-ad094b9e67bd-s0",
         "primary", "episodic"),
    _run("tier_d_c5", "D", "C5", "C5-msb_test_180-c3703a43c516-s0",
         "primary", "episodic"),
    _run("tier_d_c6", "D", "C6", "C6-msb_test_180-3ad0343111ce-s0",
         "primary", "episodic"),
    _run("tier_d_c3_no_session", "D", "C3",
         "C3-msb_test_180-da814b86c06f-s0",
         "sensitivity", "no_session"),
    _run("tier_d_c5_no_session", "D", "C5",
         "C5-msb_test_180-359553f27ba7-s0",
         "sensitivity", "no_session"),

    _run("tier_o_c1", "O", "C1", "C1-medmcqa_actionable_180-46203dfd67e6-s0",
         "primary_preregistered", "episodic"),
    _run("tier_o_c2", "O", "C2", "C2-medmcqa_actionable_180-47e797e4f9ff-s0",
         "primary_preregistered", "episodic"),
    _run("tier_o_c3", "O", "C3", "C3-medmcqa_actionable_180-9fa8b7d4aa42-s0",
         "primary_preregistered", "episodic"),
    _run("tier_o_c4", "O", "C4", "C4-medmcqa_actionable_180-e6c1757ff451-s0",
         "primary_preregistered", "episodic"),
    _run("tier_o_c5", "O", "C5", "C5-medmcqa_actionable_180-c0363d8d792a-s0",
         "primary_preregistered", "episodic"),
    _run("tier_o_c6", "O", "C6", "C6-medmcqa_actionable_180-1cc2789c911e-s0",
         "primary_preregistered", "episodic"),
)

ANALYSIS_GROUPS = {
    "tier_b_episodic_subset": {
        "description": (
            "Exploratory Betley-8 subset of the Tier C episodic runs; this is "
            "not the two-condition standalone calibration."
        ),
        "run_ids": [f"tier_c_c{i}" for i in range(1, 7)],
        "probe_set": "betley8",
    },
    "tier_c_episodic": {
        "description": "Primary exploratory nonclinical-generalization analysis.",
        "run_ids": [f"tier_c_c{i}" for i in range(1, 7)],
    },
    "tier_d_episodic": {
        "description": "Primary exploratory clinical-harm analysis.",
        "run_ids": [f"tier_d_c{i}" for i in range(1, 7)],
    },
    "tier_o_episodic": {
        "description": "Preregistered benign-clinical over-refusal analysis.",
        "run_ids": [f"tier_o_c{i}" for i in range(1, 7)],
    },
    "tier_c_no_session": {
        "description": "Matched C3-vs-C5 no-session content sensitivity on Tier C.",
        "run_ids": [
            "tier_c_c1", "tier_c_c2", "tier_c_c3_no_session",
            "tier_c_c5_no_session", "tier_c_c6",
        ],
    },
    "tier_d_no_session": {
        "description": "Matched C3-vs-C5 no-session content sensitivity on Tier D.",
        "run_ids": [
            "tier_d_c1", "tier_d_c2", "tier_d_c3_no_session",
            "tier_d_c5_no_session", "tier_d_c6",
        ],
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise TypeError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    if not rows:
        raise ValueError(f"{path}: empty result file")
    return rows


def _uniform(rows: list[dict[str, Any]], field: str) -> list[Any]:
    return sorted({row.get(field) for row in rows}, key=lambda value: str(value))


def result_directory(spec: dict[str, Any]) -> str:
    """Return the publication-facing directory for one declared run."""
    if spec["role"] in {"primary", "primary_preregistered"}:
        return f"results/primary/tier_{spec['tier'].lower()}"
    if spec["role"] == "sensitivity":
        return f"results/sensitivity/tier_{spec['tier'].lower()}"
    if spec["role"] == "diagnostic_only":
        return "results/diagnostic"
    if spec["role"] == "calibration":
        return "results/calibration"
    raise ValueError(f"{spec['run_id']}: unknown result role {spec['role']!r}")


def summarize_run(spec: dict[str, Any]) -> dict[str, Any]:
    directory = result_directory(spec)
    raw_relative = f"{directory}/{spec['stem']}.jsonl"
    judged_relative = f"{directory}/{spec['stem']}.judged.jsonl"
    raw_path, judged_path = ROOT / raw_relative, ROOT / judged_relative
    if not raw_path.exists() or not judged_path.exists():
        raise ValueError(f"{spec['run_id']}: raw/judged pair is missing")

    raw_rows = read_jsonl(raw_path)
    judged_rows = read_jsonl(judged_path)
    if len(raw_rows) != len(judged_rows):
        raise ValueError(
            f"{spec['run_id']}: raw has {len(raw_rows)} rows, judged has "
            f"{len(judged_rows)}"
        )
    for index, (raw, judged) in enumerate(zip(raw_rows, judged_rows, strict=True)):
        source_part = {key: value for key, value in judged.items() if key not in JUDGE_FIELDS}
        if source_part != raw:
            raise ValueError(
                f"{spec['run_id']}: judged row {index} is not its raw row plus "
                "the five judge fields"
            )

    for field, expected in (("tier", spec["tier"]), ("condition", spec["condition"])):
        values = _uniform(raw_rows, field)
        if values != [expected]:
            raise ValueError(
                f"{spec['run_id']}: expected {field}={expected!r}, found {values!r}"
            )
    judge_models = _uniform(judged_rows, "judge_model")
    if judge_models != ["gpt-4o-2024-08-06"]:
        raise ValueError(f"{spec['run_id']}: unexpected judge models {judge_models}")

    probe_counts: dict[str, int] = {}
    for row in raw_rows:
        probe_counts[row["probe_id"]] = probe_counts.get(row["probe_id"], 0) + 1
    samples_per_probe = sorted(set(probe_counts.values()))
    if len(samples_per_probe) != 1:
        raise ValueError(
            f"{spec['run_id']}: unequal samples per probe {samples_per_probe}"
        )

    artifacts = []
    for relative in spec["extra_artifacts"]:
        path = ROOT / relative
        if not path.exists():
            raise ValueError(f"{spec['run_id']}: missing extra artifact {relative}")
        artifacts.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })

    return {
        "run_id": spec["run_id"],
        "role": spec["role"],
        "protocol": spec["protocol"],
        "tier": spec["tier"],
        "condition": spec["condition"],
        "rows": len(raw_rows),
        "probes": len(probe_counts),
        "samples_per_probe": samples_per_probe[0],
        "raw": {
            "path": raw_relative,
            "bytes": raw_path.stat().st_size,
            "sha256": sha256_file(raw_path),
        },
        "judged": {
            "path": judged_relative,
            "bytes": judged_path.stat().st_size,
            "sha256": sha256_file(judged_path),
        },
        "extra_artifacts": artifacts,
        "config_hash": _uniform(raw_rows, "config_hash"),
        "generation_git_sha": _uniform(raw_rows, "git_sha"),
        "schema_version": _uniform(raw_rows, "schema_version"),
        "judge_model": judge_models,
        "seed": _uniform(raw_rows, "seed"),
        "temperature": _uniform(raw_rows, "temperature"),
        "load_4bit": _uniform(raw_rows, "load_4bit"),
        "base_model": _uniform(raw_rows, "base_model"),
        "adapter": _uniform(raw_rows, "adapter"),
        "memory_kind": _uniform(raw_rows, "memory_kind"),
        "corpus": _uniform(raw_rows, "corpus"),
    }


def build_manifest() -> dict[str, Any]:
    run_ids = [spec["run_id"] for spec in RUN_SPECS]
    if len(set(run_ids)) != len(run_ids):
        raise ValueError("RUN_SPECS contains duplicate run ids")
    missing_group_ids = {
        run_id
        for group in ANALYSIS_GROUPS.values()
        for run_id in group["run_ids"]
        if run_id not in run_ids
    }
    if missing_group_ids:
        raise ValueError(f"analysis groups reference unknown runs: {missing_group_ids}")

    runs = [summarize_run(spec) for spec in RUN_SPECS]
    expected_paths = {
        artifact["path"]
        for run in runs
        for artifact in (run["raw"], run["judged"], *run["extra_artifacts"])
    }
    actual_paths = {
        str(path.relative_to(ROOT))
        for path in RESULTS_DIR.rglob("*")
        if path.is_file() and str(path.relative_to(ROOT)) not in NON_RESULT_FILES
    }
    if actual_paths != expected_paths:
        raise ValueError(
            "publication results differ from RUN_SPECS; "
            f"unregistered={sorted(actual_paths - expected_paths)}, "
            f"missing={sorted(expected_paths - actual_paths)}"
        )

    return {
        "manifest_version": MANIFEST_VERSION,
        "judge_model": "gpt-4o-2024-08-06",
        "bootstrap": {"replicates": 2000, "seed": 0, "interval": "BCa 95%"},
        "scope": {
            "top_level_results": (
                "Every publication result artifact is organized by role and listed "
                "with its identity and hash. Superseded pilots are excluded."
            ),
        },
        "analysis_groups": ANALYSIS_GROUPS,
        "runs": runs,
    }


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def write_manifest() -> dict[str, Any]:
    manifest = build_manifest()
    MANIFEST_PATH.write_text(canonical_json(manifest), encoding="utf-8")
    return manifest


def verify_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"missing {MANIFEST_PATH}; create it with --write")
    try:
        recorded = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid results manifest: {exc}") from exc
    current = build_manifest()
    if recorded != current:
        diff = "".join(difflib.unified_diff(
            canonical_json(recorded).splitlines(keepends=True),
            canonical_json(current).splitlines(keepends=True),
            fromfile="manifest.json",
            tofile="current results",
            n=2,
        ))
        raise SystemExit(
            "RESULTS VERIFICATION FAILED. Do not rewrite the manifest "
            "without reviewing the data change.\n" + diff[:12000]
        )
    return recorded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true",
        help="create/replace the manifest after deliberate review",
    )
    parser.add_argument(
        "--list-groups", action="store_true",
        help="print the canonical analysis groups after verification",
    )
    args = parser.parse_args()

    manifest = write_manifest() if args.write else verify_manifest()
    action = "wrote" if args.write else "verified"
    total_rows = sum(run["rows"] for run in manifest["runs"])
    print(
        f"{action} {len(manifest['runs'])} runs, {total_rows:,} raw rows, "
        f"{2 * total_rows:,} raw+judged rows"
    )
    print(f"manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    print(f"sha256:   {sha256_file(MANIFEST_PATH)}")
    if args.list_groups:
        for name, group in manifest["analysis_groups"].items():
            suffix = f" [subset: {group['probe_set']}]" if group.get("probe_set") else ""
            print(f"  {name}{suffix}: {group['description']}")


if __name__ == "__main__":
    main()
