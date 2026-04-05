"""Extract a single version section from CHANGELOG.md for GitHub releases."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: extract_release_notes.py <tag> <changelog_path> <output_path>",
            file=sys.stderr,
        )
        return 1

    tag, changelog_path, output_path = sys.argv[1:4]
    version = tag[1:] if tag.startswith("v") else tag

    changelog = Path(changelog_path).read_text(encoding="utf-8")

    pattern = re.compile(
        rf"^## \[{re.escape(version)}\].*?(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(changelog)
    if not match:
        print(
            f"Could not find a CHANGELOG section for version {version}",
            file=sys.stderr,
        )
        return 2

    release_notes = match.group(0).strip() + "\n"
    Path(output_path).write_text(release_notes, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
