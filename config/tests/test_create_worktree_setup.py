"""Tests for create-worktree's setup hook: the repo's committed .orchestrator/setup.sh
runs once in a fresh worktree, and a failing setup fails the step."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "steps" / "create-worktree" / "script.sh"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def _repo(tmp_path: Path, setup: str | None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("x\n")
    if setup is not None:
        (repo / ".orchestrator").mkdir()
        (repo / ".orchestrator" / "setup.sh").write_text(setup)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-qm", "init")
    return repo


def _run(tmp_path: Path, repo: Path) -> subprocess.CompletedProcess:
    state = tmp_path / "state.yaml"
    state.write_text("slug: demo\n")
    env = {
        **os.environ,
        "REPO_ROOT": str(repo),
        "CHANGE_ID": "demo",
        "STATE_YAML_PATH": str(state),
        "WORKTREE_BASE_DIR": str(tmp_path / "wt"),
    }
    env.pop("CLAUDE_CODE_REMOTE", None)
    return subprocess.run(["bash", str(_SCRIPT)], env=env, capture_output=True, text=True)


def test_setup_runs_in_new_worktree(tmp_path):
    repo = _repo(tmp_path, 'touch ready; printf %s "$REPO_ROOT" > root\n')
    res = _run(tmp_path, repo)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout.strip().splitlines()[-1])
    wt = Path(out["worktree_path"])
    assert out["created"] is True and (wt / "ready").is_file()
    assert (wt / "root").read_text() == str(repo)


def test_failing_setup_fails_the_step(tmp_path):
    repo = _repo(tmp_path, "exit 3\n")
    res = _run(tmp_path, repo)
    assert res.returncode != 0
    assert json.loads(res.stdout.strip().splitlines()[-1])["reason"] == "setup.sh failed"


def test_no_setup_is_fine(tmp_path):
    res = _run(tmp_path, _repo(tmp_path, None))
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout.strip().splitlines()[-1])["created"] is True


def test_setup_skipped_for_reused_branch(tmp_path):
    """A branch that already exists may hold an earlier run's agent commits."""
    repo = _repo(tmp_path, "touch ready\n")
    _git(repo, "branch", "feature/demo")
    res = _run(tmp_path, repo)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert not (Path(out["worktree_path"]) / "ready").exists()


def test_uncommitted_setup_is_ignored(tmp_path):
    repo = _repo(tmp_path, None)
    (repo / ".orchestrator").mkdir()
    (repo / ".orchestrator" / "setup.sh").write_text("touch ready\n")
    res = _run(tmp_path, repo)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout.strip().splitlines()[-1])
    assert not (Path(out["worktree_path"]) / "ready").exists()
