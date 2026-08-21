"""Paper-ready paired analysis for the final matched C4 mechanism experiment."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import scripts.sensitivity_analysis as sens
from harness.schema import read_jsonl
from harness.stats import bootstrap_metric


def intervals(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {key: vars(value) for key, value in table.items()}


def analyze(c3_path: str, c4_path: str) -> dict[str, Any]:
    rows = {"C3E0": read_jsonl(c3_path), "C4E1": read_jsonl(c4_path)}
    if any(len(arm) != 1800 for arm in rows.values()):
        raise ValueError("expected exactly 1,800 judged rows in each arm")
    identities = {
        label: [(row["probe_id"], row["sample_idx"]) for row in arm]
        for label, arm in rows.items()
    }
    if identities["C3E0"] != identities["C4E1"]:
        raise ValueError("C3E0 and C4E1 rows are not exactly paired")

    probe_ids = {row["probe_id"] for row in rows["C3E0"]}
    cluster_map, cluster_unit = sens.cluster_map_for(probe_ids)
    comparison = (("C4E1", "C3E0"),)
    output: dict[str, Any] = {
        "n_rows_per_arm": 1800,
        "n_clusters": (
            len(set(cluster_map.values())) if cluster_map else len(probe_ids)
        ),
        "cluster_unit": cluster_unit,
        "n_boot": 2000,
        "seed": 0,
        "contrast": "C4E1-C3E0",
    }
    for metric in ("harm", "refusal", "derailment"):
        rates, differences = bootstrap_metric(
            rows,
            "D",
            metric,
            comparisons=comparison,
            n_boot=2000,
            seed=0,
            cluster_map=cluster_map,
        )
        output[metric] = {
            "rates": intervals(rates),
            "contrast": intervals(differences),
        }

    original_contrasts = sens.CONTRASTS
    try:
        sens.CONTRASTS = comparison
        sensitivity_metrics = (
            ("strict_floor", sens.classify_strict_floor, sens.harm_tally),
            ("composite", sens.classify, sens.composite_tally),
        )
        for name, classifier, tally in sensitivity_metrics:
            rates, differences, n_clusters, unit = sens.contrast_intervals(
                rows,
                "D",
                classifier,
                tally,
                n_boot=2000,
                seed=0,
            )
            output[name] = {
                "rates": rates,
                "contrast": intervals(differences),
                "n_clusters": n_clusters,
                "cluster_unit": unit,
            }
    finally:
        sens.CONTRASTS = original_contrasts
    return output


def render_text(output: dict[str, Any]) -> str:
    lines = ["C4E1 - C3E0; 2,000 paired probe-clustered draws; BCa 95%"]
    for metric in ("harm", "refusal", "derailment"):
        result = output[metric]
        difference = result["contrast"]["C4E1-C3E0"]
        lines.append(
            f"{metric}: C3E0={result['rates']['C3E0']['point']:.3%} "
            f"C4E1={result['rates']['C4E1']['point']:.3%} "
            f"diff={difference['point']:+.3%} "
            f"BCa=[{difference['bca_lo']:+.3%},{difference['bca_hi']:+.3%}]"
        )
    for name in ("strict_floor", "composite"):
        result = output[name]
        difference = result["contrast"]["C4E1-C3E0"]
        lines.append(
            f"{name}: C3E0={result['rates']['C3E0']:.3%} "
            f"C4E1={result['rates']['C4E1']:.3%} "
            f"diff={difference['point']:+.3%} "
            f"BCa=[{difference['bca_lo']:+.3%},{difference['bca_hi']:+.3%}]"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("c3")
    parser.add_argument("c4")
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="print the deterministic summary without writing analysis files",
    )
    args = parser.parse_args()
    if not args.stdout_only and args.out is None:
        parser.error("--out is required unless --stdout-only is used")

    output = analyze(args.c3, args.c4)
    rendered = render_text(output)
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "results.json").write_text(
            json.dumps(output, indent=2) + "\n", encoding="utf-8"
        )
        (args.out / "results.txt").write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
