"""fetch-base: bring the project's default branch up to date before open-pr rebases onto it.

open-pr's agent runs in a sandbox with no network, so it can't fetch. This step runs outside it,
with the pack's GitHub token (lib/forge/github.py), and fetches origin's default branch into
refs/remotes/origin/<default>. It writes pr-base.json for open-pr:
{default_branch, base_ref, base_sha, fetched, reason?}.

No token, or an origin that isn't on GitHub: nothing is fetched (fetched: false, with the reason) and
open-pr rebases onto what the repo already has. That is not a failure; push-pr asks for the token.

Env (from the driver): REPO_ROOT, ORCHESTRATOR_ARTIFACTS_DIR.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib" / "forge"))
import github  # noqa: E402


def local_default(repo: str) -> str:
    ref = github.git(repo, "symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD", check=False)
    if ref.startswith("origin/"):
        return ref.removeprefix("origin/")
    for name in ("main", "master"):
        if github.git(repo, "rev-parse", "-q", "--verify", f"refs/heads/{name}", check=False):
            return name
    return "main"


def main() -> int:
    repo = os.environ.get("REPO_ROOT", "")
    art = os.environ.get("ORCHESTRATOR_ARTIFACTS_DIR", "")
    if not repo or not art:
        return github.emit({"status": "failed", "outputs": {"reason": "REPO_ROOT and ORCHESTRATOR_ARTIFACTS_DIR required"}})

    record: dict = {"fetched": False}
    tok, slug = github.token(), github.repo_slug(repo)
    try:
        github.check_repo_config(repo)
        if not slug:
            record["reason"] = "origin is not a GitHub repo"
        elif not tok:
            record["reason"] = f"no GitHub token at {github.token_file()}"
        else:
            owner, name = slug
            default = github.api(tok, "GET", f"/repos/{owner}/{name}")["default_branch"]
            github.git(
                repo,
                "fetch",
                "--no-tags",
                github.remote_url(owner, name),
                f"+refs/heads/{default}:refs/remotes/origin/{default}",
                env=github.auth_env(tok),
            )
            record.update({"fetched": True, "default_branch": default})
    except github.ForgeError as e:
        record["reason"] = str(e)
    default = record.get("default_branch") or local_default(repo)
    base_ref = f"origin/{default}"
    sha = github.git(repo, "rev-parse", "-q", "--verify", f"refs/remotes/{base_ref}^{{commit}}", check=False)
    if not sha:  # no remote-tracking ref at all: the local default branch is the base
        base_ref = default
        sha = github.git(repo, "rev-parse", "-q", "--verify", f"refs/heads/{default}^{{commit}}", check=False)
    record.update({"default_branch": default, "base_ref": base_ref, "base_sha": sha or None})
    out = Path(art) / "pr-base.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return github.emit({"fetched": record["fetched"], "base": str(out)})


if __name__ == "__main__":
    sys.exit(main())
