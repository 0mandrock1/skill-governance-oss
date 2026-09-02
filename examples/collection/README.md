# Broken on purpose

Seven skills, each authored to trip exactly one class of defect the three linters catch. Point
the linters at this directory (not at the repo root — the repo root is meant to pass) and expect
`FAIL`.

```bash
python3 ../../scripts/audit_triggers.py     --skills .
python3 ../../scripts/lint_dependencies.py  --skills .
python3 ../../scripts/validate_registry.py  --skills . --registry registry.md
```

| Skill | Linter | Defect |
|---|---|---|
| `orphan-state-owner` | `validate_registry` | declares `## Encapsulation`, appears in no registry row |
| `duplicate-owner-a` + `duplicate-owner-b` | `validate_registry` | `registry.md` gives the same state to both — two owners, one resource |
| `collision-phrase-a` + `collision-phrase-b` | `audit_triggers` | both quote the exact same trigger phrase |
| `dangling-dependency` | `lint_dependencies` | `Depends on:` names a skill that does not exist |
| `broken-inheritance` | `lint_dependencies` | `Inherits from:` names a skill that does not exist |

`registry.md` also carries an orphan row (`owner: TBD`) and a row naming an owner skill that
was never authored, to show those two `validate_registry` checks as well.
