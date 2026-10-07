"""Tests for the check-rerun workflow step.

The run is finished when its own step_history has a completed `workflow-report`
entry. Finished -> non-zero exit (the engine then answers needs_you and the run
stops). `status: completed` alone must NOT halt: mark-change-completed stamps it
before open-pr / pr-merged.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

_STEP_PY = Path(__file__).resolve().parents[1] / "steps" / "check-rerun" / "check_rerun.py"
_spec = importlib.util.spec_from_file_location("check_rerun", _STEP_PY)
assert _spec is not None and _spec.loader is not None
check_rerun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_rerun)


def _state(tmp_path: Path, **extra) -> Path:
    p = tmp_path / "state.yaml"
    p.write_text(yaml.safe_dump({"slug": "orc-7", "ticket_id": "ORC-7", "tokens": [], **extra}))
    return p


def _run(monkeypatch, path: Path) -> int:
    monkeypatch.setenv("STATE_YAML_PATH", str(path))
    return check_rerun.main()


def test_finished_run_halts_nonzero(tmp_path, monkeypatch, capsys):
    p = _state(tmp_path, step_history=[
        {"step": "open-pr", "attempt": 1, "status": "completed"},
        {"step": "workflow-report", "attempt": 1, "status": "completed"},
    ])
    before = p.read_text()
    assert _run(monkeypatch, p) != 0
    assert "already finished" in capsys.readouterr().err
    assert p.read_text() == before


def test_status_completed_alone_does_not_halt(tmp_path, monkeypatch):
    """mark-change-completed stamps status before open-pr / pr-merged."""
    p = _state(tmp_path, status="completed", step_history=[
        {"step": "mark-change-completed", "attempt": 1, "status": "completed"},
    ])
    assert _run(monkeypatch, p) == 0


def test_failed_terminal_step_does_not_halt(tmp_path, monkeypatch):
    p = _state(tmp_path, step_history=[{"step": "workflow-report", "attempt": 1, "status": "failed"}])
    assert _run(monkeypatch, p) == 0


def test_empty_history_proceeds_and_leaves_state_untouched(tmp_path, monkeypatch, capsys):
    p = _state(tmp_path, step_history=[])
    before = p.read_text()
    assert _run(monkeypatch, p) == 0
    assert '"proceed"' in capsys.readouterr().out
    assert p.read_text() == before


def test_missing_state_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("STATE_YAML_PATH", str(tmp_path / "nope.yaml"))
    assert check_rerun.main() == 3
