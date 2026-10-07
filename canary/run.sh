#!/usr/bin/env bash
# canary/run.sh — exercise every run: (exec) step contract against a throwaway
# git repo fixture. No engine DB writes: each script is invoked directly with
# the env vars orchestrator would inject, and stdout is checked for valid JSON.
# Steps needing a live backlog/ticket backend are skipped (see skip.txt).
set -uo pipefail

PACK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STEPS_DIR="$PACK_ROOT/config/steps"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# workflow-report imports orchestrator_next directly; point PYTHONPATH at an
# engine checkout. CI sets ORCHESTRATOR_ENGINE_SRC to the cloned engine repo;
# locally, fall back to a sibling ../orchestrator checkout if present.
ENGINE_SRC="${ORCHESTRATOR_ENGINE_SRC:-$PACK_ROOT/../orchestrator}"
if [ -d "$ENGINE_SRC/orchestrator_next" ]; then
  export PYTHONPATH="$ENGINE_SRC${PYTHONPATH:+:$PYTHONPATH}"
fi

REPO="$WORK/repo"
CHANGE_ID="canary-$(date +%s)"
SUMMARY="$WORK/summary.json"
SKIP_FILE="$(dirname "$0")/skip.txt"

mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.email "canary@example.com"
git -C "$REPO" config user.name "canary"
mkdir -p "$REPO/spec/changes/$CHANGE_ID"
echo "seed" > "$REPO/README.md"
git -C "$REPO" add -A
git -C "$REPO" commit -q -m "seed"

STATE_YAML="$REPO/spec/changes/$CHANGE_ID/state.yaml"
cat > "$STATE_YAML" <<EOF
change_id: $CHANGE_ID
slug: $CHANGE_ID
schema: feature
status: active
phase: main
repo_root: $REPO
worktree_path: ""
branch: ""
step_history: []
workflow_plan: {main: {nodes: [], filtered: []}}
EOF

results=()

run_step() {
  local id="$1"; shift
  local dir="$STEPS_DIR/$id"
  if [ ! -d "$dir" ]; then
    results+=("{\"step\":\"$id\",\"status\":\"skipped\",\"reason\":\"no step dir\"}")
    return
  fi
  echo "=== $id ==="
  local out status
  out="$(env ORCHESTRATOR_STEP_DIR="$dir" REPO_ROOT="$REPO" CHANGE_ID="$CHANGE_ID" \
        STATE_YAML_PATH="$STATE_YAML" ORCHESTRATOR_STATE_YAML_PATH="$STATE_YAML" \
        "$@" bash "$dir/script.sh" 2>&1)"
  if echo "$out" | tail -1 | python3 -c 'import json,sys; json.loads(sys.stdin.readline())' >/dev/null 2>&1; then
    status="pass"
  else
    status="fail"
  fi
  echo "$out"
  results+=("{\"step\":\"$id\",\"status\":\"$status\"}")
}

# Skipped: need a live backlog/ticket backend or the pack-registry publish
# verb, which isn't available in this fixture harness.
: > "$SKIP_FILE"
for id in ticket-start ticket-review ticket-qa ticket-rework ticket-done; do
  echo "$id: needs a live backlog REST backend (ticketing=backlog); no fixture server here" >> "$SKIP_FILE"
  results+=("{\"step\":\"$id\",\"status\":\"skipped\",\"reason\":\"needs live backlog backend\"}")
done
echo "persist-learnings: publishes to the pack scenario registry; no registry fixture here" >> "$SKIP_FILE"
results+=("{\"step\":\"persist-learnings\",\"status\":\"skipped\",\"reason\":\"needs pack registry\"}")

run_step check-rerun
run_step create-worktree
WORKTREE_PATH="$(python3 -c "import yaml; print((yaml.safe_load(open('$STATE_YAML')) or {}).get('worktree_path') or '')" 2>/dev/null)"
[ -n "$WORKTREE_PATH" ] && python3 - "$STATE_YAML" "$WORKTREE_PATH" <<'PY'
import sys, yaml
p, wt = sys.argv[1], sys.argv[2]
d = yaml.safe_load(open(p)) or {}
d["worktree_path"] = wt
d["branch"] = "feature/" + d.get("change_id", "canary")
yaml.safe_dump(d, open(p, "w"), sort_keys=False)
PY
run_step mark-change-completed
mkdir -p "$REPO/spec/changes/archive"
run_step archive-completed-change ARCHIVE_PATH="$REPO/spec/changes/archive/$CHANGE_ID" WORKTREE_ROOT="${WORKTREE_PATH:-}"
run_step remove-worktree
run_step merge-to-main
run_step workflow-report

printf '{"canary_run":"%s","results":[%s]}\n' "$CHANGE_ID" "$(IFS=,; echo "${results[*]}")" | python3 -m json.tool > "$SUMMARY"
cat "$SUMMARY"
echo "summary: $SUMMARY"

fail_count="$(python3 -c "import json; d=json.load(open('$SUMMARY')); print(sum(1 for r in d['results'] if r['status']=='fail'))")"
exit "$fail_count"
