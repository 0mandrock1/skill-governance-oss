# Changelog

## 2026-10-08 — 2.3.0: archive state, merge-audit, effect-arm gate, de-instantiation

- SPEC.md §6 (Trigger-Collision Policy): three new rules — merge-audit every singleton skill
  before a second instance ships; "family named after its first member" smell (rename the
  parent before it acquires a second child); fail-closed default on an ambiguous merge/no-merge
  call.
- `references/lifecycle.md`: new `archived` state, distinct from deprecate/retire — no
  successor required, no deprecation period, reversible (move the directory back + regen the
  manifest). For dead-weight skills nobody depends on, not candidates for a deprecation cycle.
- SPEC.md §8 (Testing): effect-arm check (run the task once with the skill available, once
  without, same prompt) and a SkillGLoW-style commit gate —
  `effect(new) ≥ max(effect(current), effect(no-skill)) − ε`. A skill that regresses against
  the no-skill baseline is a blocking defect, not a style note.
- SPEC.md §10 (Writing Rules): rule 9, de-instantiation — a behavioural parent's contract must
  stay runtime-agnostic; instance-shaped detail (a PID, a run-dir, a literal file name, a
  concrete hostname) belongs to the child that has it, never the parent, even with only one
  child today.
- New `scripts/lint_deinstantiation.py`: heuristic WARN-only lint for the rule above — scans
  every parent declaring `## Instances` for leaked instance-shaped tokens outside its own
  Instances table.
- New `references/consolidation.md`: four worked merge examples side by side, with
  version-bump sizing and the failed-attempt lessons each one produced (domain names
  anonymized per this repo's own redaction rule — see `CASE.md`).
- Prior Art: added SkillGLoW (arXiv:2609.02217, CC BY 4.0) as the source for the
  effect-arm/commit-gate and the family-naming smell.
- Removed `skill-creator-set/`, `skill-creator-set-unpack/` and `mcp-builder/` from this repo
  — unused peer skills that had drifted out of the published surface; `skill-creator-pack/`'s
  NOT-trigger line updated to drop the now-dangling reference.

## 2026-09-23 — 2.2.0: de-hardcode

- Meta-skills list moved out of the framework files into the private registry
  (`## Environment → Meta-skills`); `install_enforcement.sh --meta` / `FRAMEWORK_META_SKILLS`,
  default `skill-creator`.
- Pre-commit hook refuses registry file names from `REGISTRY_NAMES` instead of a baked-in name.
- Registry location wording unified: bundled `references/state-registry.md` (git-ignored) or `--registry`.
- Step 0 block points at `{skills-root}`, not a fixed install path.

## 2026-09-02 — initial public extraction

- Extracted `skill-creator-framework` (governing spec, three linters, references,
  enforcement doc) from a private 116-skill collection, generalized all infrastructure
  identifiers into placeholders, and published as `SPEC.md` + `scripts/` + `references/`.
- Added `CASE.md`: a real lint run against the source collection (37 `validate_registry.py`
  FAIL, 10 `lint_dependencies.py` WARN, 12 `audit_triggers.py` WARN), with three defects
  shown in full.
- Added `examples/collection/`: skills deliberately authored to fail each linter, for anyone
  verifying the tooling before pointing it at their own collection.
- Included nine peer skills that use or complement the framework: `skill-creator-pack`,
  `skill-creator-set`, `skill-creator-set-unpack`, `skill-translator`, `skill-rosetta`,
  `skill-doc-framework`, `cc-prompt-writer`, `cc-remote-agent` (base contract only —
  machine-specific instances were not published), `mcp-builder`, `cowork-agents`.
- Framework version at extraction: `2.1.0` (see `SPEC.md` history in the source collection —
  not tracked separately here; this repo starts its own changelog from the extraction point).
