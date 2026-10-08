#!/usr/bin/env python3
"""Workflow report step: summarise a run from its state file.

The engine is stateless (`orchestrator next` only), so the run's history lives
in the driver's state file, given as STATE_YAML_PATH. That file is JSON (valid
YAML); stdlib only. No durations, models or costs: the state does not record
them, and this step does not guess them.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter


def main() -> int:
    path = os.environ.get("STATE_YAML_PATH") or os.environ.get("ORCHESTRATOR_STATE_YAML_PATH", "")
    if not path:
        sys.stderr.write("error: STATE_YAML_PATH required\n")
        return 1
    try:
        with open(path, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError) as e:
        print(json.dumps({"status": "failed", "evidence": {"summary": f"cannot read state: {e}"}}))
        return 1

    steps = [{k: h.get(k) for k in ("step", "status", "attempt")} for h in st.get("step_history", [])]
    report = {
        "change_id": st.get("change_id") or st.get("slug"),
        "workflow": st.get("workflow"),
        "started": st.get("started"),
        "steps": steps,
        "counts": dict(Counter(s["status"] for s in steps)),
    }
    for s in steps:
        sys.stderr.write(f"{s['step']:<28} {s['status']:<12} try {s['attempt']}\n")
    print(json.dumps({"status": "completed", "outputs": {"report": report}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
