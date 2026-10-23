"""Tests for name-branch: dev's run branch is renamed for triage's call after the
worktree exists, and an unreadable call fails instead of defaulting."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "steps" / "name-branch" / "script.sh"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def _run(tmp_path: Path, triage: str | None, worktree: bool = True) -> tuple[int, dict, Path]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-qm", "init")
    wt = tmp_path / "wt"
    if worktree:
        _git(repo, "worktree", "add", "-q", "-b", "dev/demo", str(wt))
    arts = tmp_path / "arts"
    arts.mkdir()
    if triage is not None:
        (arts / "triage.md").write_text(triage)
    env = {**os.environ, "CHANGE_ID": "demo", "ORCHESTRATOR_ARTIFACTS_DIR": str(arts)}
    for k in ("STATE_YAML_PATH", "ORCHESTRATOR_STATE_YAML_PATH", "WORKTREE_PATH", "BRANCH"):
        env.pop(k, None)
    if worktree:
        env.update(WORKTREE_PATH=str(wt), BRANCH="dev/demo")
    res = subprocess.run(["bash", str(_SCRIPT)], env=env, capture_output=True, text=True)
    return res.returncode, json.loads(res.stdout.strip().splitlines()[-1]), wt


def test_branch_is_renamed_for_triages_call(tmp_path):
    for call, prefix in [("feature", "feature"), ("fix", "fix"), ("quick", "chore")]:
        rc, out, wt = _run(tmp_path / call, f"# Triage: {call}\n\nBecause the ticket says so.\n")
        assert rc == 0 and out["change_type"] == call  # dev.yaml routes on it
        assert out["branch"] == out["state_patch"]["branch"] == f"{prefix}/demo"
        assert _git(wt, "symbolic-ref", "--short", "HEAD") == f"{prefix}/demo"


def test_no_worktree_still_reports_the_call(tmp_path):
    rc, out, _ = _run(tmp_path, "# Triage: fix\n", worktree=False)
    assert rc == 0 and out == {"change_type": "fix"}


def test_unreadable_triage_fails_instead_of_defaulting(tmp_path):
    rc, out, wt = _run(tmp_path, "Looks like a fix to me.\n")
    assert rc != 0 and "Triage" in out["outputs"]["reason"]
    assert _git(wt, "symbolic-ref", "--short", "HEAD") == "dev/demo"
