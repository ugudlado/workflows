"""push-pr: push the run branch and open its pull request, with a token no agent can read.

open-pr's agent writes pr.md (first line `# <title>`, then the body) but has no network and no
credentials. This step runs outside the sandbox with the pack's GitHub token (lib/forge/github.py):

1. Push the run branch (the one checked out in the run's worktree) to origin on GitHub. A branch the
   run pushed before is updated with --force-with-lease against what GitHub has now, since open-pr
   rebases. A local `pr-assets` branch (open-pr's screenshots) is pushed too.
2. Find the branch's open PR, or create one against the default branch from pr.md.
3. Put the PR's link at the top of pr.md (the pr-merged gate shows it) and return pr_urls.

Anything that stops it (no token, origin not on GitHub, a forge binding for another provider, a
GitHub error) is a question, not a failure: the run waits, and the answer re-runs this step. An
answer holding a GitHub pull request URL (a PR opened by hand) completes the step with that URL.

Env (from the driver): REPO_ROOT, WORKTREE_PATH, STATE_YAML_PATH, ORCHESTRATOR_ARTIFACTS_DIR,
ORCHESTRATOR_USER_ANSWER (on a re-run after a question), ORCHESTRATOR_BINDINGS.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib" / "forge"))
import github  # noqa: E402

BY_HAND = "Push the branch and open the PR yourself, then answer with its URL."


def pr_url_in(answer: str) -> str | None:
    m = re.search(r"https://[^/\s]+/[^/\s]+/[^/\s]+/pull/\d+", answer or "")
    return m.group(0) if m else None


def title_and_body(text: str) -> tuple[str, str]:
    lines = text.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise github.ForgeError("pr.md must start with a `# <title>` line")
    return lines[0][2:].strip(), "\n".join(lines[1:]).strip() + "\n"


def with_link(text: str, url: str) -> str:
    lines = [ln for ln in text.splitlines() if not ln.startswith("Pull request: ")]
    return "\n".join([*lines[:1], "", f"Pull request: {url}", *lines[1:]]).replace("\n\n\n", "\n\n") + "\n"


def run_branch(worktree: str, state_path: str) -> str:
    state = (yaml.safe_load(Path(state_path).read_text(encoding="utf-8")) or {}) if state_path else {}
    want = str(state.get("branch") or "")
    head = github.git(worktree, "symbolic-ref", "-q", "--short", "HEAD", check=False)
    if not want or head != want:
        raise github.ForgeError(f"the worktree is on '{head}', not the run branch '{want}'")
    return want


def remote_sha(repo: str, url: str, ref: str, env: dict) -> str:
    out = github.git(repo, "ls-remote", url, f"refs/heads/{ref}", env=env)
    return out.split()[0] if out else ""


def push(repo: str, url: str, branch: str, env: dict) -> None:
    seen = remote_sha(repo, url, branch, env)
    lease = f"--force-with-lease=refs/heads/{branch}:{seen}"
    github.git(repo, "push", "--no-verify", lease, url, f"refs/heads/{branch}:refs/heads/{branch}", env=env)


def main() -> int:
    art = Path(os.environ.get("ORCHESTRATOR_ARTIFACTS_DIR", ""))
    pr_md = art / "pr.md"
    answer = os.environ.get("ORCHESTRATOR_USER_ANSWER", "")
    by_hand = pr_url_in(answer)
    if by_hand:
        if pr_md.is_file():
            pr_md.write_text(with_link(pr_md.read_text(encoding="utf-8"), by_hand), encoding="utf-8")
        return github.emit({"pr_urls": by_hand, "state_patch": {"pr_url": by_hand}})

    forge = (json.loads(os.environ.get("ORCHESTRATOR_BINDINGS") or "{}") or {}).get("forge") or {}
    if forge and forge.get("provider") != "github":
        return github.ask(f"push-pr only opens GitHub PRs; this repo's forge binding is {forge.get('provider')}. {BY_HAND}")

    repo = os.environ.get("REPO_ROOT", "")
    worktree = os.environ.get("WORKTREE_PATH") or repo
    try:
        github.check_repo_config(repo)
    except github.ForgeError as e:
        return github.ask(f"push-pr won't send the token: {e}. Then answer anything to retry, or: {BY_HAND}")
    slug, tok = github.repo_slug(repo), github.token()
    if not slug:
        return github.ask(f"origin of {repo} is not a GitHub repo, so the run can't open a PR. {BY_HAND}")
    if not tok:
        return github.ask(
            f"No GitHub token at {github.token_file()}. Add one (Contents and Pull requests read/write on "
            f"{slug[0]}/{slug[1]}) and answer anything to retry, or: {BY_HAND}"
        )
    try:
        title, body = title_and_body(pr_md.read_text(encoding="utf-8"))
        branch = run_branch(worktree, os.environ.get("STATE_YAML_PATH", ""))
        owner, name = slug
        url, env = github.remote_url(owner, name), github.auth_env(tok)
        push(repo, url, branch, env)
        if github.git(repo, "rev-parse", "-q", "--verify", "refs/heads/pr-assets", check=False):
            push(repo, url, "pr-assets", env)
        found = github.api(tok, "GET", f"/repos/{owner}/{name}/pulls?state=open&head={owner}:{branch}")
        if found:
            pr = found[0]
        else:
            default = github.api(tok, "GET", f"/repos/{owner}/{name}")["default_branch"]
            pr = github.api(
                tok,
                "POST",
                f"/repos/{owner}/{name}/pulls",
                {"title": title, "body": body, "head": branch, "base": default},
            )
    except (github.ForgeError, OSError, KeyError, TypeError) as e:
        return github.ask(f"push-pr could not open the PR: {e}. Fix it and answer anything to retry, or: {BY_HAND}")
    link = pr["html_url"]
    pr_md.write_text(with_link(pr_md.read_text(encoding="utf-8"), link), encoding="utf-8")
    return github.emit({"pr_urls": link, "state_patch": {"pr_url": link}})


if __name__ == "__main__":
    sys.exit(main())
