---
name: dangling-dependency
description: >
  Example skill for skill-governance-oss. Depends on a skill that was never authored — the
  dangling-reference defect `lint_dependencies.py` exists to catch. Trigger on:
  "dangling dependency example".
---

# dangling-dependency

Depends on: nonexistent-upstream-service
Uses operations: nonexistent-upstream-service.fetch_records()

This skill claims to read state from `nonexistent-upstream-service`, which does not exist
anywhere in this collection.
