# Case study: running the framework against a real collection

This is a real run, on 2026-09-02, against the private collection the framework was extracted
from — 116 skills discovered under one `user/` directory, accumulated over roughly a year of
daily use across two machines and two runtimes (a CLI agent and an app runtime with connectors).
Domain skill names below are anonymized per the redaction rules in this repo's own governance;
meta-skills (the ones that manage other skills) keep their real names, since those ship in this
repo anyway.

## The numbers

| Linter | FAIL | WARN | What it checks |
|---|---|---|---|
| `validate_registry.py` | **37** | 0 | every unit of owned state has exactly one registered owner |
| `lint_dependencies.py` | 0 | **10** | `Inherits from:` contracts are actually honoured |
| `audit_triggers.py` | 0 | **12** | trigger phrases don't collide across descriptions |

`validate_registry.py` was run against `references/state-registry.template.md` itself — the
blank template, not a filled-in registry. That is not a rigged demo; it is the first honest
finding of this case study: **the registry had never actually been filled in**, eleven months
after the ownership convention (`## Encapsulation`) was adopted. Every skill that declares
`## Encapsulation` and appears in zero registry rows is therefore a real, unregistered owner of
real, live state — not a hypothetical. Point `--registry` at your own filled-in file and the
FAIL count reports genuine drift instead; on a collection with a maintained registry, expect
this number to trend toward zero. Here it did not, because the file was never started.

## Three defects, in full

### 1 — `validate_registry.py`: unregistered state, two skills, one plausible collision

```
FAIL  skill 'personal-db' declares `## Encapsulation` but owns nothing in the registry — unregistered state
FAIL  skill 'channel-poster-personal' declares `## Encapsulation` but owns nothing in the registry — unregistered state
```

(Real names in the source collection; anonymized here as required by this repo's own
redaction rules for domain skills — see the note at the top of this file.)

`personal-db` owns a Postgres schema — the actual `## Encapsulation → Owns` line names a
specific database, schema and connection file. `channel-poster-personal` owns a specific
Telegram channel identity and its credentials-doc section. Both are exactly the kind of state
this framework's §4 exists to track: a live resource, one skill wide, with a
credential-bearing connection string or bot token behind it.

Neither appears in a single registry row. That means: nothing currently stops a second skill
from being authored tomorrow that also queries that Postgres schema directly, or posts to that
same channel with a second bot identity — the collision this whole framework is written to
prevent, sitting undetected in a year-old collection until a static linter actually enumerated
`## Encapsulation` blocks against a registry and found the empty set. A per-file linter (a
markdown linter, a frontmatter schema checker) cannot find this class of defect by
construction — it has no notion of "the same state, described in two different files."

### 2 — `audit_triggers.py`: a homoglyph in a trigger-adjacent word

```
WARN  make-getting-started: mixed-script word 'verifikації' — likely a homoglyph typo
```

`verifikації` mixes a Latin `k` into what should be an all-Cyrillic Ukrainian word. It renders
identically to the correct spelling in nearly every font and editor — this is not a typo a
human proofreading the file would catch by eye. It sits in body prose, not a quoted trigger
phrase, so it does not silently break triggering today — but the same failure mode, one
character over in a `NOT trigger:` line or a quoted phrase, produces a phrase that looks
present but matches nothing, and a collision the linter can no longer see because the string
comparison it depends on now fails on a byte level nobody can read. `audit_triggers.py` flags
every mixed-script word in every description and body it scans; this is the kind of defect that
only a script checking codepoints, not eyeballs, will ever find.

### 3 — `lint_dependencies.py`: inheritance declared, Step 0 not honoured

```
WARN  device-guide-audio: no explicit Step 0 read of parent device-guide
WARN  device-guide-camera: no explicit Step 0 read of parent device-guide
WARN  device-guide-embedded: no explicit Step 0 read of parent device-guide
WARN  device-guide-printer: no explicit Step 0 read of parent device-guide
```

Four device-family instances declare `Inherits from: device-guide` (§5.2) — they share the
parent's 17-section schema and its full/lean split — but none carries the mandatory
"Step 0: read the parent's SKILL.md before doing anything else" instruction the framework
requires of every child. In practice this means each instance's *actual* behaviour depends on
whatever the model reconstructs about the parent contract from the child's own text alone,
which drifts from the parent silently as either file is edited — exactly the failure mode §5.2
names inheritance is not free to prevent. The fix is mechanical (insert the Step 0 block, as
`ENFORCEMENT.md` layer 2 does for meta-skills) but nothing had been checking for its absence
until this linter existed.

## What per-skill review would have missed

All three defects above are invisible to a linter — or a human reviewer — scoped to one
`SKILL.md` at a time. Defect 1 requires comparing `## Encapsulation` blocks *across* every
file in the collection against a separate registry. Defect 3 requires comparing a child's body
against its declared parent's body. Neither comparison is expressible as a rule about one
file's frontmatter or prose; both are only visible once the whole collection is the unit of
analysis. That is this framework's actual claim: not that single-skill quality does not
matter (it does — see Prior Art in `SPEC.md`), but that a second, disjoint class of defect
exists only *between* files, and nothing else in the current tooling ecosystem looks there.
