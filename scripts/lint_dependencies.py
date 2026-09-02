#!/usr/bin/env python3
"""Verify the inter-skill contract across a collection.

Checks:
  * `Depends on:` names an existing skill
  * every op in `Uses operations:` is declared in that owner's Public Interface
  * a skill declaring `Uses operations:` also declares `Depends on:`
  * `Inherits from:` names an existing skill, is not self-referential, and the child's body
    actually instructs reading the parent (Step 0)
  * at most one behavioural parent (multiple `Inherits from:` targets)
  * no inheritance cycles
  * skills declaring `## Encapsulation` expose a non-empty Public Interface
  * dangling references: a skill mentioned by another that does not exist

Usage:
  python3 lint_dependencies.py --skills ~/.claude/skills
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillparse import (load_skills, find_section, report,  # noqa: E402
                        declares_encapsulation, has_public_interface)

DEPENDS_RE = re.compile(r"^\s*Depends on:\s*(.+)$", re.M | re.I)
USES_RE = re.compile(r"^\s*Uses operations:\s*(.+)$", re.M | re.I)
INHERITS_RE = re.compile(r"^\s*Inherits from:\s*(.+)$", re.M | re.I)
OP_RE = re.compile(r"([A-Za-z0-9_.:-]+)\s*\(")


SENTINELS = {"none", "n/a", "na", "-", "\u2014", "\u2013", "", "nothing", "own root"}


def split_targets(raw):
    """Normalize a declaration line into bare skill slugs.

    Trailing parentheticals are annotations, not targets: `Depends on: craft-poster (Craft
    MCP conventions)` declares one dependency, not three.
    """
    raw = re.sub(r"[`*]", "", raw)
    raw = re.sub(r"\([^)]*\)?", "", raw)
    raw = raw.split("\u2014")[0].split(" - ")[0]
    raw = re.split(r"\.\s+|\s{2,}", raw)[0]
    out = []
    for t in re.split(r"[,+;/]| and ", raw):
        t = t.strip().strip(".").strip('"\'').strip().lower()
        if not t or t in SENTINELS or ":" in t:
            continue
        out.append(t)
    return out


def declared_ops(skill):
    body = find_section(skill["sections"], "public interface")
    if body is None:
        return None
    return {m.group(1).split(".")[-1].split(":")[-1].lower() for m in OP_RE.finditer(body)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    args = ap.parse_args()

    skills = load_skills(args.skills)
    by_name = {}
    for s in skills:
        by_name[s["dir"].lower()] = s
        if s["name"]:
            by_name[s["name"].lower()] = s

    problems, warnings = [], []
    parents = {}

    for s in skills:
        me, body = s["dir"], s["body_nocode"]
        deps = [t for m in DEPENDS_RE.findall(body) for t in split_targets(m)]
        uses = [t for m in USES_RE.findall(body) for t in split_targets(m)]
        inherits = [t for m in INHERITS_RE.findall(body) for t in split_targets(m)]

        if uses and not deps:
            problems.append("%s: `Uses operations:` without `Depends on:`" % me)

        for dep in deps:
            owner = by_name.get(dep)
            if owner is None:
                problems.append("%s: depends on unknown skill %r" % (me, dep))
                continue
            ops = declared_ops(owner)
            if ops is None:
                problems.append("%s: depends on %s, which declares no Public Interface"
                                % (me, dep))
                continue
            for call in uses:
                base = call.split(".")[0].lower()
                if base not in (dep, owner["dir"].lower()) and len(deps) > 1:
                    continue
                op = OP_RE.search(call + "(")
                op_name = call.split(".")[-1].split("(")[0].strip().lower()
                if op_name and op_name not in ops:
                    problems.append("%s: calls %s.%s(), not in %s Public Interface"
                                    % (me, dep, op_name, dep))

        if len(inherits) > 1:
            problems.append("%s: %d behavioural parents (%s) — split the skill or demote all "
                            "but one to `Depends on:`" % (me, len(inherits),
                                                          ", ".join(inherits)))
        for par in inherits:
            if par == me.lower():
                problems.append("%s: inherits from itself" % me)
                continue
            if par not in by_name:
                problems.append("%s: inherits from unknown skill %r" % (me, par))
                continue
            parents[me.lower()] = by_name[par]["dir"].lower()
            if by_name[par]["dir"] not in body and par not in body.lower():
                warnings.append("%s: declares `Inherits from: %s` but body never instructs "
                                "reading the parent SKILL.md" % (me, par))
            if not re.search(r"(read|view|open).{0,80}%s" % re.escape(par), body, re.I | re.S):
                warnings.append("%s: no explicit Step 0 read of parent %s" % (me, par))

        enc = declares_encapsulation(s)
        if enc is not None and not declared_ops(s):
            problems.append("%s: `## Encapsulation` with empty Public Interface" % me)
        elif enc is None and has_public_interface(s) \
                and "encapsulation" in " ".join(s["sections"]):
            warnings.append("%s: Public Interface without a complete `## Encapsulation` "
                            "(missing Owns)" % me)

    for child in list(parents):
        seen, cur = set(), child
        while cur in parents:
            if cur in seen:
                problems.append("inheritance cycle involving %r" % child)
                break
            seen.add(cur)
            cur = parents[cur]

    print("skills: %s (%d found)\n" % (args.skills, len(skills)))
    sys.exit(report(problems, warnings, "lint_dependencies"))


if __name__ == "__main__":
    main()
