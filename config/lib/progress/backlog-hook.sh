#!/usr/bin/env bash
# Progress hook: forward orchestrator progress events (JSON lines on stdin) to
# the Backlog ticket's live progress feed.
#
# The engine spawns this once per run with ORCHESTRATOR_PROGRESS_HOOK=<this file>
# and streams events; it knows nothing about Backlog. Creds come from the same
# env the ticket-* steps use (BACKLOG_URL / BACKLOG_TOKEN / BACKLOG_PROJECT_ID),
# the ticket from ORCHESTRATOR_TICKET_ID.
#
# Best-effort by contract: HTTP failures are swallowed — losing live progress
# must never fail a step. A {"kind":"run","status":"completed"} event clears
# the feed (durable history lives in comments, not here).
set -u
# shellcheck source=../ticket/backlog-api.sh
. "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/ticket/backlog-api.sh"

ticket_id="${ORCHESTRATOR_TICKET_ID:-}"
[ -n "$ticket_id" ] || exec cat >/dev/null   # no ticket → drain stdin silently
url="$(_backlog_tasks_base)/${ticket_id}/progress" || exec cat >/dev/null

# ponytail: batching lives in python (timer + 100-cap); bash `read -t` would
# do, but json-escaping a batch in bash is where the bugs live.
# python3 -c, NOT `python3 -` — stdin must stay the event stream.
read -r -d '' PY <<'PY' || true
import json, sys, time, urllib.request

url, token = sys.argv[1], sys.argv[2]
MAX_BATCH, INTERVAL = 100, 1.0


def send(method, body=None):
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except Exception:  # noqa: BLE001 - best-effort
        pass


batch, last = [], time.monotonic()


def flush():
    global batch, last
    if batch:
        send("POST", json.dumps({"events": batch}).encode())
        batch = []
    last = time.monotonic()


for line in sys.stdin:
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("kind") == "run":
        flush()
        if ev.get("status") == "completed":
            send("DELETE")
        continue
    batch.append(ev)
    if len(batch) >= MAX_BATCH or time.monotonic() - last >= INTERVAL:
        flush()
flush()
PY
exec python3 -c "$PY" "$url" "$BACKLOG_TOKEN"
