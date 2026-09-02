#!/usr/bin/env python3
"""
Normalize a SKILL.md frontmatter to the official Agent Skills schema.

The framework (skill-creator-framework §7) mandates `version:` for stateful
skills; the platform schema rejects any key outside
{name, description, allowed-tools, compatibility, license, metadata}.
This script reconciles the two by relocating non-schema keys under `metadata:`
so packaging validates without losing the collection's own conventions.

Usage:
    python normalize_frontmatter.py <path/to/SKILL.md> [--check]

    --check   report only, exit 1 if changes are needed, write nothing
"""

import sys
from pathlib import Path

ALLOWED = {
    "name",
    "description",
    "allowed-tools",
    "compatibility",
    "license",
    "metadata",
}


def split_frontmatter(text):
    """Return (frontmatter_text, body_text). Raises ValueError if absent."""
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter: file does not start with ---")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise ValueError("no frontmatter: closing --- not found")
    return text[4:end + 1], text[end + 5:]


def top_level_keys(fm_text):
    """Ordered list of (key, block_text) for each top-level key in frontmatter."""
    lines = fm_text.split("\n")
    entries = []
    current_key = None
    current = []
    for line in lines:
        if line and not line[0].isspace() and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key and all(c.isalnum() or c in "-_" for c in key):
                if current_key is not None:
                    entries.append((current_key, "\n".join(current)))
                current_key = key
                current = [line]
                continue
        if current_key is not None:
            current.append(line)
    if current_key is not None:
        entries.append((current_key, "\n".join(current)))
    return entries


def indent_block(block_text):
    """Indent a top-level key block by two spaces so it nests under metadata."""
    out = []
    for line in block_text.split("\n"):
        out.append("  " + line if line.strip() else line)
    return "\n".join(out)


def normalize(path, check_only=False):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    entries = top_level_keys(fm)

    offenders = [(k, v) for k, v in entries if k not in ALLOWED]
    if not offenders:
        return []

    if check_only:
        return [k for k, _ in offenders]

    kept = [(k, v) for k, v in entries if k in ALLOWED]
    existing_meta = next((v for k, v in kept if k == "metadata"), None)
    kept = [(k, v) for k, v in kept if k != "metadata"]

    meta_lines = ["metadata:"]
    if existing_meta is not None:
        for line in existing_meta.split("\n")[1:]:
            if line.strip():
                meta_lines.append(line)
    for _, block in offenders:
        meta_lines.append(indent_block(block).rstrip("\n"))

    # name first, then metadata, then the rest in original order
    name_block = next((v for k, v in kept if k == "name"), None)
    rest = [v for k, v in kept if k != "name"]

    parts = []
    if name_block is not None:
        parts.append(name_block.rstrip("\n"))
    parts.append("\n".join(meta_lines).rstrip("\n"))
    parts.extend(b.rstrip("\n") for b in rest)

    new_text = "---\n" + "\n".join(parts) + "\n---\n" + body
    path.write_text(new_text, encoding="utf-8")
    return [k for k, _ in offenders]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv
    if not args:
        print(__doc__)
        return 2

    target = Path(args[0])
    if target.is_dir():
        target = target / "SKILL.md"
    if not target.exists():
        print(f"not found: {target}")
        return 2

    try:
        moved = normalize(target, check_only)
    except ValueError as exc:
        print(f"{target}: {exc}")
        return 2

    if not moved:
        print(f"{target}: frontmatter already schema-clean")
        return 0

    verb = "would move" if check_only else "moved"
    print(f"{target}: {verb} to metadata: {', '.join(moved)}")
    return 1 if check_only else 0


if __name__ == "__main__":
    sys.exit(main())
