#!/usr/bin/env bash
# set-status.sh <ticket-id> <status> — backlog tracker helper: move a task to <status>
# via REST and post a correlation comment. Idempotent: already at <status> is a
# no-op with no comment. Exit 1 with a message on stderr if the status update fails;
# a failed comment only warns. Needs BACKLOG_URL, BACKLOG_TOKEN, BACKLOG_PROJECT_ID.
# Optional ORCHESTRATOR_STEP_ID / ORCHESTRATOR_CHANGE_ID feed the correlation key.
set -euo pipefail

LIB="$(cd "$(dirname "$0")" && pwd)/backlog-api.sh"
# shellcheck source=backlog-api.sh
source "$LIB"

ticket_id="${1:-}"
target="${2:-}"
if [[ ! "$ticket_id" =~ ^[A-Za-z][A-Za-z0-9]*-[0-9]+$ ]] || [ -z "$target" ]; then
  echo "ERROR set-status: usage: set-status.sh <ticket-id> <status>" >&2
  exit 1
fi
ticket_id="$(printf '%s' "$ticket_id" | tr '[:lower:]' '[:upper:]')"
prefix="${ORCHESTRATOR_STEP_ID:-set-status}"

if [ "$(backlog_api_ticketing)" != "backlog" ] || ! backlog_api_base >/dev/null; then
  echo "ERROR ${prefix}: BACKLOG_URL/BACKLOG_TOKEN/BACKLOG_PROJECT_ID missing for ${ticket_id}" >&2
  exit 1
fi

current=""
if json="$(backlog_api_get_task "$ticket_id" 2>/dev/null)"; then
  current="$(printf '%s' "$json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status") or "")')"
fi
if [ "$current" = "$target" ]; then
  echo "${prefix}: ${ticket_id} already ${target} — skipping" >&2
  exit 0
fi
if ! backlog_api_put_status "$ticket_id" "$target"; then
  echo "ERROR ${prefix}: REST status update failed for ${ticket_id} -> ${target}" >&2
  exit 1
fi
echo "${prefix}: ${ticket_id} -> ${target}" >&2
backlog_api_post_comment "$ticket_id" "${prefix}: status set to ${target}." ||
  echo "WARN ${prefix}: comment post failed for ${ticket_id}" >&2
