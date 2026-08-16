import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DOCS = (
    ROOT / "README.md",
    ROOT / "docs/experiment_freeze.md",
    ROOT / "docs/project_review.md",
    ROOT / "docs/onboarding.md",
    ROOT / "docs/tierC_results.md",
    ROOT / "docs/paired_contrasts.md",
    ROOT / "docs/agent-context/STATUS.md",
    ROOT / "docs/agent-context/PROJECT_CONTEXT.md",
    ROOT / "docs/paper/intro.md",
)


def test_active_docs_do_not_reopen_closed_experiments():
    forbidden = (
        "tier o does not exist",
        "pending human validation",
        "prepared_prompts/c5_scrambled",
        "what is owed",
        "needs gpu",
    )
    for path in ACTIVE_DOCS:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"{path.relative_to(ROOT)} contains {phrase!r}"


def test_active_local_markdown_links_exist():
    link_pattern = re.compile(r"\[[^]]*]\(([^)]+)\)")
    for path in ACTIVE_DOCS:
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (path.parent / target).resolve().exists(), (
                f"{path.relative_to(ROOT)} links to missing {target}"
            )


def test_human_audit_is_unexecuted_and_has_no_exports():
    manifest = json.loads(
        (ROOT / "human_validation/sample_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["execution_status"] == "PREPARED_NOT_EXECUTED"
    ratings = ROOT / "human_validation/ratings"
    assert not ratings.exists() or not list(ratings.iterdir())


def test_c5_final_artifact_is_named_placebo():
    assert (ROOT / "prepared_prompts/C5_placebo_rag_prompts.jsonl").exists()
    assert not (ROOT / "prepared_prompts/C5_scrambled_rag_prompts.jsonl").exists()
