#!/usr/bin/env bash
# Install framework enforcement layers 2 and 5.
#
#   ./install_enforcement.sh --skills ~/.claude/skills [--repo ~/claude-config] \
#                            [--registry ~/my-registry.md] [--dry-run]
#
# Layer 2: inject a mandatory Step 0 block into every meta-skill (idempotent).
# Layer 5: install a pre-commit hook that blocks commits touching a SKILL.md when any
#          linter reports FAIL.
set -euo pipefail

FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRAMEWORK_NAME="skill-creator-framework"
SKILLS=""; REPO=""; REGISTRY=""; DRY=0
MARKER="<!-- ${FRAMEWORK_NAME}:step0 -->"

META_SKILLS=(skill-creator skill-rosetta skill-doc-framework skill-translator
             skills-sync cowork-prompt cc-prompt-writer)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skills)   SKILLS="$2"; shift 2 ;;
    --repo)     REPO="$2"; shift 2 ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    --dry-run)  DRY=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$SKILLS" ]] || { echo "--skills is required" >&2; exit 2; }
[[ -d "$SKILLS" ]] || { echo "no such directory: $SKILLS" >&2; exit 2; }

step0_block() {
  cat <<BLOCK

${MARKER}
## Step 0 — MANDATORY

Read \`${SKILLS}/${FRAMEWORK_NAME}/SKILL.md\` in full before doing anything else in this
skill. It governs naming, encapsulation, dependencies, trigger space and lifecycle. Do not
skip it for "small" edits — a description tweak changes the shared trigger namespace and is
exactly the change that breaks a collection silently.

Before reporting the work finished, run all three lint scripts from
\`${SKILLS}/${FRAMEWORK_NAME}/scripts/\` and report the results.
BLOCK
}

echo "== Layer 2: Step 0 injection =="
for skill in "${META_SKILLS[@]}"; do
  file="${SKILLS}/${skill}/SKILL.md"
  if [[ ! -f "$file" ]]; then
    echo "  skip   ${skill} (not installed)"
    continue
  fi
  if grep -qF "$MARKER" "$file"; then
    echo "  ok     ${skill} (already wired)"
    continue
  fi
  if [[ $DRY -eq 1 ]]; then
    echo "  would  ${skill}"
    continue
  fi
  # Insert after the closing --- of the frontmatter (line 2 onwards).
  end=$(awk 'NR>1 && /^---[[:space:]]*$/ {print NR; exit}' "$file")
  if [[ -z "$end" ]]; then
    echo "  FAIL   ${skill}: no frontmatter terminator found" >&2
    continue
  fi
  tmp="$(mktemp)"
  head -n "$end" "$file" > "$tmp"
  step0_block >> "$tmp"
  tail -n +"$((end + 1))" "$file" >> "$tmp"
  cp "$file" "${file}.bak"
  mv "$tmp" "$file"
  echo "  wired  ${skill} (backup at ${skill}/SKILL.md.bak)"
done

if [[ -z "$REPO" ]]; then
  echo
  echo "== Layer 5: skipped (no --repo given) =="
  echo "Enforcement is soft-only. Re-run with --repo <path-to-git-repo> to install the hook."
  exit 0
fi

echo
echo "== Layer 5: pre-commit hook =="
HOOK_DIR="${REPO}/.git/hooks"
[[ -d "$HOOK_DIR" ]] || { echo "not a git repo: $REPO" >&2; exit 2; }
HOOK="${HOOK_DIR}/pre-commit"

if [[ -f "$HOOK" ]] && ! grep -qF "$FRAMEWORK_NAME" "$HOOK"; then
  echo "  existing pre-commit hook found and it is not ours."
  echo "  refusing to overwrite. Merge manually, or move it aside and re-run."
  exit 2
fi

if [[ $DRY -eq 1 ]]; then
  echo "  would install ${HOOK}"
  exit 0
fi

cat > "$HOOK" <<HOOKEOF
#!/usr/bin/env bash
# ${FRAMEWORK_NAME} pre-commit gate
set -uo pipefail

staged="\$(git diff --cached --name-only)"

# Hard block: the private state registry must never be committed.
if echo "\$staged" | grep -Eq '(^|/)(state-registry|my-registry)\.md$'; then
  echo "commit blocked: the private state registry is staged."
  echo "unstage it:  git rm --cached <path>"
  echo "it is git-ignored by design; see scripts/registry_guard.sh"
  exit 1
fi

if ! echo "\$staged" | grep -q 'SKILL\.md$'; then
  exit 0
fi

FW="${FRAMEWORK_DIR}"
SKILLS="${SKILLS}"
REGISTRY="${REGISTRY}"
fail=0

run() {
  echo "--- \$1"
  out="\$(python3 "\$@" 2>&1)" || true
  echo "\$out" | grep -E '^\s+(FAIL|WARN)' || true
  if echo "\$out" | grep -q '  FAIL '; then fail=1; fi
}

run "\$FW/scripts/audit_triggers.py"  --skills "\$SKILLS"
run "\$FW/scripts/lint_dependencies.py" --skills "\$SKILLS"
if [[ -n "\$REGISTRY" && -f "\$REGISTRY" ]]; then
  run "\$FW/scripts/validate_registry.py" --skills "\$SKILLS" --registry "\$REGISTRY"
else
  echo "--- validate_registry.py skipped (no registry configured)"
fi

if [[ \$fail -ne 0 ]]; then
  echo
  echo "commit blocked: skill framework lint reported FAIL."
  echo "fix the failures, or bypass deliberately with: git commit --no-verify"
  exit 1
fi
exit 0
HOOKEOF

chmod +x "$HOOK"
echo "  installed ${HOOK}"
echo
echo "Done. Layers 3 and 4 are manual — see ENFORCEMENT.md."
