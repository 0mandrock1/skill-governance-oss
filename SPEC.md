# Skill Framework — OOP Model for Skill Collections

Governing document for a **collection** of Claude Skills that must stay coherent as it grows
past the point where one person can hold it in their head.

A single skill needs no framework. Twenty skills sharing state, credentials and trigger space
do. This document is the contract that keeps them from colliding, and `scripts/` are the
linters that prove the contract holds.

**Read order for any skill work:** this file → `references/` as needed → your own
registry file (see §5) → then write.

---

## 0. Non-negotiables

Before writing or editing a SKILL.md, all four must be true:

1. You have read this file **in this session**.
2. You have checked the trigger space (§6) for collisions with existing skills.
3. If the skill owns persistent state, it has an `## Encapsulation` section (§4).
4. If the skill reads another skill's state, it declares `Depends on:` (§5).

If any is false, stop and fix before writing.

---

## 1. OOP Model

Skills are modelled as classes. This is the whole conceptual load of the framework.

| OOP | Here |
|---|---|
| Class | Skill — a directory containing `SKILL.md` |
| Instance | One session-scoped invocation |
| Field / state | Anything persistent: databases, folders, files, caches, channels, tables |
| Method | An operation the skill performs, usually via MCP or a script |
| Public interface | Trigger phrases (human-facing) + Inter-Skill API (machine-facing) |
| Private internals | ID resolution, schemas, parsing, fuzzy matching, caching |
| Inheritance | `Inherits from:` + parent SKILL.md read first |
| Encapsulation | One owner per unit of state; everyone else goes through the public interface |
| Polymorphism | Domain instances of one parent (`{parent}-{domain}`) honouring the same contract |

**The one rule that matters:** state has exactly one owner. Everything else follows.

---

## 2. Anatomy and Layout

```
{collection-root}/
├── {parent-skill}/            ← shared base, if any
├── {skill-name}/
│   ├── SKILL.md               ← required
│   ├── references/            ← docs read on demand
│   ├── scripts/                ← deterministic helpers
│   └── assets/                 ← fonts, templates, icons
```

**Frontmatter spec** — `name` and `description` are required; `version` and `compatibility`
optional. Hard limits per the Agent Skills spec: `name` ≤ 64 characters, lowercase with
hyphens, matching the directory name; `description` ≤ 1024 characters. Exceeding either is a
load-time failure, not a style issue. Verify against your platform's current spec if unsure.

**Progressive disclosure** — three levels, and they are a budget, not a suggestion:

| Level | Cost | Contents |
|---|---|---|
| Metadata (name + description) | always in context | triggering only |
| SKILL.md body | on trigger | the workflow, ≤ ~500 lines |
| `references/`, `scripts/` | on demand | everything else, unbounded |

Body over ~500 lines means you skipped a hierarchy level. Split into `references/` with an
explicit pointer telling the reader when to open each one. Reference files over ~300 lines
get a table of contents.

---

## 3. Naming

| Type | Pattern | Example |
|---|---|---|
| Action skill | `{domain}-{action}` | `telegraph-publisher` |
| Domain helper | `{tool}-helper` | `bitwig-project-helper` |
| Docs fetcher | `{tool}-docs` | `ableton-docs` |
| Shared base | `{domain}-helper` or `core` | `purchase-helper`, `core` |
| Runtime variant | `{runtime}-{domain}` | `cowork-blender` |
| Specialization | `{parent}-{specialization}` | `crystalized-article-topic` |

Directory name, `name:` field and every cross-reference must match exactly. A rename is a
three-place edit plus a dependency sweep (§5.4).

---

## 4. Encapsulation

Any skill owning persistent state carries this section verbatim in structure:

```markdown
## Encapsulation

### Owns
<concrete list: which database, which folder, which files, which cache>

### Public Interface (Inter-Skill API)
- `skill.operation_a(args) → return_shape` — one-line description
- `skill.operation_b(args) → return_shape`

### Internal (do not call from outside)
- _ID resolution, schema, status maps, fuzzy matching, caching_
```

**Rules:**

1. **One store, one owner.** Two skills claiming the same database is the defect this
   framework exists to prevent. When it happens, promote one to owner and make the other
   declare `Depends on:`.
2. **Consumers hardcode nothing** — not IDs, not schemas, not status values, not tag formats,
   not state file paths. All of that is the owner's private state.
3. **Calling a public interface** means: read the owner's SKILL.md, find
   `## Encapsulation → Public Interface`, execute the described operation. SKILL.md declares
   the signature; the model is the runtime. There is no type checker — the lint scripts in
   `scripts/` are the closest thing, so run them.
4. **Bootstrap exception.** An owner may create its own state on first run (e.g. create the
   database). This is the only legitimate raw call that writes *structure* rather than
   *items*, and it must be documented in a `## Bootstrap` section inside that skill.
5. **Stateless skills skip this section** entirely. Docs fetchers, explainers, calculators,
   formatters — transparent, nothing to encapsulate.
6. **Deleting an owner orphans its state.** Retirement procedure is in
   `references/lifecycle.md`; never delete an owner without reassigning or archiving.

---

## 5. Inter-Skill API and the Registry

### 5.1 Declaring a dependency

```markdown
Depends on: {owner-skill}
Uses operations: {owner}.op_a(), {owner}.op_b()
```

### 5.2 Declaring inheritance

Inheritance here is **an authoring and linting convention, not a runtime hint to the model.**
A related proposal — a `specializes:` frontmatter field meant to tell the model at inference
time which skill takes precedence over a near neighbour — was raised and withdrawn in the
Agent Skills community (see `agentskills/agentskills#404`): explicit precedence hints measured
*worse* skill selection on frontier models than clear NOT-trigger prose. `Inherits from:` in
this framework exists so a human (or `scripts/lint_dependencies.py`) can trace a contract and
sweep dependents on change — it is never read by the model to break a trigger tie. Trigger
collisions are resolved by NOT-trigger lines (§6), never by declaring one skill "more
specialized" than another.

```markdown
Inherits from: {parent}
Overrides: {what changes}
Reuses verbatim: {what does not}
```

Step 0 of the child's body: read the parent's SKILL.md before doing anything else.

**Multi-parent.** A skill may inherit from at most one *behavioural* parent (the one defining
its workflow shape) and any number of *service* parents (credentials, storage, transport).
Resolution order is: behavioural parent first, then service parents in declaration order; on
conflict the behavioural parent wins and the child must state the override explicitly. If two
behavioural parents genuinely apply, the skill is two skills.

**Inheritance is not free.** Each `Inherits from:` costs a full parent-file read at runtime.
Inherit when the shared surface is a *contract* (credentials, output format, publishing
pipeline). Duplicate when it is a couple of lines of prose.

### 5.3 The State Registry

Every collection keeps one registry file listing every unit of persistent state and its owner.
Template: `references/state-registry.template.md`. Your filled-in registry is a **separate,
private file** — copy the template outside this repository, fill it in, and never commit it;
see `.gitignore` and `scripts/registry_guard.sh`.

The registry holds IDs **for bootstrap and debugging only**. At runtime, consumers reach state
through the owner, never by ID.

Registries rot silently, which makes them worse than useless — a stale registry is trusted.
Two defences, both mandatory:
- `scripts/validate_registry.py` — static consistency (run on every change).
- A live reconciliation pass — enumerate the actual databases/folders via MCP and diff against
  the registry. Schedule it; do not rely on remembering.

### 5.4 Changing a public interface

Changing an owner's public interface is a breaking change to every declared consumer.
Procedure: `scripts/lint_dependencies.py` → patch every consumer it reports → re-run until
clean. Never ship a signature change without the sweep.

---

## 6. Trigger-Collision Policy

Trigger space is a **shared, finite namespace**. Past ~20 skills it is the dominant failure
mode: two skills claiming the same phrase means neither fires reliably, and the model picks
by coin-flip. This is a defect class per-skill linters cannot see by definition — a linter
scoped to one `SKILL.md` has no view of the other 100.

**Rules:**

1. **Every description declares NOT-triggers** once the collection holds a near neighbour:
   `NOT trigger: <case> — use {other-skill} instead.` This is the single highest-value line
   in most descriptions.
2. **A phrase belongs to one skill.** If two want it, one of them is wrong about its scope —
   or they should be merged.
3. **Reserved-word skills.** A skill whose output is disruptive, expensive or noisy (posting
   publicly, spending money, printing, deleting) triggers **only** on an explicit unique
   token or slash command, never on a general phrase. State this in the description in the
   strongest terms available.
4. **Same-family skills** (`x`, `x-lite`, `x-pro`) disambiguate on an explicit axis — output
   destination, depth, runtime — and each names the others in its NOT-trigger line.
5. **Run `scripts/audit_triggers.py` after adding or editing any description.** It reports
   phrases claimed by more than one skill.

Full decision table and worked examples: `references/trigger-policy.md`.

---

## 7. Lifecycle

`draft → test → install → register → maintain → deprecate → retire`

Summary; details in `references/lifecycle.md`.

- **Draft** in an output directory, never directly into the live collection.
- **Test** before install — see §8.
- **Install**, then **register**: add owned state to the registry in the same change.
- **Maintain**: run all three lint scripts after any edit.
- **Deprecate**: description gets `DEPRECATED — use {successor}` as its first sentence; the
  body keeps working. Deprecation is not deletion.
- **Retire**: only after state is reassigned or archived, dependents are patched, and the
  registry row is updated or removed. A retired skill leaves no orphaned state behind.

Version the framework itself and every skill that owns state (`version:` in frontmatter). If
you cannot say which version a consumer was written against, the contract is decorative.

---

## 8. Testing

A skill is untested until it has been triggered by prompts nobody wrote for it.

**Minimum bar for any skill:**
- 3 positive prompts phrased the way a real request arrives — short, contextless, mid-task.
- 3 negative prompts that *should not* fire it, drawn from the nearest neighbours in §6.
- 1 adversarial prompt from a different language or register, if the collection is multilingual.

Negative tests are the ones that catch real defects; positive tests mostly confirm the
description echoes the prompt. Skills with objectively checkable output (transforms,
extraction, code generation, fixed workflows) warrant quantitative evals; subjective ones
(style, voice, art) are judged by reading the output.

Record which prompts were used, in the skill's own `references/` — otherwise the next edit
re-tests from zero.

---

## 9. Credentials — Threat Model

State the model explicitly rather than assuming it.

**Default posture:** secrets live in exactly one store, owned by exactly one skill, loaded
through one documented operation. No other skill reads that store; no skill ever hardcodes a
token; no token is ever echoed into output, logs, artifacts or error messages.

**What this posture does and does not protect against:**

| Threat | Covered |
|---|---|
| Accidental copy-paste of a token into a skill body | ✅ single-source discipline |
| A skill leaking a secret into its output | ✅ only if the no-echo rule is enforced in review |
| A reader of the store obtaining every secret at once | ❌ the store is a single point of compromise |
| Secrets at rest in a plaintext notes app or doc | ❌ readable by anything with that app's scope |
| Exfiltration by a skill installed from an untrusted source | ❌ nothing here prevents it |

Consequences to accept or mitigate: **prefer an environment-variable or secret-manager
backend where the runtime supports it**, and treat a plaintext document store as a
convenience tier for low-value keys only. Whatever backend is chosen, the ownership rule is
unchanged — one owner, one load operation.

Never install a skill from an untrusted source without reading every line of its scripts.

---

## 10. Writing Rules

1. **Imperative voice.** "Read X", "Fetch Y" — not "you should read X".
2. **Description is the trigger.** All when-to-use information lives there, none in the body.
3. **Descriptions are deliberately pushy** — models under-trigger skills. Over-trigger, then
   constrain with NOT-triggers rather than starting timid.
4. **No placeholder code.** Everything shipped must run as written. `# TODO` in a skill is a
   defect.
5. **State the output format** explicitly when it matters — the model will otherwise invent
   a reasonable one, differently each time.
6. **One skill, one job.** A skill that needs "and also" in its summary is two skills.
7. **Gotchas do not belong in the rules list.** Environment-specific landmines (font
   registration, escaping quirks, API endpoints that must not use the obvious library) go in
   `references/gotchas.md` and are cited from the workflow step that needs them. Mixing
   lessons-learned into normative rules makes the norms unreadable.
8. **Principle of lack of surprise.** A skill's behaviour must match its description. No
   hidden network calls, no unrequested writes, no side effects a reader would not predict.

---

## 11. Environment Profile

Every collection depends on facts about its host: which connectors exist, which runtime is in
play, which paths are writable, which model strings are current. These rot fastest of
anything in a skill collection.

**Do not inline them here.** Keep them in your registry file (§5.3) under
`## Environment`, timestamped, with a re-verification cadence. Rule of thumb: connector lists
and model identifiers are stale within a quarter.

When a skill needs an environment fact, it reads the registry — it does not carry its own
copy. Duplicated environment facts diverge, and the divergence is invisible until something
breaks in production.

---

## 12. Runtime Boundaries

Skills run under different runtimes with genuinely different capabilities — a CLI agent with
filesystem and git, an app runtime with connectors and a workspace, a chat runtime with
neither. A skill written for one will fail silently in another, usually by describing an
action it cannot perform and reporting success.

**Rules:**
- Every skill whose workflow depends on runtime capability names its target runtime in the
  first lines of the body.
- Cross-runtime families use the `{runtime}-{domain}` naming pattern and never share a body.
- Keep the capability matrix in your registry file, not here — capabilities change with every
  platform release, and a wrong ❌ in a framework document is worse than no matrix at all.

---

## 13. Checklist

- [ ] Read this file this session
- [ ] Existing skill or parent does not already cover it
- [ ] Name matches §3; directory, `name:` and references agree
- [ ] `description` ≤ 1024 chars, pushy, with NOT-triggers naming the near neighbours
- [ ] `scripts/audit_triggers.py` clean
- [ ] `Inherits from:` / `Overrides:` / `Reuses verbatim:` if it has a parent; Step 0 reads it
- [ ] `## Encapsulation` present **iff** it owns state
- [ ] `Depends on:` + `Uses operations:` for every foreign state it touches; zero hardcoded IDs
- [ ] `scripts/lint_dependencies.py` clean
- [ ] Registry updated in the same change; no new orphans
- [ ] `scripts/validate_registry.py` clean
- [ ] Body ≤ ~500 lines; overflow moved to `references/` with pointers
- [ ] No placeholder code, no hardcoded secrets, no echoed tokens
- [ ] 3 positive + 3 negative test prompts run and recorded
- [ ] `version:` set; changelog line written

---

## 14. Bundled Resources

| File | Read when |
|---|---|
| your private registry (copied from the template, kept outside this repo) | any question of who owns what, which ID, which connector |
| `references/state-registry.template.md` | starting a collection, or restructuring the registry |
| `references/trigger-policy.md` | naming triggers, resolving a collision, splitting a family |
| `references/lifecycle.md` | installing, deprecating, retiring, renaming, splitting, merging |
| `references/gotchas.md` | a workflow step touches PDFs, fonts, note apps, publishing APIs, RNG |
| `scripts/validate_registry.py` | after any registry or ownership change |
| `scripts/lint_dependencies.py` | after any interface, inheritance or dependency change |
| `scripts/audit_triggers.py` | after any description change |
| `ENFORCEMENT.md` | wiring this framework so it loads automatically |
| `scripts/registry_guard.sh` | keeping the private registry out of git (run from cron on your host) |

Run all three scripts together before considering any skill change finished:

```bash
python3 scripts/validate_registry.py --skills {collection-root} --registry {your-registry.md}
python3 scripts/lint_dependencies.py --skills {collection-root}
python3 scripts/audit_triggers.py  --skills {collection-root}
```

---

## Prior Art

This framework is not the first attempt at skill discipline, and does not claim a novel
insight at the single-skill level:

- **Destefanis, "Authoring Agent Skills: A Software-Engineering Approach"** (arXiv 2607.25032,
  2026-07-27) makes the case for SE discipline applied to **one** skill — structure, testing,
  versioning. It ships no repository and no tooling. This framework's scope starts where that
  paper's ends: a **collection** of skills, where the defects are between files, not within
  one — state ownership conflicts, trigger-space collisions, inheritance-contract breakage.
- **smixs/skill-conductor** (MIT) ships the same *form* of solution — a governing document
  plus linters — for a different *content*. Worth reading side by side with this repository;
  neither supersedes the other.
- **obra/superpowers**, skill `writing-skills`, is the best treatment available of what makes
  *one* trigger description good. This framework assumes that quality and asks the next
  question: what happens when twenty good triggers compete for the same phrase.

None of the above addresses semantic overlap between trigger descriptions across a whole
collection, or who owns a given piece of persistent state — the two defect classes this
framework's linters exist to catch.
