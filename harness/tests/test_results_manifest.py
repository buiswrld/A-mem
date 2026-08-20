import json

import pytest

from scripts import final_analysis
from scripts import verify_results as results_manifest


@pytest.fixture(scope="module")
def rebuilt_manifest():
    return results_manifest.build_manifest()


def test_committed_results_manifest_is_exact(rebuilt_manifest):
    committed = json.loads(results_manifest.MANIFEST_PATH.read_text(encoding="utf-8"))
    assert committed == rebuilt_manifest
    assert len(committed["runs"]) == 25
    assert sum(run["rows"] for run in committed["runs"]) == 27_760


def test_manifest_covers_every_publication_result_artifact(rebuilt_manifest):
    declared = {
        artifact["path"]
        for run in rebuilt_manifest["runs"]
        for artifact in (run["raw"], run["judged"], *run["extra_artifacts"])
    }
    actual = {
        str(path.relative_to(results_manifest.ROOT))
        for path in results_manifest.RESULTS_DIR.rglob("*")
        if path.is_file()
        and str(path.relative_to(results_manifest.ROOT))
        not in results_manifest.NON_RESULT_FILES
    }
    assert actual == declared


def test_analysis_groups_select_one_run_per_condition(rebuilt_manifest):
    runs = {run["run_id"]: run for run in rebuilt_manifest["runs"]}
    for group in rebuilt_manifest["analysis_groups"].values():
        conditions = [runs[run_id]["condition"] for run_id in group["run_ids"]]
        assert len(conditions) == len(set(conditions))


def test_final_analysis_command_comes_only_from_manifest(rebuilt_manifest):
    command = final_analysis.stats_command(
        rebuilt_manifest, "tier_b_episodic_subset"
    )
    assert command[:5] == [
        final_analysis.sys.executable,
        "-m",
        "harness.stats",
        "--probe-set",
        "betley8",
    ]
    judged = {
        run["judged"]["path"]
        for run in rebuilt_manifest["runs"]
        if run["run_id"] in rebuilt_manifest["analysis_groups"][
            "tier_b_episodic_subset"
        ]["run_ids"]
    }
    assert set(command[5:]) == judged


def test_verifier_rejects_manifest_drift(tmp_path, monkeypatch, rebuilt_manifest):
    changed = json.loads(json.dumps(rebuilt_manifest))
    changed["runs"][0]["rows"] -= 1
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(changed), encoding="utf-8")
    monkeypatch.setattr(results_manifest, "MANIFEST_PATH", path)
    with pytest.raises(SystemExit, match="VERIFICATION FAILED"):
        results_manifest.verify_manifest()
