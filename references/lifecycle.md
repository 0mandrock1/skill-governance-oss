# Skill Lifecycle

Read when installing, renaming, splitting, merging, deprecating or retiring a skill.

## Contents
1. States
2. Install
3. Rename
4. Split
5. Merge
6. Deprecate
7. Retire
8. Versioning

---

## 1. States

```
draft ──► tested ──► installed ──► registered ──► maintained ──► deprecated ──► retired
                                        │
                                        └──► renamed / split / merged (stays installed)
```

A skill is **not installed** until it is registered. An unregistered skill owning state is the
single most common way a collection acquires an orphan.

---

## 2. Install

1. Draft in a scratch/output directory. Never author directly in the live collection —
   half-written skills in the live tree trigger.
2. Run the three lint scripts.
3. Run the test prompts (framework §8).
4. Copy into the collection.
5. **Same change**: add every owned state row to the registry, with today's date in Verified.
6. **Same change**: commit to whatever backup/sync mechanism the collection uses. A skill that
   exists only on one machine is a skill you will lose.

---

## 3. Rename

A rename touches five places. Missing any one produces a silent dangling reference.

- [ ] Directory name
- [ ] `name:` in frontmatter
- [ ] Trigger phrases containing the old name and the old slash command
- [ ] Every `Inherits from:` / `Depends on:` / `Owner skill` reference in other skills
- [ ] Registry rows

Keep the old name in the description as an alias for one cycle: `also known as {old-name}`.
Users and habits outlive renames.

Then: `lint_dependencies.py` and `validate_registry.py` must both come back clean.

---

## 4. Split

Split when a skill has two jobs (framework §10.6) or its body exceeds the body budget with no
natural reference-file boundary.

1. Decide which half keeps the name. The half that keeps the **state** normally keeps the name.
2. The new half declares `Depends on:` the old one, or `Inherits from:` if the shared surface
   is a contract.
3. Split the trigger space explicitly — both descriptions get NOT-triggers naming the other.
4. Registry: ownership stays with exactly one half. Never leave both listed.
5. Test the split with prompts that previously hit the single skill; every one must land
   deterministically.

---

## 5. Merge

Merge when two skills fight for the same triggers and the decision table says they do the
same thing.

1. Pick the survivor — better name, more dependents, more state.
2. Move the loser's unique capability into the survivor.
3. Transfer state ownership in the registry **before** deleting anything.
4. Patch every `Depends on:` pointing at the loser.
5. Deprecate the loser (§6) for one cycle, then retire it (§7). Do not delete it the same day.

---

## 6. Deprecate

Deprecation is a signal, not a removal. The skill keeps working.

- First sentence of the description becomes: `DEPRECATED — use {successor} instead.`
- Keep the body functional. A deprecated skill that errors is worse than one that works.
- Add a `## Deprecation` section: successor, reason, planned retirement date.
- Leave registry rows intact, marked deprecated. State does not disappear because the skill
  is out of favour.

---

## 7. Retire

Preconditions — all four, no exceptions:

1. State reassigned to another owner, or archived and the row removed from the registry.
2. Every consumer declaring `Depends on:` this skill has been patched.
3. `lint_dependencies.py` clean with the skill removed.
4. Deprecation period elapsed.

Then remove the directory and record the removal in the registry changelog. A retirement that
leaves an orphan is not a retirement, it is a leak.

---

## 8. Versioning

`version:` in frontmatter, semver-flavoured:

| Bump | When |
|---|---|
| Major | Public interface changed or removed; state schema changed incompatibly |
| Minor | New operation, new trigger, new capability; backward compatible |
| Patch | Wording, bug fix, gotcha added, no interface change |

The framework itself is versioned the same way. A collection whose skills were written against
three different framework majors is a collection that no longer has a contract — treat a
framework major bump as a scheduled migration, not an announcement.
