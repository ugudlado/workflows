#!/usr/bin/env bash
# Appends validated proposed-scenarios rows to each target pack's
# scenarios/train.jsonl and commits them. Learning is best-effort: this step
# never fails the run.
set -euo pipefail
: "${ORCHESTRATOR_STEP_DIR:?orchestrator: ORCHESTRATOR_STEP_DIR required}"

# Capture the step's JSON result so the publish hook below can run after it
# without swallowing the last-line JSON contract (stdout's last line must be
# the step's JSON object).
_result="$(python3 "${ORCHESTRATOR_STEP_DIR}/persist_learnings.py" "$@")"

# Publish the appended scenarios to the pack registry, per step. The
# `pack publish-scenarios` verb is being added engine-side; a build without it
# exits non-zero and is ignored, so this stays a no-op until the verb lands.
if [ -n "${ORCHESTRATOR_PACK:-}" ] && command -v orchestrator >/dev/null 2>&1; then
  for _step in ${ORCHESTRATOR_PERSISTED_STEPS:-}; do
    orchestrator pack publish-scenarios "${ORCHESTRATOR_PACK}" --step "${_step}" \
      >&2 2>&1 || echo "persist-learnings: publish-scenarios unavailable for ${_step}, skipped" >&2
  done
fi

printf '%s\n' "${_result}"
