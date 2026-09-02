#!/usr/bin/env bash
# registry_guard.sh — keep the private state registry out of every git remote.
#
# Runs from cron on the VPS. Scans configured roots for git repositories, and for each one
# checks whether the private registry has appeared in the working tree or the index.
#
# Design rule: NEVER destroy the only copy. If a canonical copy exists outside every repo,
# a stray copy inside a repo is deleted. If no canonical copy exists, the stray one is MOVED
# to the canonical location instead — a guard that can eat your source of truth is worse than
# the leak it prevents.
#
# Install:
#   install -m 755 registry_guard.sh /usr/local/bin/registry-guard
#   crontab -l 2>/dev/null | grep -q registry-guard || \
#     (crontab -l 2>/dev/null; echo '*/15 * * * * /usr/local/bin/registry-guard >>/var/log/registry-guard.log 2>&1') | crontab -
#
# Dry run:
#   DRY_RUN=1 /usr/local/bin/registry-guard

set -uo pipefail

# --- configuration -----------------------------------------------------------------------
REGISTRY_NAME="${REGISTRY_NAME:-state-registry.md}"
ALT_NAMES="${ALT_NAMES:-my-registry.md}"
CANONICAL="${CANONICAL:-$HOME/private/state-registry.md}"
SEARCH_ROOTS="${SEARCH_ROOTS:-$HOME /opt /srv}"
MAX_DEPTH="${MAX_DEPTH:-6}"
DRY_RUN="${DRY_RUN:-0}"
# -----------------------------------------------------------------------------------------

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { printf '%s  %s\n' "$(ts)" "$*"; }
act() { if [[ "$DRY_RUN" == "1" ]]; then log "DRY-RUN would: $*"; else eval "$@"; fi; }

mkdir -p "$(dirname "$CANONICAL")"
chmod 700 "$(dirname "$CANONICAL")" 2>/dev/null || true

names=("$REGISTRY_NAME")
for n in $ALT_NAMES; do names+=("$n"); done

found_any=0

# Enumerate git repositories under the search roots.
repos="$(find $SEARCH_ROOTS -maxdepth "$MAX_DEPTH" -type d -name .git -prune 2>/dev/null \
         | sed 's#/\.git$##' | sort -u)"

[[ -z "$repos" ]] && { log "no git repositories found under: $SEARCH_ROOTS"; exit 0; }

while IFS= read -r repo; do
  [[ -d "$repo" ]] || continue

  # 1) Make sure the ignore rule exists, so the next copy never gets staged at all.
  ignore="$repo/.git/info/exclude"
  for n in "${names[@]}"; do
    if ! grep -qxF "$n" "$ignore" 2>/dev/null; then
      act "printf '%s\n' '$n' >> '$ignore'"
      log "added '$n' to $ignore"
    fi
  done

  # 2) Untrack it if it is already in the index — the dangerous case, since a tracked file
  #    is one commit away from the remote and .gitignore does not cover tracked files.
  for n in "${names[@]}"; do
    if git -C "$repo" ls-files --error-unmatch "**/$n" >/dev/null 2>&1 || \
       git -C "$repo" ls-files --error-unmatch "$n" >/dev/null 2>&1; then
      found_any=1
      log "ALERT: '$n' is TRACKED in $repo — untracking"
      act "git -C '$repo' rm --cached --quiet -r -- '*$n' || true"
    fi
  done

  # 3) Remove stray working-tree copies.
  while IFS= read -r hit; do
    [[ -f "$hit" ]] || continue
    found_any=1
    if [[ -s "$CANONICAL" ]]; then
      if cmp -s "$hit" "$CANONICAL"; then
        log "removing duplicate registry: $hit (identical to canonical)"
        act "rm -f '$hit'"
      else
        stamp="$CANONICAL.conflict.$(date +%Y%m%d-%H%M%S)"
        log "registry in repo DIFFERS from canonical — preserving as $stamp"
        act "cp -a '$hit' '$stamp'"
        act "rm -f '$hit'"
      fi
    else
      log "no canonical registry yet — MOVING $hit -> $CANONICAL instead of deleting"
      act "mv '$hit' '$CANONICAL'"
      act "chmod 600 '$CANONICAL'"
    fi
  done < <(for n in "${names[@]}"; do
             find "$repo" -path "$repo/.git" -prune -o -type f -name "$n" -print 2>/dev/null
           done)

done <<< "$repos"

if [[ "$found_any" == "0" ]]; then
  log "clean — no registry copies inside any repository"
fi
exit 0
