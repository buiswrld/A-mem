"""Build and verify the Overleaf bundle from the canonical LaTeX manuscript.

The only editable manuscript sources live directly under ``paper/``. The
``paper/overleaf_upload`` directory and ZIP archive are disposable build
artifacts; this script always derives them from the canonical files.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "paper"
BUNDLE_DIR = PAPER_DIR / "overleaf_upload"
ZIP_PATH = PAPER_DIR / "overleaf_upload.zip"

SOURCE_NAMES = (
    "main.tex",
    "introduction.tex",
    "method.tex",
    "results.tex",
    "discussion.tex",
    "related_work.tex",
    "limitations.tex",
    "conclusion.tex",
    "supplement.tex",
    "checklist.tex",
    "references.bib",
    "neurips_2026.sty",
)


def expected_files() -> list[tuple[Path, Path]]:
    pairs = [(PAPER_DIR / name, Path(name)) for name in SOURCE_NAMES]
    pairs.extend(
        (path, path.relative_to(PAPER_DIR))
        for path in sorted((PAPER_DIR / "figures").glob("*.pdf"))
    )
    missing = [str(source) for source, _ in pairs if not source.is_file()]
    if missing:
        raise SystemExit("missing canonical paper source(s): " + ", ".join(missing))
    return pairs


def check() -> bool:
    pairs = expected_files()
    expected = {relative for _, relative in pairs}
    actual = {
        path.relative_to(BUNDLE_DIR)
        for path in BUNDLE_DIR.rglob("*")
        if path.is_file()
    } if BUNDLE_DIR.is_dir() else set()
    stale = actual != expected
    for source, relative in pairs:
        destination = BUNDLE_DIR / relative
        stale = stale or not destination.is_file() or not filecmp.cmp(
            source, destination, shallow=False
        )
    if not ZIP_PATH.is_file():
        stale = True
    else:
        with zipfile.ZipFile(ZIP_PATH) as archive:
            if set(archive.namelist()) != {str(path) for path in expected}:
                stale = True
            else:
                for source, relative in pairs:
                    if archive.read(str(relative)) != source.read_bytes():
                        stale = True
                        break
    return not stale


def build() -> None:
    pairs = expected_files()
    with tempfile.TemporaryDirectory(dir=PAPER_DIR) as temporary:
        staging = Path(temporary) / "overleaf_upload"
        for source, relative in pairs:
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        if BUNDLE_DIR.exists():
            shutil.rmtree(BUNDLE_DIR)
        staging.rename(BUNDLE_DIR)

    with tempfile.NamedTemporaryFile(
        dir=PAPER_DIR, prefix="overleaf_upload.", suffix=".zip", delete=False
    ) as handle:
        temporary_zip = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary_zip, "w", zipfile.ZIP_DEFLATED) as archive:
            for _, relative in pairs:
                archive.write(BUNDLE_DIR / relative, arcname=str(relative))
        temporary_zip.replace(ZIP_PATH)
    finally:
        temporary_zip.unlink(missing_ok=True)

    if not check():
        raise SystemExit("generated Overleaf bundle failed verification")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if the generated bundle is stale"
    )
    args = parser.parse_args()
    if args.check:
        if not check():
            raise SystemExit("Overleaf bundle is stale; run: python scripts/sync_paper.py")
        print("Overleaf bundle matches the canonical paper sources")
    else:
        build()
        print(f"built {BUNDLE_DIR.relative_to(ROOT)}/ and {ZIP_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
