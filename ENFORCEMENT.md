# Enforcement — making the framework load on every skill change

A skill cannot force its own invocation. Nothing in the platform guarantees a given skill
fires. So enforcement is **layered**: four soft layers that raise the probability toward
certainty, and one hard layer that actually blocks bad output.

Install all five. Skipping the hard layer means you have a convention, not a contract.

| Layer | Mechanism | Strength | Covers |
|---|---|---|---|
| 1 | Pushy description | soft | user asks for skill work directly |
| 2 | Step 0 in every meta-skill | strong | skill work reached through another skill |
| 3 | `CLAUDE.md` project/global rule | strong | Claude Code sessions |
| 4 | Personal instructions line | soft | chat and app runtimes |
| 5 | Git pre-commit hook | **hard** | everything that reaches the repo |

---

## Layer 1 — description (already shipped)

The `description:` in `SKILL.md` covers create / edit / refactor / rename / split / merge /
deprecate / audit, in both languages, plus the explicit instruction to trigger whenever a
file named `SKILL.md` is about to be written. It over-triggers deliberately.

Nothing to do. Verify with:

```bash
python3 scripts/audit_triggers.py --skills ~/.claude/skills
```

---

## Layer 2 — Step 0 in every meta-skill

Any skill that produces or edits skills must read this framework first. Insert this block
immediately after the frontmatter of each meta-skill:

```markdown
## Step 0 — MANDATORY

Read `/mnt/skills/user/skill-creator-framework/SKILL.md` in full before doing anything
else in this skill. It governs naming, encapsulation, dependencies, trigger space and
lifecycle. Do not skip it for "small" edits — a description tweak changes the shared trigger
namespace and is exactly the change that breaks a collection silently.

After finishing, run all three lint scripts and report the results:
`validate_registry.py`, `lint_dependencies.py`, `audit_triggers.py`.
```

Targets: `skill-creator`, `skill-rosetta`, `skill-doc-framework`, `skill-translator`,
`skills-sync`, `cowork-prompt`, `cc-prompt-writer`.

`scripts/install_enforcement.sh` does this idempotently.

---

## Layer 3 — CLAUDE.md

Add to `~/.claude/CLAUDE.md` (global) and to your skills repo's own `CLAUDE.md`:

```markdown
## Skill authoring — hard rule

Before creating, editing, renaming, splitting, merging, deprecating or deleting ANY
`SKILL.md`, read `skill-creator-framework/SKILL.md` first, in this session. This
includes single-line description edits and adding one trigger phrase.

Before considering any skill change finished, run:
  python3 <framework>/scripts/validate_registry.py --skills ~/.claude/skills --registry <registry.md>
  python3 <framework>/scripts/lint_dependencies.py --skills ~/.claude/skills
  python3 <framework>/scripts/audit_triggers.py  --skills ~/.claude/skills
Report failures. Do not commit a skill change with outstanding FAIL lines.
```

---

## Layer 4 — personal instructions

One line, in the settings profile used by chat and app runtimes:

```
Skill work (creating/editing any SKILL.md) always starts by reading
skill-creator-framework and ends by running its three lint scripts.
```

Weakest layer — instructions compete with everything else in the profile — but it is free and
it covers the runtimes where no filesystem hook exists.

---

## Layer 5 — pre-commit hook (the one that actually holds)

Layers 1–4 raise probability. This one blocks. Installed into whichever repo holds the skills
— a dedicated backup repo, or the same repo your agent config lives in.

The hook fires only when a commit touches a `SKILL.md`, runs all three linters, and rejects
the commit on any `FAIL`. Warnings pass.

Installed by `scripts/install_enforcement.sh --repo <path>`. Bypass with `git commit
--no-verify` when you genuinely need to land a known-broken state — and then fix it in the
next commit, not the next month.

---

## Verifying enforcement is live

```bash
# layer 2
grep -L "skill-creator-framework" ~/.claude/skills/{skill-creator,skill-rosetta,\
skill-doc-framework,skill-translator,skills-sync,cowork-prompt,cc-prompt-writer}/SKILL.md

# layer 3
grep -c "skill-creator-framework" ~/.claude/CLAUDE.md

# layer 5
test -x <repo>/.git/hooks/pre-commit && echo "hook installed"
```

Empty output from the first command means every meta-skill is wired.

---

## Upgrading in place from framework v1

This package keeps the name `skill-creator-framework`, so it is a **drop-in replacement**, not
a migration. Every existing `Depends on: skill-creator-framework`, every `/skill-creator-framework`
invocation and every muscle-memory reference keeps resolving. No deprecation stub is needed,
and no rename sweep (`references/lifecycle.md` §3) applies.

Two things do change and must be handled by hand:

1. **The registry moved out.** v1 carried infrastructure IDs inline. They now live in a
   separate private registry file (`references/state-registry.template.md` is the shape).
   Point `validate_registry.py --registry` at it, and never merge it back into the skill —
   that is what made v1 unshippable.

2. **`## Encapsulation` is now enforced.** Skills that own state but never declared it will
   fail `validate_registry.py` on the first run. That is not a regression; it is the defect
   becoming visible. Work the list down rather than silencing the check.

Back up the old file before overwriting:

```bash
cp -r ~/.claude/skills/skill-creator-framework ~/skill-creator-framework.v1.bak
```
