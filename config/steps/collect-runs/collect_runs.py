#!/usr/bin/env python3
"""collect-runs — list finished runs the nightly learn workflow has not seen.

Runs live at `<runs root>/<slug>/state.yaml`. A run is eligible when

  - its `step_history` holds a completed `workflow-report` (the same "finished"
    fact check-rerun uses; `status: completed` is NOT the signal),
  - its run dir has no `learned.json` marker (written by mark-learned), and
  - it is not this learn run itself, nor any run of the `learn` workflow.

Writes `runs.json`, a list of {slug, run_dir, state_path, artifacts_dir,
finished_at}, and prints the step's JSON result as the last stdout line.
Zero eligible runs is success (an empty list), never a failure.

Runs root: env ORCHESTRATOR_RUNS_DIR if set, else
Path(STATE_YAML_PATH).parent.parent.

The driver passes `--runs-out <path>` (payload.out.runs). Without it the file
goes to $ORCHESTRATOR_ARTIFACTS_DIR/runs.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

TERMINAL_STEP = "workflow-report"  # same definition as check-rerun
MARKER = "learned.json"
OWN_WORKFLOW = "learn"


def run_finished(state: dict) -> bool:
    return any(
        isinstance(e, dict) and e.get("step") == TERMINAL_STEP and e.get("status") == "completed"
        for e in state.get("step_history") or []
    )


def finished_at(state: dict, state_path: Path) -> str | None:
    """Best-effort finish time: the terminal entry's stamp, else completed_at."""
    for e in reversed(state.get("step_history") or []):
        if isinstance(e, dict) and e.get("step") == TERMINAL_STEP and e.get("status") == "completed":
            for key in ("finished_at", "completed_at", "ended_at", "timestamp", "at"):
                if e.get(key):
                    return str(e[key])
    if state.get("completed_at"):
        return str(state["completed_at"])
    return None


def runs_root() -> Path | None:
    env = os.environ.get("ORCHESTRATOR_RUNS_DIR", "")
    if env:
        return Path(env)
    state_path = os.environ.get("STATE_YAML_PATH", "")
    if state_path:
        return Path(state_path).parent.parent
    return None


def is_learn_run(state: dict) -> bool:
    for key in ("workflow", "workflow_name"):
        if state.get(key) == OWN_WORKFLOW:
            return True
    return False


def collect(root: Path, own_slug: str = "", own_dir: Path | None = None) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if not root.is_dir():
        return found
    own_resolved = own_dir.resolve() if own_dir else None
    for run_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        state_path = run_dir / "state.yaml"
        if not state_path.is_file() or (run_dir / MARKER).exists():
            continue
        if run_dir.name == own_slug or (own_resolved and run_dir.resolve() == own_resolved):
            continue
        try:
            state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue  # unreadable run: skip, retry tomorrow
        if not isinstance(state, dict) or is_learn_run(state) or not run_finished(state):
            continue
        found.append({
            "slug": run_dir.name,
            "run_dir": str(run_dir),
            "state_path": str(state_path),
            "artifacts_dir": str(run_dir / "artifacts"),
            "finished_at": finished_at(state, state_path),
        })
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-out", type=Path)
    args = parser.parse_args()

    out = args.runs_out
    if out is None:
        art = os.environ.get("ORCHESTRATOR_ARTIFACTS_DIR", "")
        if not art:
            print(json.dumps({"error": "pass --runs-out or set ORCHESTRATOR_ARTIFACTS_DIR"}))
            return 3
        out = Path(art) / "runs.json"

    root = runs_root()
    if root is None:
        print(json.dumps({"error": "set ORCHESTRATOR_RUNS_DIR or STATE_YAML_PATH"}))
        return 3

    state_path = os.environ.get("STATE_YAML_PATH", "")
    own_slug = os.environ.get("ORCHESTRATOR_CHANGE_ID") or os.environ.get("CHANGE_ID") or ""
    own_dir = Path(state_path).parent if state_path else None
    runs = collect(root, own_slug, own_dir)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")
    print(f"collect-runs: {len(runs)} unlearned finished run(s) under {root}", file=sys.stderr)
    print(json.dumps({"status": "completed", "outputs": {"runs": str(out), "run_count": len(runs)}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
