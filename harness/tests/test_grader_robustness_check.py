from scripts.grader_robustness_check import PER_CELL, SOURCE_FILES, VERDICTS, build_sample


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
