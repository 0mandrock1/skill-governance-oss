"""Shared SKILL.md parsing helpers for the framework lint scripts.

No third-party dependencies: the frontmatter subset used by skills is parsed directly so the
scripts run anywhere Python 3.8+ runs.
"""

import os
import re

SECTION_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.M)


def _parse_frontmatter(text):
    """Parse the leading --- block. Supports `key: value` and `key: >`/`|` block scalars."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:]

    data, key, buf, indent = {}, None, [], None
    for line in raw.split("\n"):
        if key is not None:
            stripped = line.strip()
            cur_indent = len(line) - len(line.lstrip())
            if stripped and (indent is None or cur_indent >= indent):
                if indent is None:
                    indent = cur_indent
                buf.append(stripped)
                continue
            data[key] = " ".join(buf).strip()
            key, buf, indent = None, [], None
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v in (">", "|", ">-", "|-", ">+", "|+"):
            key, buf, indent = k, [], None
        else:
            data[k] = v.strip("'\"")
    if key is not None:
        data[key] = " ".join(buf).strip()
    return data, body


FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.M | re.S)


def strip_code(body):
    """Remove fenced code blocks so template placeholders are not parsed as real values."""
    return FENCE_RE.sub("", body)


def _nested_version(text):
    """Read `version:` nested under `metadata:` in the frontmatter.

    The platform's SKILL.md schema rejects a top-level `version:` key, so the
    collection's convention (framework §7) survives packaging only as
    `metadata.version`. The flat frontmatter parser above cannot see indented
    keys, so recover it here rather than silently reporting every packaged
    skill as unversioned.
    """
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    in_meta = False
    for line in text[3:end].split("\n"):
        if re.match(r"^metadata:\s*$", line):
            in_meta = True
            continue
        if in_meta:
            if line.strip() and not line[0].isspace():
                break
            m = re.match(r"^\s+version:\s*(.+?)\s*$", line)
            if m:
                return m.group(1).strip("'\"")
    return ""


def sections(body):
    """Return {heading_text_lower: section_body} for every markdown heading."""
    out, marks = {}, list(SECTION_RE.finditer(body))
    for i, m in enumerate(marks):
        start = m.end()
        stop = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        out[m.group(2).strip().lower()] = body[start:stop]
    return out


def find_section(secs, *needles):
    """First section whose heading contains any needle."""
    for head, content in secs.items():
        for n in needles:
            if n in head:
                return content
    return None


def load_skills(root):
    """Yield dicts for every SKILL.md under root (one level of nesting or deeper)."""
    skills = []
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" not in filenames:
            continue
        path = os.path.join(dirpath, "SKILL.md")
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print("  ! cannot read %s: %s" % (path, exc))
            continue
        meta, body = _parse_frontmatter(text)
        skills.append({
            "dir": os.path.basename(dirpath),
            "path": path,
            "name": meta.get("name", ""),
            "version": meta.get("version", "") or _nested_version(text),
            "description": meta.get("description", ""),
            "meta": meta,
            "body": body,
            "body_nocode": strip_code(body),
            "sections": sections(body),
        })
        dirnames[:] = [d for d in dirnames if d not in ("references", "scripts", "assets")]
    return sorted(skills, key=lambda s: s["dir"])


def nested_section(body, heading_name):
    """Section content INCLUDING its sub-headings.

    `sections()` cuts at the next heading of any level, so a `## Encapsulation`
    section stops dead at its own `### Owns`. Anything checking for a subsection
    must use this instead: it runs to the next heading of the same or higher
    level, which is what markdown nesting actually means.
    """
    marks = list(SECTION_RE.finditer(body))
    for i, m in enumerate(marks):
        head = re.sub(r"^[\d.\s]+", "", m.group(2).strip().lower()).strip()
        if head != heading_name:
            continue
        level = len(m.group(1))
        stop = len(body)
        for nxt in marks[i + 1:]:
            if len(nxt.group(1)) <= level:
                stop = nxt.start()
                break
        return body[m.end():stop]
    return None


def declares_encapsulation(skill):
    """True only for a real state declaration, not a chapter discussing the concept.

    Requires a heading that normalizes to exactly "encapsulation" and an Owns subsection
    outside code fences — so the framework's own explanatory section does not self-trip.
    """
    content = nested_section(skill["body"], "encapsulation")
    if content is None:
        return None
    clean = strip_code(content)
    # `### Owns` heading, or an inline `Owns:` line — both are used in practice
    # and both are a real ownership declaration.
    if re.search(r"^\s*#{2,4}\s*Owns\b", clean, re.M | re.I):
        return content
    if re.search(r"^\s*\**Owns\**\s*:", clean, re.M | re.I):
        return content
    # Framework §4.5: a skill that declares itself stateless owns nothing and is
    # exempt from the Owns requirement. Honour that instead of flagging it.
    if re.search(r"\bstateless\b", clean, re.I):
        return content
    return None


def has_public_interface(skill):
    """True if the skill declares a Public Interface outside code fences.

    Checked against the fence-stripped body so a skill quoting the interface
    template as an example — the framework itself does — is not counted as
    declaring one.
    """
    for head in sections(skill["body_nocode"]):
        norm = re.sub(r"^[\d.\s]+", "", head).strip()
        if norm.startswith("public interface"):
            return True
    return False


def report(problems, warnings, label):
    """Print a uniform result block and return a shell exit code."""
    for w in warnings:
        print("  WARN  %s" % w)
    for p in problems:
        print("  FAIL  %s" % p)
    if not problems and not warnings:
        print("  OK    %s" % label)
    print("\n%s: %d failure(s), %d warning(s)" % (label, len(problems), len(warnings)))
    return 1 if problems else 0
