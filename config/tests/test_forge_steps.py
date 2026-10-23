"""fetch-base and push-pr: the exec steps that reach GitHub with the pack's token, so no agent has to.

A bare repo stands in for GitHub's git side (ORCH_GITHUB_URL=file://...) and a local HTTP server for its
API (ORCH_GITHUB_API), so the steps run their real git and HTTP code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

STEPS = Path(__file__).resolve().parents[1] / "steps"
TOKEN = "ghp_test_token"


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
             "GIT_COMMITTER_EMAIL": "t@t"},
    ).stdout.strip()


class FakeGitHub(BaseHTTPRequestHandler):
    pulls: list[dict] = []
    calls: list[tuple[str, str, dict | None, str]] = []

    def _reply(self, code: int, body: object) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        self.calls.append(("GET", self.path, None, self.headers.get("Authorization", "")))
        if self.path == "/repos/o/r":
            return self._reply(200, {"default_branch": "main"})
        if self.path.startswith("/repos/o/r/pulls"):
            return self._reply(200, self.pulls)
        return self._reply(404, {"message": "Not Found"})

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.calls.append(("POST", self.path, body, self.headers.get("Authorization", "")))
        pr = {"number": 7, "html_url": "https://github.com/o/r/pull/7", **body}
        self.pulls.append(pr)
        return self._reply(201, pr)

    def log_message(self, *a):  # quiet
        pass


@pytest.fixture
def gh(tmp_path):
    FakeGitHub.pulls, FakeGitHub.calls = [], []
    server = HTTPServer(("127.0.0.1", 0), FakeGitHub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def run(tmp_path, gh):
    """A project repo whose origin is the bare 'GitHub' repo o/r, a run worktree on its branch, a run dir."""
    remote = tmp_path / "gh"
    bare = remote / "o" / "r.git"
    bare.mkdir(parents=True)
    git(bare, "init", "-q", "--bare", "-b", "main")
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("hi\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "init")
    git(repo, "remote", "add", "origin", f"file://{bare}")
    git(repo, "push", "-q", "origin", "main")
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", "-b", "feature/r1", str(wt))
    (wt / "a.txt").write_text("change\n")
    git(wt, "add", ".")
    git(wt, "commit", "-qm", "change")
    rundir = tmp_path / "run"
    art = rundir / "artifacts"
    art.mkdir(parents=True)
    (rundir / "state.yaml").write_text(json.dumps({"branch": "feature/r1", "worktree_path": str(wt)}))
    tokfile = tmp_path / "home" / ".config" / "orchestrator" / "github-token"
    tokfile.parent.mkdir(parents=True)
    tokfile.write_text(TOKEN + "\n")
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith(("ORCH", "GIT_"))},
        "HOME": str(tmp_path / "home"),
        "REPO_ROOT": str(repo),
        "WORKTREE_PATH": str(wt),
        "STATE_YAML_PATH": str(rundir / "state.yaml"),
        "ORCHESTRATOR_ARTIFACTS_DIR": str(art),
        "ORCH_GITHUB_URL": f"file://{remote}",
        "ORCH_GITHUB_API": gh,
    }
    return {"repo": repo, "wt": wt, "art": art, "bare": bare, "env": env, "tokfile": tokfile}


def step(name: str, env: dict) -> dict:
    py = STEPS / name / f"{name.replace('-', '_')}.py"
    r = subprocess.run([sys.executable, str(py)], capture_output=True, text=True, env=env, check=False)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert TOKEN not in r.stdout + r.stderr
    return out


PR_MD = "# Add a.txt\n\n## Summary\nAdds a.txt.\n"


def test_fetch_base_fetches_the_default_branch(run):
    # GitHub's main moves on after the run started.
    other = run["bare"].parent / "other"
    git(run["bare"].parent, "clone", "-q", str(run["bare"]), str(other))
    (other / "b.txt").write_text("b\n")
    git(other, "add", ".")
    git(other, "commit", "-qm", "upstream")
    git(other, "push", "-q", "origin", "main")
    out = step("fetch-base", run["env"])
    assert out["fetched"] is True
    base = json.loads((run["art"] / "pr-base.json").read_text())
    assert base["base_ref"] == "origin/main" and base["default_branch"] == "main"
    assert base["base_sha"] == git(other, "rev-parse", "HEAD") == git(run["repo"], "rev-parse", "origin/main")
    assert all(c[3] == f"Bearer {TOKEN}" for c in FakeGitHub.calls)


def test_fetch_base_without_a_token_uses_what_the_repo_has(run):
    run["tokfile"].unlink()
    out = step("fetch-base", run["env"])
    base = json.loads((run["art"] / "pr-base.json").read_text())
    assert out["fetched"] is False and "no GitHub token" in base["reason"]
    assert base["base_sha"] == git(run["repo"], "rev-parse", "main")
    assert FakeGitHub.calls == []


def test_push_pr_pushes_and_opens_the_pr(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    out = step("push-pr", run["env"])
    assert out["pr_urls"] == "https://github.com/o/r/pull/7"
    assert out["state_patch"] == {"pr_url": "https://github.com/o/r/pull/7"}
    assert git(run["bare"], "rev-parse", "feature/r1") == git(run["wt"], "rev-parse", "HEAD")
    post = [c for c in FakeGitHub.calls if c[0] == "POST"]
    assert len(post) == 1 and post[0][2] == {
        "title": "Add a.txt", "body": "## Summary\nAdds a.txt.\n", "head": "feature/r1", "base": "main"}
    assert "Pull request: https://github.com/o/r/pull/7" in (run["art"] / "pr.md").read_text()


def test_push_pr_rerun_after_a_rebase_updates_the_branch_and_reuses_the_pr(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    step("push-pr", run["env"])
    git(run["wt"], "commit", "-q", "--amend", "-m", "change, reworded")  # history rewritten, as by a rebase
    out = step("push-pr", run["env"])
    assert out["pr_urls"] == "https://github.com/o/r/pull/7"
    assert git(run["bare"], "rev-parse", "feature/r1") == git(run["wt"], "rev-parse", "HEAD")
    assert len([c for c in FakeGitHub.calls if c[0] == "POST"]) == 1
    assert (run["art"] / "pr.md").read_text().count("Pull request: ") == 1


def test_push_pr_without_a_token_asks(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    run["tokfile"].unlink()
    out = step("push-pr", run["env"])
    assert out["status"] == "await_input" and "No GitHub token" in out["outputs"]["ask"]
    assert FakeGitHub.calls == [] and not git(run["bare"], "branch", "--list", "feature/r1")


def test_push_pr_takes_a_pr_opened_by_hand(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    run["tokfile"].unlink()
    env = {**run["env"], "ORCHESTRATOR_USER_ANSWER": "done: https://github.com/o/r/pull/12 thanks"}
    out = step("push-pr", env)
    assert out["pr_urls"] == "https://github.com/o/r/pull/12"
    assert "Pull request: https://github.com/o/r/pull/12" in (run["art"] / "pr.md").read_text()


@pytest.mark.parametrize(
    "key,value",
    [("url.https://evil.example/.insteadOf", "file://"), ("http.proxy", "http://evil.example:8080"),
     ("remote.origin.pushurl", "https://evil.example/x.git"), ("include.path", "/tmp/x")],
)
def test_push_pr_refuses_repo_config_that_could_redirect_the_token(run, key, value):
    (run["art"] / "pr.md").write_text(PR_MD)
    git(run["repo"], "config", key, value)
    out = step("push-pr", run["env"])
    assert out["status"] == "await_input" and key.lower() in out["outputs"]["ask"].lower()
    assert not git(run["bare"], "branch", "--list", "feature/r1")


def test_push_pr_only_pushes_the_run_branch(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    git(run["wt"], "checkout", "-q", "-b", "elsewhere")
    out = step("push-pr", run["env"])
    assert out["status"] == "await_input" and "not the run branch" in out["outputs"]["ask"]


def test_push_pr_needs_a_title_line(run):
    (run["art"] / "pr.md").write_text("no title here\n")
    out = step("push-pr", run["env"])
    assert out["status"] == "await_input" and "# <title>" in out["outputs"]["ask"]


def test_push_pr_asks_when_origin_is_not_github(run):
    (run["art"] / "pr.md").write_text(PR_MD)
    git(run["repo"], "remote", "set-url", "origin", "https://gitlab.example/o/r.git")
    out = step("push-pr", run["env"])
    assert out["status"] == "await_input" and "not a GitHub repo" in out["outputs"]["ask"]


def test_fetch_base_refuses_repo_config_that_could_redirect_the_token(run):
    git(run["repo"], "config", "http.proxy", "http://evil.example:8080")
    out = step("fetch-base", run["env"])
    base = json.loads((run["art"] / "pr-base.json").read_text())
    assert out["fetched"] is False and "http.proxy" in base["reason"] and FakeGitHub.calls == []
