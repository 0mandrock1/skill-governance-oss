#!/usr/bin/env python3
"""Static consistency check between a state registry and a skill collection.

Checks:
  * every Owner skill named in the registry actually exists
  * every registry owner declares `## Encapsulation`
  * orphan / TBD / empty owner cells
  * two rows claiming the same state name with different owners
  * skills that own state (have `## Encapsulation`) but appear in no registry row
  * rows whose Verified date is missing or older than --max-age days

Usage:
  python3 validate_registry.py --skills ~/.claude/skills --registry ~/registry.md
"""

import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillparse import load_skills, report, declares_encapsulation  # noqa: E402

ORPHAN_TOKENS = ("orphan", "tbd", "n/a", "none", "?", "-", "—", "–", "")
DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_tables(md):
    """Yield (headers, row_cells) for every pipe table in the markdown."""
    rows, headers = [], None
    for line in md.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            headers = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            continue
        if headers is None:
            headers = [c.lower() for c in cells]
            continue
        rows.append((headers, cells))
    return rows


def cell(headers, cells, *names):
    for n in names:
        for i, h in enumerate(headers):
            if n in h and i < len(cells):
                return cells[i]
    return ""


def clean_owner(raw):
    return re.sub(r"[`*_()]", "", raw).split("(")[0].strip().strip(".").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True, help="collection root containing skill dirs")
    ap.add_argument("--registry", default=None,
                    help="filled-in registry markdown; defaults to "
                         "../references/state-registry.md next to this script")
    ap.add_argument("--max-age", type=int, default=120,
                    help="days before a Verified date is considered stale (0 disables)")
    args = ap.parse_args()

    if args.registry is None:
        here = os.path.dirname(os.path.abspath(__file__))
        args.registry = os.path.join(here, "..", "references", "state-registry.md")
        if not os.path.isfile(args.registry):
            print("no registry found at %s — pass --registry explicitly" % args.registry)
            sys.exit(2)

    skills = load_skills(args.skills)
    by_name = {}
    for s in skills:
        by_name[s["dir"].lower()] = s
        if s["name"]:
            by_name[s["name"].lower()] = s

    with open(args.registry, encoding="utf-8") as fh:
        registry = fh.read()

    problems, warnings = [], []
    claimed, seen_state = set(), {}
    today = datetime.date.today()

    for headers, cells in parse_tables(registry):
        owner_raw = cell(headers, cells, "owner")
        if not any("owner" in h for h in headers):
            continue
        # Backlog tables (orphans, known defects, changelog) name owners that do not exist
        # yet by design; they are tracked, not enforced.
        if any(k in h for h in headers for k in ("suspected", "decision", "defect", "fix")):
            continue
        state = cell(headers, cells, "location", "database", "schema", "path", "channel",
                     "repo", "store", "state") or cells[0]
        state = re.sub(r"[`*]", "", state).strip()
        if not state or state.lower() in ("", "|"):
            continue
        owner = clean_owner(owner_raw)

        if owner in ORPHAN_TOKENS or "orphan" in owner or "tbd" in owner:
            problems.append("orphan state, no owner declared: %r" % state)
            continue
        if owner not in by_name:
            problems.append("registry row %r names unknown owner skill %r" % (state, owner))
            continue

        claimed.add(by_name[owner]["dir"].lower())
        prev = seen_state.get(state.lower())
        if prev and prev != owner:
            problems.append("state %r claimed by two owners: %r and %r" % (state, prev, owner))
        seen_state[state.lower()] = owner

        if declares_encapsulation(by_name[owner]) is None:
            problems.append("owner %r of %r has no `## Encapsulation` section"
                            % (owner, state))

        verified = cell(headers, cells, "verified")
        m = DATE_RE.search(verified)
        if args.max_age:
            if not m:
                warnings.append("no Verified date on row %r" % state)
            else:
                d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                age = (today - d).days
                if age > args.max_age:
                    warnings.append("row %r last verified %d days ago" % (state, age))

    for s in skills:
        if declares_encapsulation(s) is not None \
                and s["dir"].lower() not in claimed:
            problems.append("skill %r declares `## Encapsulation` but owns nothing in the "
                            "registry — unregistered state" % s["dir"])

    print("registry: %s\nskills:   %s (%d found)\n" % (args.registry, args.skills, len(skills)))
    sys.exit(report(problems, warnings, "validate_registry"))


if __name__ == "__main__":
    main()
