---
name: duplicate-owner-a
description: >
  Example skill for skill-governance-oss. Registered in `registry.md` as the owner of
  "shared-cache" — the same state a second skill also claims. Trigger on:
  "duplicate owner example a".
---

# duplicate-owner-a

## Encapsulation

### Owns
The `shared-cache` store (see `registry.md` in this directory).

### Public Interface (Inter-Skill API)
- `duplicate_owner_a.get(key) → value`
- `duplicate_owner_a.set(key, value) → bool`

### Internal (do not call from outside)
- _backend connection details_
