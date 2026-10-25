import pytest

from harness.schema import read_jsonl
from scripts.grader_robustness_check import (
    PER_CELL,
    RESULTS_PATH,
    SOURCE_FILES,
    VERDICTS,
    agreement_stats,
    build_sample,
)


def test_audit_sample_is_balanced_and_deterministic():
    first = build_sample()
    second = build_sample()
    assert first == second
    assert len(first) == len(SOURCE_FILES) * len(VERDICTS) * PER_CELL
    assert len({row["audit_id"] for row in first}) == len(first)
    for condition in SOURCE_FILES:
        for verdict in VERDICTS:
            assert sum(
                row["condition"] == condition and row["reference_verdict"] == verdict
                for row in first
            ) == PER_CELL


def test_released_audit_agreement_matches_paper():
    matches, observed, kappa = agreement_stats(read_jsonl(str(RESULTS_PATH)))

    assert matches == 27
    assert observed == pytest.approx(0.45)
    assert kappa == pytest.approx(0.2204724409)
