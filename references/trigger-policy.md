# Trigger-Collision Policy

Read when naming triggers, resolving an overlap, or splitting a skill family.

## Contents
1. Why this is the dominant failure mode
2. Decision table
3. The four collision shapes
4. NOT-trigger syntax
5. Reserved-word skills
6. Multilingual trigger space
7. Review procedure

---

## 1. Why this is the dominant failure mode

Description metadata for every installed skill sits in context simultaneously. Selection is a
judgement call made against that whole set. Two skills claiming the same phrase does not
produce an error — it produces a coin flip, and the coin flip is invisible because both
outcomes look plausible in isolation.

This gets worse superlinearly. At 5 skills the space is empty; at 50 nearly every new skill
lands next to a neighbour. Collision review is therefore not optional past the first dozen.

---

## 2. Decision table

| Situation | Action |
|---|---|
| New skill's phrases overlap an existing skill's | Narrow the new one **and** add NOT-triggers to both |
| Two skills do the same thing to different destinations | Disambiguate on destination, in both descriptions |
| Two skills do the same thing at different depth | Disambiguate on depth with explicit thresholds, not adjectives |
| Two skills genuinely do the same thing | Merge. Keep the better name, deprecate the other |
| A skill fires when it should not | Add a NOT-trigger before touching positive triggers |
| A skill fails to fire | Add phrases; only then consider weakening a neighbour's claim |
| Output is expensive, public or destructive | Convert to reserved-word triggering (§5) |
| Overlap is only in one language | Fix in that language; do not translate the fix into the others blindly |

---

## 3. The four collision shapes

**Synonym collision.** Two skills claim phrases meaning the same thing (`save to X` vs
`store in X`). Almost always a sign the skills should merge or one should become the other's
public interface.

**Family collision.** `x`, `x-lite`, `x-pro` all claim the bare `x`. Fix: the bare term
belongs to exactly one member — normally the most-used, not the most general — and every
member names the others.

**Verb-noun collision.** One skill claims the verb (`publish …`), another the noun
(`… article`). The phrase `publish article` belongs to neither cleanly. Fix: whichever skill
owns the *destination* wins; the other adds a NOT-trigger.

**Escalation collision.** A cheap skill and an expensive skill cover the same intent at
different cost (inline answer vs full background job). The cheap one owns the trigger; the
expensive one triggers only on explicit escalation language or a slash command.

---

## 4. NOT-trigger syntax

Put it at the end of the description, after the positive triggers:

```
NOT trigger: <specific case> — use {other-skill}. <second case> — use {another-skill}.
```

Requirements:
- Name the alternative skill. "Do not use for other things" is worthless.
- Describe the case concretely enough to be matched against a real prompt.
- Add a NOT-trigger to the **neighbour** too. One-sided fixes shift the coin flip rather than
  removing it.

---

## 5. Reserved-word skills

A skill triggers on a unique token only when a false positive is costly: posting publicly,
spending money, sending to another person, printing, deleting, running a long background job.

Pattern:

```
Trigger EXCLUSIVELY on the literal word "{token}" or "/{token}", written by the user.
Do NOT trigger on any paraphrase, related noun, or adjacent request — the general words
"{word1}", "{word2}" do NOT activate this skill. When another skill wants this output,
it must still be the user who says "{token}".
```

State it in the strongest terms the description allows, and repeat the prohibition — a single
soft "prefer not to" will be overridden by a plausible-looking request.

---

## 6. Multilingual trigger space

A multilingual collection has *n* trigger spaces that collide independently. A phrase can be
unique in English and contested in another language, and the audit only catches it if the
phrases are actually written out in the description.

Rules:
- Write triggers in every language the collection is used in. Do not rely on translation at
  selection time.
- Include the informal register, not just the dictionary form — real prompts are short,
  contextless and often mixed-language.
- Run the trigger audit per language, not on the merged set.

---

## 7. Review procedure

1. Run `scripts/audit_triggers.py --skills {root}`.
2. For every reported pair, apply the decision table (§2).
3. Patch **both** descriptions.
4. Re-run until clean.
5. Test: 3 prompts that must hit the new skill, 3 that must hit the neighbour. If any lands
   on the wrong side, the descriptions are still ambiguous — the coin flip has not been
   removed, only tilted.
