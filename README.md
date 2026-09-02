# skill-governance-oss

A governance spec plus three linters for **collections** of Claude Skills — one skill needs no
framework, twenty skills sharing state, credentials and trigger space do.

On a real 116-skill collection, the linters found:

| | FAIL | WARN |
|---|---|---|
| `validate_registry.py` — state ownership | **37** | 0 |
| `lint_dependencies.py` — inheritance contracts | 0 | **10** |
| `audit_triggers.py` — trigger-phrase collisions | 0 | **12** |

Full writeup, with three defects shown in full and how each linter caught them: [CASE.md](CASE.md).

This repository's own skills (everything except `examples/collection/`, which is deliberately
broken — see below) run `0 FAIL / 0 WARN` on all three linters. `examples/collection/` is not
excluded automatically; either lint it separately or copy the repo elsewhere without that
directory before running `--skills .` at the root, or `FAIL` from the examples will show up
mixed in with a clean repo, which is expected — that mix *is* the point of shipping them.

## Run it

No install step — clone and run against your own skills directory.

```bash
python3 scripts/audit_triggers.py     --skills ~/.claude/skills
python3 scripts/lint_dependencies.py  --skills ~/.claude/skills
python3 scripts/validate_registry.py  --skills ~/.claude/skills --registry ~/my-registry.md
```

Python 3.8+, standard library only. `FAIL` blocks, `WARN` informs. Expect the first run on an
existing collection to be ugly — every `FAIL` is a defect that was already there, silently. Copy
`references/state-registry.template.md` to start your own (private, never-committed) registry.

To install the framework itself as a live skill in your own collection (so it actually loads
per `ENFORCEMENT.md`), copy `skill-creator-framework/`, `references/` and `scripts/` from this
repository root into your skills directory, keeping them siblings so the relative links inside
`skill-creator-framework/SKILL.md` resolve.

## What these catch that nothing else does

Two defect classes live **between** files, not inside any one of them — which means no linter
scoped to a single `SKILL.md`, and no human reviewing one skill at a time, will ever find them:

- **Semantic overlap between trigger descriptions.** Two skills can each read as perfectly
  reasonable on their own and still claim the same phrase, so neither fires reliably and the
  model picks by coin-flip. `audit_triggers.py` compares descriptions *across the whole
  collection* — the comparison a per-file linter cannot express by definition.
- **Ownership of persistent state.** A database, a folder, a channel identity, a credential —
  each needs exactly one owning skill. `validate_registry.py` diffs every skill's declared
  `## Encapsulation` block against a separate registry file and reports orphans, unregistered
  owners, and two skills claiming the same state. No frontmatter schema or markdown linter has
  a notion of "the same state, described in two different files."

The governing document behind both checks — the OOP model, inheritance rules, credential threat
model, lifecycle — is [SPEC.md](SPEC.md).

## What's in here

```
SPEC.md                    the governing document
references/                trigger-policy, lifecycle, gotchas, registry template
scripts/                   the three linters + shared parser + enforcement installer
ENFORCEMENT.md             five layers that make the framework load on every skill change
examples/collection/       skills deliberately broken so the linters FAIL on them
CASE.md                    the real 116-skill run in full
skill-creator-framework/   thin pointer skill so `Inherits from:`/`Depends on:` resolve (see SPEC.md)
skill-creator-pack/        pack a skill (or set of skills) for distribution
skill-creator-set/         bundle several skills into one shareable archive
skill-creator-set-unpack/  install a bundle into a target collection
skill-translator/          translate a skill's trigger language without breaking triggering
skill-rosetta/             cross-reference terminology across a multilingual collection
skill-doc-framework/       authoring conventions for reference docs skills read on demand
cc-prompt-writer/          generate Claude Code prompts/configs (CLAUDE.md, subagents, tasks)
cc-remote-agent/           base contract for delegating headless work to a remote node
mcp-builder/               build new MCP servers (Anthropic's guide, unmodified)
cowork-agents/             patterns for fanning work out to subagents within one session
```

## License

MIT — see [LICENSE](LICENSE). No roadmap, no support promise: this is a snapshot of a working
setup, published because the case study seemed worth more than another private gist.

Українською: [README.uk.md](README.uk.md).
