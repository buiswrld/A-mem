import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_DOCS = (
    ROOT / "README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/final_results.md",
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
