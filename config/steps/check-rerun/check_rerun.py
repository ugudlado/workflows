#!/usr/bin/env python3
"""check-rerun — refuse to rerun a slug whose run already finished.

One slug is one run dir, so "already finished" is a fact in the run's own
state, not a directory hunt. The run is finished when `step_history` holds a
completed `workflow-report` entry (the terminal step). `status: completed` is
NOT the signal: mark-change-completed stamps it before open-pr / pr-merged.

  - Finished → exit 2 with a clear message; the engine answers `needs_you`
    (check-rerun has no `on_failure`) and the run stops. Fresh start = delete
    the run dir.
  - Otherwise → print {"rerun": "proceed"}, exit 0, state untouched.

Env input: STATE_YAML_PATH.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

TERMINAL_STEP = "workflow-report"


def run_finished(state: dict) -> bool:
    return any(
        isinstance(e, dict) and e.get("step") == TERMINAL_STEP and e.get("status") == "completed"
        for e in state.get("step_history") or []
    )


def main() -> int:
    state_path = os.environ.get("STATE_YAML_PATH", "")
    if not state_path or not Path(state_path).is_file():
        print(json.dumps({"error": "STATE_YAML_PATH must point to existing state.yaml"}))
        return 3

    state = yaml.safe_load(Path(state_path).read_text(encoding="utf-8")) or {}
    if run_finished(state):
        who = state.get("ticket_id") or state.get("slug") or state.get("change_id") or "this run"
        msg = (
            f"{who} already finished: {TERMINAL_STEP} is completed in {state_path}. "
            "Delete the run dir to start over."
        )
        print(msg, file=sys.stderr)
        print(json.dumps({"rerun": "halted", "message": msg}))
        return 2

    print(json.dumps({"rerun": "proceed"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
