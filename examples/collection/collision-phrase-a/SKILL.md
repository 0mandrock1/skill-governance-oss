---
name: collision-phrase-a
description: >
  Example skill for skill-governance-oss. Trigger on: "export my data", "collision phrase
  example a". NOT trigger: nothing — this is a deliberately broken example.
---

# collision-phrase-a

Demonstrates a trigger-phrase collision: `collision-phrase-b` quotes the exact same phrase,
`"export my data"`, in its own description. `audit_triggers.py` reports any phrase claimed by
more than one skill.
