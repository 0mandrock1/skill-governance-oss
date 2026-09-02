# State Registry — examples/collection (deliberately broken)

## Filesystem / CDN state

| Location | Owner skill | Public ops | Public URL pattern | Verified |
|---|---|---|---|---|
| `shared-cache` | duplicate-owner-a | `duplicate_owner_a.get/set` | — | 2026-08-01 |
| `shared-cache` | duplicate-owner-b | `duplicate_owner_b.get/set` | — | 2026-08-01 |
| `mystery-store` | TBD | — | — | — |

## Database store

| Database | Owner skill | Public ops | ID (debug only) | Verified |
|---|---|---|---|---|
| `ghost-db` | ghost-owner-skill | `ghost.query` | — | 2026-08-01 |

Notes: `orphan-state-owner` intentionally has no row anywhere in this file — that omission
*is* the defect `validate_registry.py` reports for it. `shared-cache` has two rows on purpose
(duplicate ownership). `mystery-store` is an orphan row (`owner: TBD`). `ghost-db` names an
owner skill, `ghost-owner-skill`, that was never authored in this example collection.
