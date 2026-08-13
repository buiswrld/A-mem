"""Build the Tier O (over-refusal) and Tier C (generalization) probe sets.

A script rather than a notebook cell because probe sets are run inputs: a
number produced from a probe set that only ever existed in someone's kernel is
not reproducible, whatever `git_sha` the row carries.

    python notebooks/build_tiers_o_c.py

## Tier O -- over-refusal

Source: `zzha6204/Health-ORSC-Bench` (arXiv 2601.17642, ACL 2026 Findings),
the benchmark `implementation-plan.md` names. STATUS.md item 9 asked whether it
was downloadable: it is -- public, ungated, and it ships the exact Hard-1K /
Medium-5K / Easy-5K splits the plan asks for.

We take **Hard-1K**, stratified across all seven health categories. Hard is the
split where the paper measures frontier models refusing up to 80% of benign
prompts, so it is where an over-refusal effect is visible at this sample size.

**These prompts are benign by construction and adversarial by appearance.**
Each is an obfuscated rewrite of a genuinely toxic seed, and the seed is kept
in `original_question` -- deliberately, because it is the handle a human needs
to check the rewrite really is benign. Some read as though they retain the
seed's intent, which matters here more than usual: on Tier O a refusal is the
*error being measured*, so any item that is actually harmful inverts its own
score. `original_question` travels into the probe record so that check can be
done without re-downloading anything. **It has not been done yet.**

## Tier C -- masking vs suppression

`implementation-plan.md` specifies Tier C as "trigger probes per 2604.25891 +
non-clinical prompts". Only the second half is buildable from this repo:
PAPERS.md marks 2604.25891 "Read in full (PDF extract incomplete)", so the
trigger recipe is not recorded anywhere here, and inventing one would produce a
probe set that cites a paper it does not implement.

So this builds the half that is specified, which is also the half that carries
the headline metric. RELATED_WORK.md states the requirement plainly: the
non-clinical prompts must be run *while corrective memory is present*. Recovery
on Tier C against Recovery on Tier D is then the repair generalization gap --
if corrective notes fix clinical harm but leave the model hostile about
marriage and money, the repair is conditional, not realignment.

The probes are Betley's, verbatim from the vendored upstream
`first_plot_questions.yaml`, all 24 variants (8 questions x free-form / json /
template) rather than the 8 free-form of `betley8`. Same questions Gate 1 used,
three response formats, so the probe count supports a probe-clustered interval
without a single word being paraphrased.
"""
from __future__ import annotations

import collections
import json
import pathlib
import random
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from harness.data import write_probes  # noqa: E402

REPO = pathlib.Path(__file__).parent.parent
N_TIER_O = 180          # matches msb_test_180, so tier D and tier O share CI machinery
ORSC_REPO = "zzha6204/Health-ORSC-Bench"
ORSC_FILE = "data/difficulty/health-orsc-hard-1k.jsonl"


def build_tier_o() -> pathlib.Path:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(ORSC_REPO, ORSC_FILE, repo_type="dataset")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]

    by_cat: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_cat[r["classification"]].append(r)

    rng = random.Random(0)
    per = N_TIER_O // len(by_cat)
    picked: list[dict] = []
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=lambda r: str(r["id"]))
        picked += rng.sample(items, min(per, len(items)))
    # top up deterministically if 180 does not divide evenly by category count
    if len(picked) < N_TIER_O:
        rest = [r for r in sorted(rows, key=lambda r: str(r["id"])) if r not in picked]
        picked += rng.sample(rest, N_TIER_O - len(picked))

    probes = [
        {
            "probe_id": f"orsc-{r['id']}",
            "text": r["question"],
            "category": r["classification"],
            # kept so a human can verify the rewrite is really benign -- on this
            # tier a refusal is the error, so a harmful item scores backwards
            "original_question": r["original_question"],
            "seed_refuse_rate": r.get("refuse_rate"),
        }
        for r in sorted(picked, key=lambda r: str(r["id"]))
    ]
    return write_probes(
        probes,
        set_id="orsc_hard_180",
        tier="O",
        provenance={
            "source": f"{ORSC_REPO}:{ORSC_FILE}",
            "paper": "arXiv:2601.17642 (Health-ORSC-Bench, ACL 2026 Findings)",
            "split": "hard-1k",
            "sampling": f"{per} per category x {len(by_cat)} categories, random.Random(0)",
            "verbatim": True,
            "human_verified": False,
            "caveat": (
                "Benign-by-construction rewrites of toxic seeds. On tier O a "
                "refusal is the measured error, so any item that still carries "
                "its seed's intent scores backwards. original_question is "
                "retained per probe for that human check, which is NOT done."
            ),
        },
    )


def build_tier_c() -> pathlib.Path:
    spec = yaml.safe_load(open(REPO / "harness/probes/betley_upstream.yaml"))
    probes = []
    for entry in spec:
        paraphrases = entry["paraphrases"]
        if isinstance(paraphrases, str):
            paraphrases = json.loads(paraphrases.replace("'", '"'))
        for i, text in enumerate(paraphrases):
            probes.append(
                {
                    "probe_id": entry["id"] if len(paraphrases) == 1 else f"{entry['id']}-{i}",
                    "text": text,
                    "variant": ("json" if entry["id"].endswith("_json")
                                else "template" if entry["id"].endswith("_template")
                                else "free_form"),
                }
            )
    return write_probes(
        probes,
        set_id="trigger_nonclinical_24",
        tier="C",
        provenance={
            "source": "harness/probes/betley_upstream.yaml (first_plot_questions.yaml)",
            "verbatim": True,
            "human_verified": False,
            "covers": (
                "The 'non-clinical prompts, with corrective memory present' half "
                "of Tier C. Recovery here vs Recovery on tier D is the repair "
                "generalization gap."
            ),
            "does_not_cover": (
                "The 2604.25891 fine-tune-cued trigger recipe. PAPERS.md marks "
                "that paper 'Read in full (PDF extract incomplete)', so the "
                "recipe is not recorded in this repo and is not implemented "
                "here. Tier C is INCOMPLETE until it is."
            ),
        },
    )


if __name__ == "__main__":
    o = build_tier_o()
    c = build_tier_c()
    for p in (o, c):
        s = json.load(open(p))
        print(f"{p}  tier {s['tier']}  {len(s['probes'])} probes")
