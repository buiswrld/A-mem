"""Regression test for sample_balanced()'s exact-count guarantee.

Pure stdlib + local CSVs from the med-safety-bench submodule -- no GPU, no API
key, nothing that spends money. Run with: uv run pytest harness/tests/
"""

from __future__ import annotations

import pytest

from harness.data import sample_balanced

# n // 9 flooring used to silently under-deliver for any n not a multiple of
# 9 -- e.g. session.py's own documented default (n_turns=10) returned 9.
NON_MULTIPLES_OF_NINE = (1, 5, 10, 11, 20, 25, 30)


@pytest.mark.parametrize("n", NON_MULTIPLES_OF_NINE)
def test_sample_balanced_returns_exactly_n(n):
    picked = sample_balanced("train", n, seed=0)
    assert len(picked) == n


def test_sample_balanced_returns_unique_items():
    picked = sample_balanced("train", 25, seed=0)
    assert len({p["source"] for p in picked}) == len(picked)


def test_sample_balanced_is_deterministic_per_seed():
    a = sample_balanced("train", 10, seed=0)
    b = sample_balanced("train", 10, seed=0)
    assert a == b


def test_sample_balanced_zero_returns_empty():
    assert sample_balanced("train", 0, seed=0) == []
