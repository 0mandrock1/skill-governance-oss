#!/usr/bin/env python3
"""
Unpack a .skillset bundle (or a bare .skill) into a skills root, or split it
back into its individual .skill files.

Verifies every member against MANIFEST.json, installs in the manifest's
declared order, and never overwrites an existing skill silently — the old
directory is moved aside first.

Usage:
    python unpack_bundle.py <bundle.skillset|skill.skill> [--into DIR] [--dry-run] [--force]
    python unpack_bundle.py <bundle.skillset> --emit-skills DIR

    --into         skills root (default: ~/.claude/skills)
    --dry-run      report the plan, touch nothing
    --force        replace an existing skill (its directory is backed up first)
    --emit-skills  write members out as separate .skill files instead of
                   installing them — for environments with no writable skills
                   root (a chat sandbox), where the .skill files themselves are
                   the deliverable. Members are copied byte-for-byte, so their
                   checksums still match the manifest.

Exit codes: 0 ok, 1 refused (collision without --force), 2 bad input.
"""

import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".claude" / "skills"


def sha256_bytes(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def read_manifest(zf):
    """Return the manifest dict, or None for a bare .skill with no manifest."""
    if "MANIFEST.json" not in zf.namelist():
        return None
    return json.loads(zf.read("MANIFEST.json").decode("utf-8"))


def skill_root_dir(skill_bytes):
    """Top-level directory name inside a .skill archive."""
    with zipfile.ZipFile(fileobj_of(skill_bytes)) as zf:
        tops = {n.split("/")[0] for n in zf.namelist() if "/" in n}
        if len(tops) != 1:
            raise ValueError(f"expected exactly one top-level dir, got {sorted(tops)}")
        return tops.pop()


def fileobj_of(data):
    import io

    return io.BytesIO(data)


def plan_from_bundle(path):
    """Return (entries, manifest). Each entry: dict(name, bytes, sha_ok)."""
    path = Path(path)
    data = path.read_bytes()

    if path.suffix == ".skill":
        name = skill_root_dir(data)
        return [{"name": name, "bytes": data, "sha_ok": None}], None

    with zipfile.ZipFile(fileobj_of(data)) as zf:
        manifest = read_manifest(zf)
        members = [n for n in zf.namelist() if n.startswith("skills/") and n.endswith(".skill")]
        if not members:
            raise ValueError("no skills/*.skill members — not a skillset")

        by_file = {}
        for m in members:
            blob = zf.read(m)
            by_file[m] = blob

    entries = []
    if manifest:
        for row in manifest["skills"]:
            blob = by_file.get(row["file"])
            if blob is None:
                raise ValueError(f"manifest lists {row['file']}, missing from archive")
            entries.append(
                {
                    "name": row["name"],
                    "bytes": blob,
                    "sha_ok": sha256_bytes(blob) == row.get("sha256"),
                    "version": row.get("version"),
                }
            )
        listed = {r["file"] for r in manifest["skills"]}
        for extra in sorted(set(by_file) - listed):
            entries.append(
                {"name": skill_root_dir(by_file[extra]), "bytes": by_file[extra],
                 "sha_ok": None, "version": None}
            )
    else:
        for m in sorted(by_file):
            entries.append(
                {"name": skill_root_dir(by_file[m]), "bytes": by_file[m],
                 "sha_ok": None, "version": None}
            )
    return entries, manifest


def install(entry, root, force, dry_run):
    """Install one entry. Returns a status string."""
    target = root / entry["name"]
    backup = None

    if target.exists():
        if not force:
            return f"REFUSED  {entry['name']} — already exists (use --force)"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = target.with_name(f"{entry['name']}.bak-{stamp}")

    if dry_run:
        note = f" (would back up existing → {backup.name})" if backup else ""
        return f"would install  {entry['name']}{note}"

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(fileobj_of(entry["bytes"])) as zf:
            zf.extractall(tmp)
        staged = Path(tmp) / entry["name"]
        if not (staged / "SKILL.md").exists():
            return f"FAILED   {entry['name']} — no SKILL.md in archive"
        if backup:
            target.rename(backup)
        shutil.copytree(staged, target)

    note = f" (old → {backup.name})" if backup else ""
    return f"installed  {entry['name']}{note}"


def emit_skills(entries, out_dir):
    """Write each member out as its own .skill file. Returns status lines."""
    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for e in entries:
        target = out_dir / f"{e['name']}.skill"
        target.write_bytes(e["bytes"])
        digest = sha256_bytes(e["bytes"])
        lines.append(f"wrote  {target.name}  {digest[:12]}  {len(e['bytes'])} B")
    return lines


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2

    dry_run = "--dry-run" in argv
    force = "--force" in argv
    root = DEFAULT_ROOT
    emit_dir = None
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] == "--into" and i + 1 < len(argv):
            root = Path(argv[i + 1]).expanduser()
            i += 2
        elif argv[i] == "--emit-skills" and i + 1 < len(argv):
            emit_dir = argv[i + 1]
            i += 2
        elif argv[i].startswith("--"):
            i += 1
        else:
            positional.append(argv[i])
            i += 1

    if not positional:
        print("need a .skillset or .skill path")
        return 2

    src = Path(positional[0]).expanduser()
    if not src.exists():
        print(f"not found: {src}")
        return 2

    try:
        entries, manifest = plan_from_bundle(src)
    except (ValueError, zipfile.BadZipFile) as exc:
        print(f"{src.name}: {exc}")
        return 2

    if manifest:
        print(f"reason: {manifest.get('reason', '—')}")
        print(f"created: {manifest.get('created', '—')}")
    print(f"target: {emit_dir if emit_dir else root}")
    print()

    bad = [e["name"] for e in entries if e["sha_ok"] is False]
    if bad:
        print("checksum mismatch — archive altered since it was built:")
        for n in bad:
            print(f"   {n}")
        print("refusing to install")
        return 2

    if emit_dir:
        if dry_run:
            for e in entries:
                print(f"  would write  {e['name']}.skill")
            print("\ndry run — nothing written")
            return 0
        for line in emit_skills(entries, emit_dir):
            print(f"  {line}")
        print("\nthese are packaged skills, not an installation —")
        print("run this again with --into <skills root> to actually install them")
        return 0

    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)

    results = [install(e, root, force, dry_run) for e in entries]
    for r in results:
        print(f"  {r}")

    refused = [r for r in results if r.startswith("REFUSED")]
    failed = [r for r in results if r.startswith("FAILED")]
    print()
    if dry_run:
        print("dry run — nothing written")
    elif not refused and not failed:
        print("run the collection lint scripts before relying on these:")
        print("  python skill-creator-framework/scripts/lint_dependencies.py --skills", root)
        print("  python skill-creator-framework/scripts/audit_triggers.py --skills", root)
    return 1 if (refused or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
