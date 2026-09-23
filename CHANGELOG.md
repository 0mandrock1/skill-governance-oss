# Changelog

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
