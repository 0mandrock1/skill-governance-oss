---
name: broken-inheritance
description: >
  Example skill for skill-governance-oss. Declares a parent that was never authored — the
  broken-inheritance defect `lint_dependencies.py` exists to catch. Trigger on: "broken
  inheritance example".
---

# broken-inheritance

Inherits from: nonexistent-parent-skill
Overrides: everything, in principle
Reuses verbatim: nothing, since the parent does not exist

Step 0: read `nonexistent-parent-skill`'s SKILL.md before doing anything else — except that
file was never authored.
