#!/usr/bin/env bash
# name-branch — rename the run branch for triage's call: feature/, fix/ or chore/<slug>.
#
# create-worktree runs before any agent step, so no agent ever works in the main
# checkout; it cannot know the type yet and names the branch for the workflow
# (dev/<slug>). This step renames it once triage has decided, and echoes
# change_type so dev.yaml can route on it. An unreadable triage.md fails the
# step rather than defaulting to feature.
#
# Env (injected by orchestrator): CHANGE_ID, ORCHESTRATOR_ARTIFACTS_DIR,
# STATE_YAML_PATH; WORKTREE_PATH and BRANCH once create-worktree has run.
# Outputs: {change_type, branch, state_patch: {branch}} or {change_type} when there is no worktree.

set -uo pipefail

: "${CHANGE_ID:?orchestrator: CHANGE_ID required}"
: "${ORCHESTRATOR_ARTIFACTS_DIR:?orchestrator: ORCHESTRATOR_ARTIFACTS_DIR required}"

TRIAGE="$ORCHESTRATOR_ARTIFACTS_DIR/triage.md"
CHANGE_TYPE=""
[ -f "$TRIAGE" ] &&
  CHANGE_TYPE="$(sed -nE 's/^#[[:space:]]*Triage:[[:space:]]*(feature|fix|quick)([^[:alnum:]].*)?$/\1/Ip' "$TRIAGE" | head -n1 | tr '[:upper:]' '[:lower:]')"
if [ -z "$CHANGE_TYPE" ]; then
  printf '%s\n' '{"status": "failed", "outputs": {"reason": "triage.md has no \"# Triage: feature|fix|quick\" heading"}}'
  exit 1
fi

STATE_YAML="${ORCHESTRATOR_STATE_YAML_PATH:-${STATE_YAML_PATH:-}}"
_read_state_field() {
  [ -n "$STATE_YAML" ] || return 0
  python3 -c "
import sys, yaml
raw = yaml.safe_load(open('$STATE_YAML')) or {}
print(raw.get('$1') or '')
" 2>/dev/null || true
}
WORKTREE_PATH="${WORKTREE_PATH:-$(_read_state_field worktree_path)}"
OLD="${BRANCH:-$(_read_state_field branch)}"

# No worktree (a remote session works in its own checkout): nothing to rename.
if [ -z "$WORKTREE_PATH" ] || [ ! -d "$WORKTREE_PATH" ] || [ -z "$OLD" ]; then
  printf '%s\n' "{\"change_type\": \"$CHANGE_TYPE\"}"
  exit 0
fi

case "$CHANGE_TYPE" in
  quick) PREFIX=chore ;;
  *) PREFIX="$CHANGE_TYPE" ;;
esac
NEW="$PREFIX/$CHANGE_ID"

# Only ever rename the run's own branch, the one checked out in its worktree.
CURRENT="$(git -C "$WORKTREE_PATH" symbolic-ref -q --short HEAD 2>/dev/null)"
if [ "$CURRENT" != "$OLD" ]; then
  printf '%s\n' "{\"status\": \"failed\", \"outputs\": {\"reason\": \"worktree is on '$CURRENT', not the run branch '$OLD'\"}}"
  exit 1
fi

if [ "$OLD" != "$NEW" ]; then
  git -c core.hooksPath=/dev/null -C "$WORKTREE_PATH" branch -m "$OLD" "$NEW" >&2 2>&1 || {
    printf '%s\n' "{\"status\": \"failed\", \"outputs\": {\"reason\": \"could not rename $OLD to $NEW (does $NEW already exist?)\"}}"
    exit 1
  }
fi

printf '%s\n' "{\"change_type\": \"$CHANGE_TYPE\", \"branch\": \"$NEW\", \"state_patch\": {\"branch\": \"$NEW\"}}"
