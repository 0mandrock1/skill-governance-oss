# State Registry — {collection name}

> Copy this file, fill it in, keep it **outside** any shipped/shared skill package.
> It contains infrastructure identifiers and is not distribution material.

Registry version: `0.1.0`
Last full reconciliation: `YYYY-MM-DD`
Reconciliation cadence: every `{N}` weeks (put it in a calendar, not in your head)

---

## How to read this file

- **Owner skill** is the single skill permitted to write this state.
- **Public ops** is the interface other skills call. Names must match the owner's
  `## Encapsulation → Public Interface` exactly.
- **ID** is for bootstrap and debugging only. Runtime access goes through the owner.
- **Orphan** rows are defects. Each one either gets an owner or gets archived.

---

## Document / notes store

| Location | Owner skill | Public ops | ID (debug only) | Verified |
|---|---|---|---|---|
| | | | | |

## Database store

| Database | Owner skill | Public ops | ID (debug only) | Verified |
|---|---|---|---|---|
| | | | | |

> Note the identifier *flavour* your platform's write tools expect (database id vs data
> source id vs collection URI). Getting this wrong produces confusing partial failures.

## Relational / SQL state

| Schema or table group | Owner skill | Public ops | Host | Verified |
|---|---|---|---|---|
| | | | | |

## Filesystem / CDN state

| Path | Owner skill | Public ops | Public URL pattern | Verified |
|---|---|---|---|---|
| | | | | |

## Messaging / channel state

| Channel | Owner skill | Public ops | Visibility | Verified |
|---|---|---|---|---|
| | | | | |

## Repository / sync state

| Repo or submodule | Owner skill | Public ops | Remote | Verified |
|---|---|---|---|---|
| | | | | |

## Credentials

| Store | Owner skill | Load operation | Backend | Verified |
|---|---|---|---|---|
| | | | | |

Threat model: see framework §9. Record here which posture applies and what is explicitly
**not** covered.

---

## Environment

Facts that rot. Re-verify on the cadence above; never duplicate these into a skill body.

### Connectors available

| Connector | Used by | Verified |
|---|---|---|
| | | |

### Runtimes and capabilities

| Capability | {runtime A} | {runtime B} |
|---|---|---|
| Filesystem / git | | |
| Connectors | | |
| Subagents | | |
| Browser automation | | |
| Scheduled / background execution | | |

### Model identifiers used by skills

| Purpose | Model string | Verified |
|---|---|---|
| | | |

### Stack

| Item | Value |
|---|---|
| Languages | |
| OS / paths | |
| Output devices | |
| Language policy | |

---

## Orphans and TBD

| State | Suspected owner | Decision due |
|---|---|---|
| | | |

---

## Changelog

| Date | Change | By |
|---|---|---|
| | | |
