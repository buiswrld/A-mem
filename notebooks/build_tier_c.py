"""Build the Tier C (generalization) probe set.

A script rather than a notebook cell because probe sets are run inputs: a
number produced from a probe set that only ever existed in someone's kernel is
not reproducible, whatever `git_sha` the row carries.

    python notebooks/build_tier_c.py

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

The probe texts are Betley's, verbatim from the vendored upstream
`first_plot_questions.yaml`: 24 ids derived from 8 questions. The current
generation harness accepts only a user prompt per probe, so the upstream
`system` field that requests JSON was not passed during the frozen runs. The
eight JSON-labelled ids therefore duplicate the eight free-form prompt texts;
the template ids are alternate formats of the same questions. Analysis must
resample the eight question families using
`harness/probes/trigger_nonclinical_24.clusters.json`, not treat the 24 ids as
independent probes.
"""
from __future__ import annotations

import json
import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from harness.data import write_probes

REPO = pathlib.Path(__file__).parent.parent


def build_tier_c() -> pathlib.Path:
    with open(REPO / "harness/probes/betley_upstream.yaml", encoding="utf-8") as source:
        spec = yaml.safe_load(source)
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
                "here. The upstream JSON system instruction is also not passed "
                "by the generation harness, so JSON-labelled ids duplicate the "
                "free-form prompt text. Tier C is INCOMPLETE until these are "
                "implemented in a new experiment."
            ),
        },
    )


if __name__ == "__main__":
    c = build_tier_c()
    with open(c, encoding="utf-8") as source:
        spec = json.load(source)
    print(f"{c}  tier {spec['tier']}  {len(spec['probes'])} probes")
