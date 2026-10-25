from scripts.sync_paper import PAPER_DIR, SOURCE_NAMES, expected_files


def test_canonical_paper_sources_are_complete() -> None:
    pairs = expected_files()
    relative_paths = {str(relative) for _, relative in pairs}

    assert set(SOURCE_NAMES) <= relative_paths
    assert any(path.startswith("figures/") for path in relative_paths)
    assert all(source.is_relative_to(PAPER_DIR) for source, _ in pairs)
