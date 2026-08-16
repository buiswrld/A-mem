import copy
import json
import math
import re
from pathlib import Path

import pytest

from scripts.analyze_human_validation import AXES, analyze, cohens_kappa
from scripts.build_human_validation import (
    OUT_DIR,
    PER_STRATUM,
    PROTOCOL_VERSION,
    TARGET_VERDICTS,
    TIERS,
    balanced_take,
    blind_item,
    build_package,
    load_source_population,
    select_sample,
)


def _row(condition: str, family: str, sample_idx: int) -> dict:
    return {
        "condition": condition,
        "_balance_prompt": family,
        "_source_file": f"results/{condition}.jsonl",
        "probe_id": family,
        "sample_idx": sample_idx,
    }


def test_balanced_take_is_order_invariant_and_spreads_conditions():
    rows = [
        _row(condition, family, sample_idx)
        for condition in ("C1", "C2", "C3")
        for family in ("p1", "p2", "p3")
        for sample_idx in range(3)
    ]
    forward = balanced_take(copy.deepcopy(rows), 12, seed=99)
    reverse = balanced_take(copy.deepcopy(list(reversed(rows))), 12, seed=99)
    identity = lambda row: (
        row["_source_file"], row["probe_id"], row["sample_idx"]
    )
    assert [identity(row) for row in forward] == [identity(row) for row in reverse]
    assert {condition: sum(r["condition"] == condition for r in forward)
            for condition in ("C1", "C2", "C3")} == {"C1": 4, "C2": 4, "C3": 4}
    family_counts = [
        sum(r["_balance_prompt"] == family for r in forward)
        for family in ("p1", "p2", "p3")
    ]
    assert max(family_counts) - min(family_counts) <= 2


def test_blind_item_has_no_source_or_judge_metadata():
    row = _row("C1", "p1", 0) | {
        "_blind_id": "HV-001",
        "probe_text": "prompt",
        "response": "response",
        "verdict": "misaligned",
        "alignment": 0,
        "tier": "C",
    }
    assert blind_item(row) == {
        "id": "HV-001", "prompt": "prompt", "response": "response"
    }


def test_cohens_kappa_examples():
    assert cohens_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert cohens_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0
    assert math.isnan(cohens_kappa([], []))
    assert math.isnan(cohens_kappa(["a", "a"], ["a", "a"]))
    with pytest.raises(ValueError, match="different lengths"):
        cohens_kappa(["a"], [])


def test_generated_package_matches_frozen_design_and_is_blinded():
    manifest = build_package()
    assert manifest["protocol_version"] == PROTOCOL_VERSION
    assert manifest["execution_status"] == "PREPARED_NOT_EXECUTED"
    assert len(manifest["items"]) == len(TIERS) * len(TARGET_VERDICTS) * PER_STRATUM
    assert len({item["blind_id"] for item in manifest["items"]}) == 180
    for tier in TIERS:
        for verdict in TARGET_VERDICTS:
            assert sum(
                item["tier"] == tier and item["source_verdict"] == verdict
                for item in manifest["items"]
            ) == PER_STRATUM

    page_orders = []
    for rater in ("a", "b"):
        html = (OUT_DIR / f"rater_{rater}.html").read_text(encoding="utf-8")
        match = re.search(r"const ITEMS = (\[.*?\]);\nconst META", html, re.DOTALL)
        assert match
        items = json.loads(match.group(1))
        assert len(items) == 180
        assert all(set(item) == {"id", "prompt", "response"} for item in items)
        assert {item["id"] for item in items} == {
            item["blind_id"] for item in manifest["items"]
        }
        page_orders.append([item["id"] for item in items])
    assert page_orders[0] != page_orders[1]


def test_sample_selection_is_invariant_to_source_row_order():
    population = load_source_population()
    forward = select_sample(copy.deepcopy(population))
    reverse = select_sample(copy.deepcopy(list(reversed(population))))
    identities = lambda rows: [
        (row["_blind_id"], row["_source_file"], row["probe_id"], row["sample_idx"])
        for row in rows
    ]
    assert identities(forward) == identities(reverse)


def test_committed_manifest_is_exact_generator_output():
    generated = build_package()
    on_disk = json.loads((Path(OUT_DIR) / "sample_manifest.json").read_text())
    assert on_disk == generated


def test_analysis_runs_end_to_end_on_complete_ratings(capsys):
    manifest = build_package()
    ratings = {}
    for index, item in enumerate(manifest["items"]):
        ratings[item["blind_id"]] = {
            axis: labels[index % len(labels)] for axis, labels in AXES.items()
        }
    analyze(manifest, ratings, copy.deepcopy(ratings))
    output = capsys.readouterr().out
    assert "INTER-RATER AGREEMENT" in output
    assert "PRESPECIFIED CONSTRUCT CHECKS" in output
    assert "not experiment estimates" in output
