"""Backlog REST integration: ticket context, project resolution, and API helpers.

Covers config/lib/ticket/backlog-api.sh and fetch-ticket.sh (the backlog tracker's helpers, used by load-ticket-context) — all
config-owned bash, exercised via subprocess. Engine-boundary assertions (that
orchestrator_next has no ticket-fetching logic of its own) live in
orchestrator_next/tests/test_run_loop_ticket_agnostic.py instead.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

_REPO_PATH = Path(_REPO)
_FETCH_SCRIPT = _REPO_PATH / "lib" / "ticket" / "fetch-ticket.sh"
_API_SH = _REPO_PATH / "lib" / "ticket" / "backlog-api.sh"


def _run_fetch(tmp_path, args, env):
    return subprocess.run(
        ["bash", str(_FETCH_SCRIPT), *args],
        capture_output=True, text=True, cwd=str(tmp_path), env=env,
    )


def test_fetch_ticket_success(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    curl = fake_bin / "curl"
    payload = {
        "id": "ORC-125",
        "title": "Replace CLI with REST",
        "status": "To Do",
        "priority": "high",
        "labels": ["bug"],
        "description": "Use BACKLOG_URL",
        "acceptanceCriteriaItems": [
            {"index": 1, "checked": False, "text": "REST fetch works"},
        ],
    }
    curl.write_text("#!/usr/bin/env bash\necho '" + json.dumps(payload) + "'\n")
    curl.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{os.environ['PATH']}"
    env["BACKLOG_URL"] = "https://example.test"
    env["BACKLOG_TOKEN"] = "tok"
    env["BACKLOG_PROJECT_ID"] = "orc"

    proc = _run_fetch(tmp_path, ["orc-125"], env)
    assert proc.returncode == 0, proc.stderr
    assert "Replace CLI with REST" in proc.stdout
    assert "REST fetch works" in proc.stdout
    assert "Use BACKLOG_URL" in proc.stdout


def test_fetch_ticket_unset_env_fails(tmp_path):
    """No ticketing env: the judgment step must not call this; it fails cleanly."""
    env = os.environ.copy()
    for k in ("BACKLOG_URL", "BACKLOG_TOKEN", "BACKLOG_PROJECT", "BACKLOG_PROJECT_ID"):
        env.pop(k, None)
    proc = _run_fetch(tmp_path, ["ORC-125"], env)
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "ticketing not configured" in proc.stderr


def test_fetch_ticket_missing_project_fails(tmp_path):
    """Credentials present but no project id must exit 1, never invent scope."""
    env = os.environ.copy()
    env["BACKLOG_URL"] = "https://example.invalid"
    env["BACKLOG_TOKEN"] = "tok"
    env.pop("BACKLOG_PROJECT", None)
    env.pop("BACKLOG_PROJECT_ID", None)
    proc = _run_fetch(tmp_path, ["ORC-125"], env)
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "BACKLOG_PROJECT_ID" in proc.stderr


def test_fetch_ticket_bad_id_fails(tmp_path):
    env = os.environ.copy()
    for args in ([], ["ORC-12x"], ["not a ticket"]):
        proc = _run_fetch(tmp_path, args, env)
        assert proc.returncode == 1
        assert proc.stdout == ""
        assert "usage" in proc.stderr


def test_run_ticket_id_prefers_artifact_over_state(tmp_path):
    arts = tmp_path / "artifacts"
    arts.mkdir()
    state = tmp_path / "state.yaml"
    state.write_text("ticket_id: OLD-1\n")

    def ticket_id(extra_env):
        env = {k: v for k, v in os.environ.items() if k != "ORCHESTRATOR_ARTIFACTS_DIR"}
        env.update(extra_env)
        return subprocess.run(
            ["bash", "-c", f"source '{_API_SH}' && backlog_api_run_ticket_id '{state}'"],
            capture_output=True, text=True, env=env,
        ).stdout

    env = {"ORCHESTRATOR_ARTIFACTS_DIR": str(arts)}
    assert ticket_id(env) == "OLD-1"  # no ticket.json: state fallback
    (arts / "ticket.json").write_text(json.dumps({"ticket_id": "ORC-7"}))
    assert ticket_id(env) == "ORC-7"
    assert ticket_id({}) == "OLD-1"  # no artifacts dir: state fallback


def _resolve_project(env_overrides: dict, repo_root: str | None) -> str:
    """Run backlog_api_project() under a controlled env; return its stdout."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("BACKLOG_PROJECT", "BACKLOG_PROJECT_ID")}
    if repo_root is not None:
        env["REPO_ROOT"] = repo_root
    else:
        env.pop("REPO_ROOT", None)
    env.update(env_overrides)
    proc = subprocess.run(
        ["bash", "-c", f"source '{_API_SH}' && backlog_api_project"],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def _write_project_yaml(tmp_path: Path, project_id) -> str:
    spec = tmp_path / "spec"
    spec.mkdir(parents=True, exist_ok=True)
    doc = {"version": 1, "ticketing": "backlog"}
    if project_id is not None:
        doc["project_id"] = project_id
    (spec / "project.yaml").write_text(yaml.safe_dump(doc))
    return str(tmp_path)


def test_backlog_api_project_env_id_wins(tmp_path):
    """BACKLOG_PROJECT_ID env takes precedence over spec/project.yaml."""
    repo = _write_project_yaml(tmp_path, "from-config")
    assert _resolve_project({"BACKLOG_PROJECT_ID": "from-env-id"}, repo) == "from-env-id"


def test_backlog_api_project_env_id_beats_legacy_name(tmp_path):
    """BACKLOG_PROJECT_ID wins; BACKLOG_PROJECT is only a legacy fallback."""
    repo = _write_project_yaml(tmp_path, "from-config")
    got = _resolve_project(
        {"BACKLOG_PROJECT": "from-env-name", "BACKLOG_PROJECT_ID": "from-env-id"}, repo)
    assert got == "from-env-id"
    assert _resolve_project({"BACKLOG_PROJECT": "from-env-name"}, repo) == "from-env-name"


def test_backlog_api_project_empty_when_no_env_even_with_config(tmp_path):
    """project_id resolution is env-only — spec/project.yaml is never read,
    even if it has a project_id key and REPO_ROOT points at it."""
    repo = _write_project_yaml(tmp_path, "orchestrator")
    assert _resolve_project({}, repo) == ""


def test_backlog_api_project_empty_when_no_repo_root():
    """No env project and no REPO_ROOT → empty (no crash)."""
    assert _resolve_project({}, None) == ""


def _correlation_line(env_overrides: dict, ticket_id: str = "ORC-125") -> str:
    """Run backlog_api_correlation_line() under a controlled env."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ORCHESTRATOR_CHANGE_ID", "CHANGE_ID", "ORCHESTRATOR_STEP_ID")}
    env.update(env_overrides)
    proc = subprocess.run(
        ["bash", "-c",
         f"source '{_API_SH}' && backlog_api_correlation_line '{ticket_id}'"],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()

def test_correlation_line_carries_full_key():
    got = _correlation_line({
        "ORCHESTRATOR_CHANGE_ID": "orc-125",
        "ORCHESTRATOR_STEP_ID": "implement",
    })
    assert got == "correlation: ticket=ORC-125 change=orc-125 step=implement"

def test_correlation_line_omits_absent_parts():
    """Missing coordinates drop out rather than appearing as empty values."""
    got = _correlation_line({"ORCHESTRATOR_STEP_ID": "code-review"})
    assert got == "correlation: ticket=ORC-125 step=code-review"
    assert "change=" not in got

def test_backlog_api_format_plain_roundtrip():
    """format helper produces readable AC lines from JSON."""
    payload = {
        "id": "ORC-1",
        "title": "T",
        "status": "To Do",
        "priority": "low",
        "labels": ["a"],
        "description": "desc",
        "acceptanceCriteriaItems": [{"index": 1, "checked": True, "text": "done item"}],
    }
    env = os.environ.copy()
    env["PAYLOAD"] = json.dumps(payload)
    proc = subprocess.run(
        ["bash", "-c", f"source '{_API_SH}' && printf '%s' \"$PAYLOAD\" | backlog_api_format_plain"],
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Task ORC-1 - T" in proc.stdout
    assert "[x] #1 done item" in proc.stdout
