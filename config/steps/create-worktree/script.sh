#!/usr/bin/env bash
# create-worktree — create feature worktree for implementation artifacts.
#
# Always creates a worktree. Re-uses worktree_path if already set in state.
#
# Remote (cloud/Slack) sessions already run in an isolated sandbox on their own
# branch — a local worktree would just misdirect every downstream step into a
# detached dir instead of the branch the PR flow surfaces. No-op there.
#
# Branch: <type>/<slug>. The type is triage's call (`# Triage: feature|fix|quick`
# in triage.md, which dev runs before this step) mapped to feature/fix/chore;
# without a triage.md it comes from the workflow (bugfix -> fix, else the name).
#
# Env (injected by orchestrator): REPO_ROOT, CHANGE_ID, STATE_YAML_PATH,
# ORCHESTRATOR_ARTIFACTS_DIR
# Outputs: {created, worktree_path, branch, change_type} or {created: false, reason}
# (change_type is triage's call, echoed so dev.yaml can route on it.)
# state_patch: worktree_path + branch written back to state when created.

set -uo pipefail

: "${REPO_ROOT:?orchestrator: REPO_ROOT required}"
: "${CHANGE_ID:?orchestrator: CHANGE_ID required}"

CHANGE_TYPE=""
TRIAGE="${ORCHESTRATOR_ARTIFACTS_DIR:-}/triage.md"
if [ -n "${ORCHESTRATOR_ARTIFACTS_DIR:-}" ] && [ -f "$TRIAGE" ]; then
  CHANGE_TYPE="$(sed -nE 's/^#[[:space:]]*Triage:[[:space:]]*(feature|fix|quick)([^[:alnum:]].*)?$/\1/Ip' "$TRIAGE" | head -n1 | tr '[:upper:]' '[:lower:]')"
  # dev routes on this, so an unreadable call must stop the run, not default to feature.
  if [ -z "$CHANGE_TYPE" ]; then
    printf '%s\n' '{"created": false, "reason": "triage.md has no \"# Triage: feature|fix|quick\" heading"}'
    exit 1
  fi
fi
CT_JSON=""
[ -n "$CHANGE_TYPE" ] && CT_JSON=", \"change_type\": \"$CHANGE_TYPE\""

if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  printf '%s\n' "{\"created\": false, \"reason\": \"remote session — using sandbox checkout in place, no local worktree\"$CT_JSON}"
  exit 0
fi

STATE_YAML="${ORCHESTRATOR_STATE_YAML_PATH:-${STATE_YAML_PATH:?orchestrator: STATE_YAML_PATH required}}"
WORKTREE_BASE_DIR="${WORKTREE_BASE_DIR:-$HOME/code/feature_worktrees}"

# Read existing worktree_path, branch and schema from state.
read_state() {
  python3 -c "
import sys, yaml
raw = yaml.safe_load(open('$STATE_YAML')) or {}
print(raw.get('worktree_path') or '')
print(raw.get('branch') or '')
print(raw.get('schema') or '')
" 2>/dev/null || printf '\n\n\n'
}

{ IFS= read -r _EXISTING_WT; IFS= read -r _EXISTING_BRANCH; IFS= read -r _SCHEMA; } <<< "$(read_state)"

TYPE="${CHANGE_TYPE:-${_SCHEMA:-feature}}"
case "$TYPE" in
  quick) PREFIX=chore ;;
  bugfix) PREFIX=fix ;;
  *) PREFIX="$TYPE" ;;
esac
BRANCH="$PREFIX/$CHANGE_ID"
WORKTREE_PATH="$WORKTREE_BASE_DIR/$CHANGE_ID"

# Re-use existing worktree if already present; it keeps the branch it was made with.
if [ -n "$_EXISTING_WT" ] && [ -d "$_EXISTING_WT" ]; then
  printf '%s\n' "{\"created\": false, \"reason\": \"worktree already exists\", \"worktree_path\": \"$_EXISTING_WT\", \"branch\": \"${_EXISTING_BRANCH:-$BRANCH}\"$CT_JSON}"
  exit 0
fi

mkdir -p "$WORKTREE_BASE_DIR"

if git -C "$REPO_ROOT" worktree list --porcelain | grep -q "worktree $WORKTREE_PATH"; then
  printf '%s\n' "{\"created\": false, \"reason\": \"worktree already registered\", \"worktree_path\": \"$WORKTREE_PATH\", \"branch\": \"$BRANCH\"$CT_JSON, \"state_patch\": {\"worktree_path\": \"$WORKTREE_PATH\", \"branch\": \"$BRANCH\"}}"
  exit 0
fi

BASE="$(git -C "$REPO_ROOT" rev-parse HEAD)"
FRESH=1
git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE" 2>&1 >&2 || {
  FRESH=0
  git -C "$REPO_ROOT" worktree add "$WORKTREE_PATH" "$BRANCH" 2>&1 >&2 || {
    printf '%s\n' '{"created": false, "reason": "git worktree add failed"}'
    exit 1
  }
}

# A fresh worktree has none of the repo's untracked setup (node_modules, a venv,
# sibling checkouts its build expects). The repo's own committed
# .orchestrator/setup.sh, if any, makes it ready: it runs here, outside the agent
# sandbox and with network, in the new worktree, with REPO_ROOT set to the main
# checkout. Checks that later steps run inside the sandbox can then work offline.
# It runs unsandboxed, so only the copy in the commit this worktree branched from
# (the repo owner's, read from git, not the working tree) and only for a branch
# created just now: a reused branch may hold an earlier run's agent commits.
if [ "$FRESH" = 1 ] && git -C "$REPO_ROOT" cat-file -e "$BASE:.orchestrator/setup.sh" 2>/dev/null; then
  SETUP="$(mktemp)"
  trap 'rm -f "$SETUP"' EXIT
  git -C "$REPO_ROOT" show "$BASE:.orchestrator/setup.sh" >"$SETUP" &&
    (cd "$WORKTREE_PATH" && REPO_ROOT="$REPO_ROOT" bash "$SETUP" </dev/null) >&2 || {
    # Undo the worktree and branch: a retry would otherwise reuse them, and setup runs only for a new branch.
    git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH" >&2 2>&1
    git -C "$REPO_ROOT" branch -D "$BRANCH" >&2 2>&1
    printf '%s\n' '{"created": false, "reason": "setup.sh failed; worktree and branch removed"}'
    exit 1
  }
fi

printf '%s\n' "{\"created\": true, \"worktree_path\": \"$WORKTREE_PATH\", \"branch\": \"$BRANCH\"$CT_JSON, \"state_patch\": {\"worktree_path\": \"$WORKTREE_PATH\", \"branch\": \"$BRANCH\"}}"
