#!/usr/bin/env python3
"""Detect trigger-phrase collisions across a skill collection.

Extracts quoted trigger phrases and slash commands from every description, normalizes them,
and reports any phrase claimed by more than one skill. Also flags descriptions that exceed
the spec limit, carry no quoted triggers at all, or sit next to a near neighbour without a
NOT-trigger line.

Usage:
  python3 audit_triggers.py --skills ~/.claude/skills
  python3 audit_triggers.py --skills ~/.claude/skills --min-overlap 3
"""

import argparse
import os
import re
import sys
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skillparse import load_skills, report  # noqa: E402

QUOTED_RE = re.compile("[\"\u201c\u201d\u00ab\u00bb]([^\"\u201c\u201d\u00ab\u00bb]{2,60})"
                       "[\"\u201c\u201d\u00ab\u00bb]")
SLASH_RE = re.compile(r"(?<![\w/])/([a-z0-9][a-z0-9_-]{2,60})(?![\w/])")
LETTER_RUN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
NOT_RE = re.compile(r"(not\s+trigger|do\s+not\s+trigger|don't\s+trigger|не\s+trigger|"
                    r"НЕ\s+trigger)", re.I)
DESC_LIMIT = 1024
NAME_LIMIT = 64

# Homoglyph guard: Cyrillic letters that look identical to Latin ones.
CONFUSABLES = {"\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c",
               "\u0445": "x", "\u0443": "y", "\u0456": "i", "\u0410": "A", "\u0412": "B",
               "\u0421": "C", "\u0415": "E", "\u041d": "H", "\u041a": "K", "\u041c": "M",
               "\u041e": "O", "\u0420": "P", "\u0422": "T", "\u0425": "X"}


def normalize(phrase):
    p = unicodedata.normalize("NFKC", phrase).strip().lower()
    p = re.sub(r"[^\w\s/-]", " ", p, flags=re.UNICODE)
    p = re.sub(r"\s+", " ", p).strip()
    return p


def script_of(phrase):
    """Rough per-language bucketing so trigger spaces are audited separately."""
    return "cyr" if re.search(r"[\u0400-\u04FF]", phrase) else "lat"


def homoglyphs(text):
    """Flag a single contiguous letter run mixing Latin with look-alike Cyrillic.

    Hyphenated Ukrenglish compounds ("Craft-\u0434\u043e\u043a") are legitimate and split into separate
    runs, so they are not reported. "refer\u0435nce" with a Cyrillic e is.
    """
    hits = []
    for run in LETTER_RUN_RE.findall(text):
        has_cyr = any(ch in CONFUSABLES for ch in run)
        has_lat = any("a" <= ch.lower() <= "z" for ch in run)
        if has_cyr and has_lat:
            hits.append(run)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    ap.add_argument("--min-overlap", type=int, default=1,
                    help="report a pair after this many shared phrases")
    args = ap.parse_args()

    skills = load_skills(args.skills)
    problems, warnings = [], []
    owners = defaultdict(set)
    phrases_by_skill = {}

    for s in skills:
        desc, name, me = s["description"], s["name"], s["dir"]

        if not name:
            problems.append("%s: missing `name:` in frontmatter" % me)
        elif name != me:
            problems.append("%s: `name: %s` does not match directory" % (me, name))
        elif len(name) > NAME_LIMIT:
            problems.append("%s: name is %d chars (limit %d)" % (me, len(name), NAME_LIMIT))
        if not re.fullmatch(r"[a-z0-9-]*", name or ""):
            problems.append("%s: name must be lowercase letters, digits and hyphens" % me)

        if not desc:
            problems.append("%s: empty description — the skill will never trigger" % me)
            continue
        if len(desc) > DESC_LIMIT:
            problems.append("%s: description is %d chars (limit %d)"
                            % (me, len(desc), DESC_LIMIT))

        for bad in homoglyphs(desc) + homoglyphs(s["body"][:4000]):
            warnings.append("%s: mixed-script word %r — likely a homoglyph typo" % (me, bad))

        found = {normalize(p) for p in QUOTED_RE.findall(desc)}
        found |= {normalize("/" + c) for c in SLASH_RE.findall(desc)}
        found = {p for p in found if p and len(p) > 2}
        phrases_by_skill[me] = found

        if not found:
            warnings.append("%s: description has no quoted trigger phrases — triggering is "
                            "left entirely to paraphrase" % me)
        for p in found:
            owners[p].add(me)

    for phrase, who in sorted(owners.items()):
        if len(who) > 1:
            problems.append("phrase %r claimed by %d skills: %s"
                            % (phrase, len(who), ", ".join(sorted(who))))

    families = defaultdict(set)
    for me in phrases_by_skill:
        families[me.split("-")[0]].add(me)
    for me, found in phrases_by_skill.items():
        neighbour = (len(families[me.split("-")[0]]) > 1
                     or any(len(owners[p]) > 1 for p in found))
        if neighbour and not NOT_RE.search(next(
                s["description"] for s in skills if s["dir"] == me)):
            warnings.append("%s: has near neighbours but no NOT-trigger line" % me)

    names = sorted(phrases_by_skill)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for script in ("lat", "cyr"):
                pa = {p for p in phrases_by_skill[a] if script_of(p) == script}
                pb = {p for p in phrases_by_skill[b] if script_of(p) == script}
                shared = pa & pb
                if len(shared) >= max(args.min_overlap, 1) and len(shared) > 1:
                    warnings.append("%s vs %s: %d shared %s phrases (%s)"
                                    % (a, b, len(shared), script,
                                       ", ".join(sorted(shared)[:4])))

    print("skills: %s (%d found)\n" % (args.skills, len(skills)))
    sys.exit(report(problems, warnings, "audit_triggers"))


if __name__ == "__main__":
    main()
