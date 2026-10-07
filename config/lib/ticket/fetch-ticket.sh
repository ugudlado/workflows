#!/usr/bin/env bash
# fetch-ticket.sh <ticket-id> — print the backlog task as plain markdown.
# Run by the load-ticket-context judgment step. Needs BACKLOG_URL, BACKLOG_TOKEN
# and BACKLOG_PROJECT_ID (same env as set-status.sh).
# Exit 1 with a message on stderr on any failure; never prints invented content.
set -euo pipefail

LIB="$(cd "$(dirname "$0")" && pwd)/backlog-api.sh"
# shellcheck source=backlog-api.sh
source "$LIB"

ticket_id="${1:-}"
if [[ ! "$ticket_id" =~ ^[A-Za-z][A-Za-z0-9]*-[0-9]+$ ]]; then
  echo "ERROR fetch-ticket: usage: fetch-ticket.sh <ticket-id> (got '${ticket_id}')" >&2
  exit 1
fi
ticket_id="$(printf '%s' "$ticket_id" | tr '[:lower:]' '[:upper:]')"

if [ "$(backlog_api_ticketing)" != "backlog" ]; then
  echo "ERROR fetch-ticket: ticketing not configured (BACKLOG_URL/BACKLOG_TOKEN unset)" >&2
  exit 1
fi
if ! backlog_api_base >/dev/null; then
  echo "ERROR fetch-ticket: BACKLOG_URL/BACKLOG_TOKEN/BACKLOG_PROJECT_ID missing (ticket ${ticket_id})" >&2
  exit 1
fi

err_file="$(mktemp)"
trap 'rm -f "$err_file"' EXIT
if ! json="$(backlog_api_get_task "$ticket_id" 2>"$err_file")"; then
  echo "ERROR fetch-ticket: GET tasks/${ticket_id} failed: $(cat "$err_file")" >&2
  exit 1
fi
printf '%s' "$json" | backlog_api_format_plain
