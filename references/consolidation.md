# Consolidation — worked examples

Read when deciding whether a second skill should become an instance of a shared behavioural
parent (framework §6, rule 6), or when writing the `Inherits from:`/`Overrides:`/`Reuses
verbatim:` block for a new instance.

Four real consolidations from the collection this framework was extracted from, in the order
they happened, with domain names anonymized per this repo's own redaction rules (see `CASE.md`)
— the structural lessons (version-bump sizing, failed-attempt causes) are real; the skill
names are illustrative stand-ins for the actual private skills.

Shown in the order they happened, spanning the full range from "pure formalization, no
behaviour change" to "real structural merge of three divergent implementations."

## 1. `deferred-action` ← its instances

**Shape:** a generic one-shot deferred-action contract (arm a timer, fire once, self-disable,
notify) with multiple domain instances scheduling different things through the same
mechanism — e.g. a license-renewal notice and a backup-verify ping, each a thin instance
naming only what to fire and when.

**Version bump:** minor on the parent when a new instance is added without changing the
shared contract; the parent only bumps major if the shared timer/fire/notify contract itself
changes shape.

## 2. `lesson-authoring` + 2 slim instances

**Shape:** a lesson-authoring parent plus two instances that are mostly thin — they add a
narrow domain vocabulary and a slightly different output target, reusing the parent's
pipeline, section schema and output conventions verbatim.

**Lesson:** when an instance's `Overrides:` list is short and its `Reuses verbatim:` list is
long, that is a sign the parent is well-designed, not that the instance is trivial.

## 3. `label-render` ← two card-generator instances

**Shape:** a real structural merge. Two skills independently implemented overlapping render
logic (print-label sizing, device-scale-factor handling, image export) before being
consolidated: `label-render` became the parent owning the shared render contract, with both
card-generator skills reparented as instances.

**Version bump:** major on the parent — the render contract was genuinely consolidated from
divergent implementations into one, not merely formalized.

**Failed-attempt lessons preserved from this merge:**
- Step 0 ("read the parent") must contain an explicit English `read`/`view`/`open` verb next
  to the parent's name — a non-English-only instruction with no English verb nearby does not
  match `lint_dependencies.py`'s detector and produces a false WARN.
- Watch for homoglyph typos at heredoc line-wrap boundaries (a newline glued onto a word) —
  `audit_triggers.py` flags these as mixed-script WARNs; they are usually an authoring
  artifact, not a real trigger-space problem, but check before dismissing one.

## 4. `blog-publisher` ← `blog-updater`

**Shape:** the lightest case — the child skill was already implemented correctly against the
parent's contract; the merge was pure formalization. The parent gained an `## Instances`
table; the child gained an explicit `Inherits from:`/`Overrides:`/`Reuses verbatim:` block and
a Step 0 read instruction. No render/behaviour logic moved.

**Version bump:** minor on both — nothing about runtime behaviour changed, only the contract
became explicit.

**Failed-attempt lesson:** the first draft of the child declared two `Inherits from:` targets
(the real parent, plus a transitive grandparent reached through it) — `lint_dependencies.py`
FAIL, "2 behavioural parents". Rule: exactly one `Inherits from:` target; a parent's own
transitive dependency is never re-declared by the child.

## How to read these four together

The version-bump size tracks how much render/behaviour logic actually moved, not how many
files changed:

| Case | What moved | Bump |
|---|---|---|
| label-render | two divergent render implementations → one | major |
| deferred-action | new instance, contract unchanged | minor (parent) |
| lesson-authoring | thin instance, mostly reuse | minor (parent) |
| blog-publisher | zero — pure formalization of an already-correct instance | minor (both) |

See also `references/trigger-policy.md` for the merge/no-merge decision table these four were
each run through before consolidating.
