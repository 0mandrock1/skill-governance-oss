#!/usr/bin/env python3
"""
Bundle several already-packaged .skill files into one .skillset archive
with a manifest describing why they travel together.

A .skillset is a zip containing:
    MANIFEST.json   machine-readable index (name, version, sha256, size)
    MANIFEST.md     human-readable: reason, contract change, install order
    skills/*.skill  the individual packaged skills

Usage:
    python build_bundle.py <out.skillset> --reason "<why>" [--order a,b,c] <a.skill> <b.skill> ...

    --reason  one line: what change made these move as a set (required)
    --order   comma-separated skill names defining install order; skills not
              listed keep argument order and follow the listed ones
"""

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def read_skill_meta(skill_file):
    """Pull name + metadata.version out of the SKILL.md inside a .skill zip."""
    with zipfile.ZipFile(skill_file) as zf:
        md = [n for n in zf.namelist() if n.endswith("SKILL.md")]
        if not md:
            raise ValueError(f"{skill_file.name}: no SKILL.md inside")
        text = zf.read(sorted(md, key=len)[0]).decode("utf-8")

    name = skill_file.stem
    version = None
    in_meta = False
    for line in text.split("\n"):
        if line.startswith("---"):
            if name != skill_file.stem:
                break
            continue
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("metadata:"):
            in_meta = True
        elif in_meta:
            if line[:1].isspace() and "version:" in line:
                version = line.split("version:", 1)[1].strip()
            elif line and not line[0].isspace():
                in_meta = False
    return name, version


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build(out_path, skill_files, reason, order=None):
    out_path = Path(out_path)
    if out_path.suffix != ".skillset":
        out_path = out_path.with_suffix(".skillset")

    entries = []
    for f in skill_files:
        f = Path(f)
        if not f.exists():
            raise FileNotFoundError(f)
        name, version = read_skill_meta(f)
        entries.append(
            {
                "name": name,
                "version": version,
                "file": f"skills/{f.name}",
                "sha256": sha256(f),
                "bytes": f.stat().st_size,
                "_src": f,
            }
        )

    if order:
        rank = {n: i for i, n in enumerate(order)}
        entries.sort(key=lambda e: (rank.get(e["name"], len(rank)), e["name"]))

    manifest = {
        "format": "skillset/1",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": reason,
        "install_order": [e["name"] for e in entries],
        "skills": [{k: v for k, v in e.items() if k != "_src"} for e in entries],
    }

    lines = [
        "# Skillset",
        "",
        f"**Reason:** {reason}",
        f"**Created:** {manifest['created']}",
        "",
        "## Install order",
        "",
        "| # | Skill | Version | SHA-256 |",
        "|---|---|---|---|",
    ]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"| {i} | `{e['name']}` | {e['version'] or '—'} | `{e['sha256'][:12]}` |"
        )
    lines += [
        "",
        "Install in the order above — later skills may declare `Depends on:`",
        "earlier ones. Unpack each `.skill` into the skills root, then run the",
        "collection's lint scripts before relying on any of them.",
        "",
    ]
    manifest_md = "\n".join(lines)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        zf.writestr("MANIFEST.md", manifest_md)
        for e in entries:
            zf.write(e["_src"], e["file"])

    return out_path, manifest


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2

    reason = None
    order = None
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] == "--reason" and i + 1 < len(argv):
            reason = argv[i + 1]
            i += 2
        elif argv[i] == "--order" and i + 1 < len(argv):
            order = [s.strip() for s in argv[i + 1].split(",") if s.strip()]
            i += 2
        else:
            positional.append(argv[i])
            i += 1

    if len(positional) < 2:
        print("need an output path and at least one .skill file")
        return 2
    if not reason:
        print("--reason is required: a bundle without a stated reason is a folder")
        return 2

    out, manifest = build(positional[0], positional[1:], reason, order)
    print(f"✅ {out}  ({len(manifest['skills'])} skills)")
    for name in manifest["install_order"]:
        print(f"   {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
