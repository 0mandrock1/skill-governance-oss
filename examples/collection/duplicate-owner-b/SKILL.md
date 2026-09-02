---
name: duplicate-owner-b
description: >
  Example skill for skill-governance-oss. Also registered in `registry.md` as the owner of
  "shared-cache" — the collision `validate_registry.py` exists to catch. Trigger on:
  "duplicate owner example b".
---

# duplicate-owner-b

## Encapsulation

### Owns
The `shared-cache` store — claimed a second time, by design, to demonstrate the defect.

### Public Interface (Inter-Skill API)
- `duplicate_owner_b.get(key) → value`
- `duplicate_owner_b.set(key, value) → bool`

### Internal (do not call from outside)
- _backend connection details_
