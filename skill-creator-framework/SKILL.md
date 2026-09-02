---
name: skill-creator-framework
metadata:
  version: 2.1.0
description: >
  MANDATORY framework for authoring, editing, refactoring, renaming, splitting, merging,
  deprecating or deleting ANY Claude Skill. Read BEFORE touching a line of any SKILL.md —
  including quick fixes and one-trigger tweaks. Covers the OOP model of skills, inheritance,
  state ownership, the inter-skill API, trigger collisions, lifecycle, testing, credential
  threat model, state registry; ships lint scripts. Trigger on:
  "skill-creator-framework", "створи скіл", "новий скіл", "як зробити скіл",
  "онови скіл", "виправ скіл", "рефактор скіла", "додай тригер", "аудит скілів",
  "конвенції скілів", "create a skill", "edit this skill", "SKILL.md", "skill audit". ALSO trigger unasked whenever skill-creator,
  skill-rosetta, skill-doc-framework, skill-translator, skills-sync, cowork-prompt or
  cc-prompt-writer runs, or a SKILL.md is about to be written. Over-trigger deliberately.
  NOT trigger: running evals or tuning one description alone — that is skill-creator, which
  reads this first anyway.
---

# skill-creator-framework

This directory exists so skills that declare `Inherits from: skill-creator-framework` or
`Depends on: skill-creator-framework` resolve to a real skill directory when the whole
collection is linted together — it is a thin pointer, not a second copy of the framework.

**The governing document itself is [`../SPEC.md`](../SPEC.md).** Read that in full before
doing anything else in this skill, or any skill that inherits from it. References live in
[`../references/`](../references/), the three lint scripts in [`../scripts/`](../scripts/),
and the layered-enforcement instructions in [`../ENFORCEMENT.md`](../ENFORCEMENT.md).

If you are installing this framework as a standalone skill into your own collection (rather
than using this repository as a whole), copy this directory together with `../references/`
and `../scripts/` from the repository root, so the relative links above keep resolving — see
the root [`README.md`](../README.md) Install section.
