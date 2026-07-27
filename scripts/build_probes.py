"""Turn the MedSafetyBench TEST split into a Tier D probe set.

    uv run python scripts/build_probes.py --n 90

Test split only. The train split becomes gold notes (scripts/build_notes.py),
and keeping that boundary is what makes Invariant #2 hold by construction:
no note can restate an answer to a probe, because no note was built from a
probe's row.

Sampling is balanced across the 9 AMA principles and both generators, so a
harm rate is not dominated by whichever category happened to be oversampled.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random

import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_notes import AMA_PRINCIPLES, load_pairs  # noqa: E402

PROBE_DIR = pathlib.Path(__file__).parent.parent / "harness" / "probes"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=90, help="probes total (multiple of 9)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(PROBE_DIR / "msb_test.json"))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    per_cat = max(1, args.n // 9)
    probes = []
    for cat in range(1, 10):
        pool = load_pairs("test", "gpt4", cat) + load_pairs("test", "llama2", cat)
        rng.shuffle(pool)
        for p in pool[:per_cat]:
            probes.append({
                "probe_id": p["source"],
                "text": p["request"],
                "principle": cat,
                "generator": p["generator"],
            })

    spec = {
        "set_id": "msb_test",
        "version": "v1",
        "tier": "D",
        "provenance": {
            "source": "MedSafetyBench test split (subrepos/med-safety-bench, MIT, research-only)",
            "built": "scripts/build_probes.py",
            "seed": args.seed,
            "verbatim": True,
            "note": "Test split only. Gold notes come from the train split, so no note "
                    "can restate a probe's safe response -- Invariant #2 by construction.",
        },
        "held_out_rule": "No item from datasets/test/ may ever enter a memory collection.",
        "ama_principles": AMA_PRINCIPLES,
        "probes": probes,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print(f"wrote {len(probes)} probes ({per_cat} per AMA principle) to {args.out}")


if __name__ == "__main__":
    main()
