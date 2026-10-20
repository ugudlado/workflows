#!/usr/bin/env python3
"""mark-learned — stamp each run collect-runs listed so it is learned from once.

Reads `runs.json` (the driver passes `--runs <path>`; absent or empty is a
no-op) and writes `<run_dir>/learned.json` for every listed run:
{learned_at, learn_run, scenarios_appended}. Idempotent: an existing marker is
left untouched, so a re-run never moves `learned_at`. Prints the step's JSON
result as the last stdout line: `marked` = markers written this call.

`scenarios_appended` is optional context: pass `--scenarios-appended N` or set
ORCHESTRATOR_SCENARIOS_APPENDED; omitted when unknown.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

MARKER = "learned.json"


def load_runs(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [r for r in data if isinstance(r, dict) and r.get("run_dir")] if isinstance(data, list) else []


def mark(runs: list[dict[str, Any]], learn_run: str, appended: int | None) -> int:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marked = 0
    for run in runs:
        run_dir = Path(str(run["run_dir"]))
        marker = run_dir / MARKER
        if not run_dir.is_dir() or marker.exists():
            continue
        record: dict[str, Any] = {"learned_at": now, "learn_run": learn_run}
        if appended is not None:
            record["scenarios_appended"] = appended
        marker.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        marked += 1
    return marked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--scenarios-appended", type=int)
    args = parser.parse_args()

    appended = args.scenarios_appended
    if appended is None and os.environ.get("ORCHESTRATOR_SCENARIOS_APPENDED", "").isdigit():
        appended = int(os.environ["ORCHESTRATOR_SCENARIOS_APPENDED"])
    learn_run = os.environ.get("ORCHESTRATOR_CHANGE_ID") or os.environ.get("CHANGE_ID") or "learn"

    marked = mark(load_runs(args.runs), learn_run, appended)
    print(f"mark-learned: marked {marked} run(s)", file=sys.stderr)
    print(json.dumps({"status": "completed", "outputs": {"marked": marked}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
