#!/usr/bin/env python3
"""Flag instance-specific detail leaking into a behavioural parent's body.

Framework §10 rule 9 (de-instantiation): a parent that declares `## Instances` must stay
runtime-agnostic. Concrete run bindings (a PID, a literal `out.log` path, a specific run
directory), literal absolute filesystem paths, or a specific hostname/IP belong to the
instance that actually has them, not to the shared contract.

This is a heuristic WARN-only lint — it flags candidates for a human read, it does not know
whether a given literal is a genuine cross-instance invariant (a shared endpoint every
instance really does call) or a leaked instance detail. False positives are expected on
skills that legitimately own one fixed external endpoint; read the match before patching.

Usage:
  python3 lint_deinstantiation.py --skills ~/.claude/skills
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillparse import load_skills, find_section, strip_code, report  # noqa: E402

INSTANCE_PATTERNS = [
    (re.compile(r"\bPID\b", re.I), "PID reference"),
    (re.compile(r"\bout\.log\b"), "literal out.log path"),
    (re.compile(r"\brun[-_]dir\b", re.I), "literal run-dir reference"),
    (re.compile(r"\bRUN_ID\b"), "literal RUN_ID token"),
    (re.compile(r"\btask\.md\b"), "literal task.md reference"),
    (re.compile(r"(?<![\w.])/(?:root|home)/[A-Za-z0-9_./-]+"), "absolute filesystem path"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "literal IP address"),
    (re.compile(r"\b[a-z0-9-]+\.(?:mandrock\.me|duckdns\.org)\b", re.I), "literal hostname"),
]


def check(skill):
    body = skill["body"]
    if find_section(skill["sections"], "instances") is None:
        return []
    # Instances table itself is allowed to name concrete things (that's its job);
    # strip it, plus code fences, before scanning the rest of the body.
    nested = re.sub(r"(?is)##\s*Instances.*?(?=\n##\s|\Z)", "", body)
    clean = strip_code(nested)
    hits = []
    for pattern, label in INSTANCE_PATTERNS:
        for m in pattern.finditer(clean):
            hits.append("%s: %s (%r)" % (skill["dir"], label, m.group(0)))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    args = ap.parse_args()

    skills = load_skills(args.skills)
    warnings = []
    for skill in skills:
        warnings.extend(check(skill))

    return report([], warnings, "lint_deinstantiation")


if __name__ == "__main__":
    sys.exit(main())
