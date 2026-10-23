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
# STATE_YAML_PATH (worktree_path and branch, from create-worktree).
# Outputs: {change_type, branch, state_patch: {branch}} or {change_type} when there is no worktree.

set -uo pipefail

: "${CHANGE_ID:?orchestrator: CHANGE_ID required}"
: "${ORCHESTRATOR_ARTIFACTS_DIR:?orchestrator: ORCHESTRATOR_ARTIFACTS_DIR required}"

# A failed step exits 0 with status: failed, so its reason reaches the engine.
fail() {
  printf '%s\n' "{\"status\": \"failed\", \"outputs\": {\"reason\": \"$1\"}}"
  exit 0
}

TRIAGE="$ORCHESTRATOR_ARTIFACTS_DIR/triage.md"
CHANGE_TYPE=""
[ -f "$TRIAGE" ] &&
  CHANGE_TYPE="$(sed -nE 's/^#[[:space:]]*Triage:[[:space:]]*(feature|fix|quick)([^[:alnum:]].*)?$/\1/Ip' "$TRIAGE" | head -n1 | tr '[:upper:]' '[:lower:]')"
[ -n "$CHANGE_TYPE" ] || fail "triage.md has no '# Triage: feature|fix|quick' heading"

STATE_YAML="${ORCHESTRATOR_STATE_YAML_PATH:-${STATE_YAML_PATH:?orchestrator: STATE_YAML_PATH required}}"
STATE="$(python3 -c "
import sys, yaml
raw = yaml.safe_load(open(sys.argv[1])) or {}
print(raw.get('worktree_path') or '')
print(raw.get('branch') or '')
" "$STATE_YAML" 2>/dev/null)" || fail "could not read worktree_path and branch from the state file"
{ IFS= read -r WORKTREE_PATH; IFS= read -r OLD; } <<< "$STATE"

# No worktree (a remote session works in its own checkout): nothing to rename.
if [ -z "$WORKTREE_PATH" ]; then
  printf '%s\n' "{\"change_type\": \"$CHANGE_TYPE\"}"
  exit 0
fi
[ -d "$WORKTREE_PATH" ] || fail "worktree $WORKTREE_PATH is missing"
[ -n "$OLD" ] || fail "the state file has a worktree but no branch"

case "$CHANGE_TYPE" in
  quick) PREFIX=chore ;;
  *) PREFIX="$CHANGE_TYPE" ;;
esac
NEW="$PREFIX/$CHANGE_ID"

# Only ever rename the run's own branch, the one checked out in its worktree.
CURRENT="$(git -C "$WORKTREE_PATH" symbolic-ref -q --short HEAD 2>/dev/null)"
[ "$CURRENT" = "$OLD" ] || fail "worktree is on '$CURRENT', not the run branch '$OLD'"

if [ "$OLD" != "$NEW" ]; then
  git -c core.hooksPath=/dev/null -C "$WORKTREE_PATH" branch -m "$OLD" "$NEW" >&2 2>&1 ||
    fail "could not rename $OLD to $NEW (does $NEW already exist?)"
fi

printf '%s\n' "{\"change_type\": \"$CHANGE_TYPE\", \"branch\": \"$NEW\", \"state_patch\": {\"branch\": \"$NEW\"}}"
