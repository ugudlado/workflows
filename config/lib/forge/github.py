"""GitHub access for the pack's exec steps (fetch-base, push-pr). Agents never get here.

The token lives in a file, never in an environment variable or argv: a judgment step's tools can read
another process's environment (/proc/<pid>/environ, same user), but not ~/.config, which the claude
worker denies to both Bash and Read. Default ~/.config/orchestrator/github-token
(ORCH_GITHUB_TOKEN_FILE overrides; keep it under a denied path). A fine-grained token with Contents
and Pull requests read/write on the project repos is enough.

Every git call here runs with the driver's safe git env (no global/system config, no hooks) plus an
Authorization header passed through GIT_CONFIG_* variables, so the token is in neither argv nor a
config file. Before a call that carries it, the repo's own config must hold nothing that could send
it elsewhere (url.*.insteadOf, http.* proxies, remote push URLs, ...): an agent step could have
written the worktree.

ORCH_GITHUB_URL / ORCH_GITHUB_API (default https://github.com, https://api.github.com) exist for tests.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_TOKEN_FILE = "~/.config/orchestrator/github-token"


class ForgeError(RuntimeError):
    pass


def web_base() -> str:
    return os.environ.get("ORCH_GITHUB_URL", "https://github.com").rstrip("/")


def api_base() -> str:
    return os.environ.get("ORCH_GITHUB_API", "https://api.github.com").rstrip("/")


def token_file() -> Path:
    return Path(os.environ.get("ORCH_GITHUB_TOKEN_FILE") or DEFAULT_TOKEN_FILE).expanduser()


def token() -> str | None:
    try:
        t = token_file().read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return t or None


def git(repo: str, *args: str, env: dict | None = None, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, env=env or os.environ.copy())
    if check and r.returncode:
        raise ForgeError(f"git {args[0]} failed: {(r.stderr or r.stdout).strip()[-400:]}")
    return r.stdout.strip()


# Keys in a repo's own config that change where git connects or what it sends.
UNSAFE_KEY = re.compile(
    r"^(url\..*|http\..*|https\..*|remote\..*\.(pushurl|proxy|receivepack|uploadpack|vcs)|core\.gitproxy|"
    r"core\.sshcommand|credential\..*|include\..*|includeif\..*)$"
)


def check_repo_config(repo: str) -> None:
    """Refuse when the repo's local or worktree config could redirect an authenticated request."""
    for scope in ("--local", "--worktree"):
        out = git(repo, "config", scope, "--name-only", "--list", check=False)
        bad = sorted({k for k in out.splitlines() if UNSAFE_KEY.match(k.lower())})
        if bad:
            raise ForgeError(f"the repo's git config sets {', '.join(bad)}; remove them before the run pushes")


def repo_slug(repo: str) -> tuple[str, str] | None:
    """(owner, name) of the repo's origin on GitHub, or None when origin is elsewhere or missing."""
    # The raw config value: `remote get-url` applies url.*.insteadOf, which check_repo_config refuses anyway.
    url = git(repo, "config", "--get", "remote.origin.url", check=False)
    if not url:
        return None
    base = web_base()
    host = re.sub(r"^[a-z]+://", "", base)
    for pattern in (
        re.escape(base) + r"/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"^(?:ssh://)?git@" + re.escape(host) + r"[:/]([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"^https://(?:[^@/]+@)?" + re.escape(host) + r"/([^/]+)/([^/]+?)(?:\.git)?/?$",
    ):
        m = re.match(pattern, url)
        if m:
            return m.group(1), m.group(2)
    return None


def remote_url(owner: str, name: str) -> str:
    return f"{web_base()}/{owner}/{name}.git"


def auth_env(tok: str) -> dict:
    """The environment for an authenticated git call: the safe env the driver set, plus the header."""
    env = os.environ.copy()
    n = int(env.get("GIT_CONFIG_COUNT") or 0)
    basic = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    env.update(
        {
            "GIT_CONFIG_COUNT": str(n + 2),
            f"GIT_CONFIG_KEY_{n}": f"http.{web_base()}/.extraHeader",
            f"GIT_CONFIG_VALUE_{n}": f"Authorization: Basic {basic}",
            f"GIT_CONFIG_KEY_{n + 1}": "core.hooksPath",  # the driver sets this too; hold it when run alone
            f"GIT_CONFIG_VALUE_{n + 1}": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        }
    )
    return env


def api(tok: str, method: str, path: str, body: dict | None = None) -> object:
    req = urllib.request.Request(
        api_base() + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        raise ForgeError(f"GitHub {method} {path}: HTTP {e.code} {detail}") from e
    except urllib.error.URLError as e:
        raise ForgeError(f"GitHub {method} {path}: {e.reason}") from e


def emit(obj: dict) -> int:
    print(json.dumps(obj))
    return 0


def ask(question: str) -> int:
    """A question for the human (the engine's await_input); the step re-runs with the answer."""
    return emit({"status": "await_input", "outputs": {"ask": question}})
