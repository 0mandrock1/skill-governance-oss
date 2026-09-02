---
name: orphan-state-owner
description: >
  Example skill for skill-governance-oss. Owns a piece of persistent state but was never
  added to the collection's registry — the exact defect `validate_registry.py` exists to
  catch. Trigger on: "orphan state owner example".
---

# orphan-state-owner

Demonstrates unregistered ownership: this skill owns real state (below) and nobody wrote it
into `registry.md`.

## Encapsulation

### Owns
A local cache directory of fetched pages.

### Public Interface (Inter-Skill API)
- `orphan_state_owner.fetch(url) → cached_path`
- `orphan_state_owner.evict(url) → bool`

### Internal (do not call from outside)
- _cache key hashing, eviction policy_
