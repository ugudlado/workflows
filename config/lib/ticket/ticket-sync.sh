#!/usr/bin/env bash
# Shared body for ticket-start/review/qa/rework: backlog task -> $TICKET_SYNC_STATUS via REST.
# ticket-done has extra idempotency logic and does not use this script.
# When ticketing=backlog, REST failure aborts the workflow (exit 1).
set -euo pipefail

# Ticketing-unconfigured is a no-op regardless of env — must be checked before
# any hard `:?` requirement below, so an unconfigured consumer never aborts.
STATE_YAML="${ORCHESTRATOR_STATE_YAML_PATH:-${STATE_YAML_PATH:-}}"
LIB="$(cd "$(dirname "$0")" && pwd)/backlog-api.sh"
# shellcheck source=backlog-api.sh
source "$LIB"


ticket_id=""
ticket_id="$(backlog_api_run_ticket_id "$STATE_YAML")"
ticketing="$(backlog_api_ticketing)"
if [ -n "$ticket_id" ]; then
  ticket_id="$(printf '%s' "$ticket_id" | tr '[:lower:]' '[:upper:]')"
fi

if [ -z "$ticket_id" ] || [ "$ticketing" != "backlog" ]; then
  printf '%s\n' "{\"status\": \"completed\", \"outputs\": {\"ticket_status_set\": \"${TICKET_SYNC_STATUS:-}\"}}"
  exit 0
fi

: "${REPO_ROOT:?orchestrator: REPO_ROOT required}"
: "${TICKET_SYNC_STATUS:?orchestrator: TICKET_SYNC_STATUS required}"
: "${TICKET_SYNC_LOG_PREFIX:?orchestrator: TICKET_SYNC_LOG_PREFIX required}"
: "${STATE_YAML:?orchestrator: state yaml path required}"

if ! backlog_api_base >/dev/null; then
  echo "ERROR ${TICKET_SYNC_LOG_PREFIX}: BACKLOG_URL/BACKLOG_TOKEN/BACKLOG_PROJECT_ID missing for ${ticket_id}" >&2
  printf '%s\n' "{\"status\": \"failed\", \"outputs\": {}, \"evidence\": {\"summary\": \"BACKLOG_URL/BACKLOG_TOKEN/BACKLOG_PROJECT_ID missing\"}}"
  exit 1
fi

if ! backlog_api_put_status "$ticket_id" "$TICKET_SYNC_STATUS"; then
  echo "ERROR ${TICKET_SYNC_LOG_PREFIX}: REST status update failed for ${ticket_id} -> ${TICKET_SYNC_STATUS}" >&2
  printf '%s\n' "{\"status\": \"failed\", \"outputs\": {}, \"evidence\": {\"summary\": \"PUT tasks/${ticket_id} status failed\"}}"
  exit 1
fi

echo "${TICKET_SYNC_LOG_PREFIX}: ${ticket_id} -> ${TICKET_SYNC_STATUS}" >&2
backlog_api_post_comment "$ticket_id" "${TICKET_SYNC_LOG_PREFIX}: status set to ${TICKET_SYNC_STATUS}." ||
  echo "WARN ${TICKET_SYNC_LOG_PREFIX}: comment post failed for ${ticket_id}" >&2
printf '%s\n' "{\"status\": \"completed\", \"outputs\": {\"ticket_status_set\": \"${TICKET_SYNC_STATUS}\"}}"
