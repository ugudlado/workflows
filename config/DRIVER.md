# Scenario-learning artifact handoff

For `learn`, substitute `{out.proposed_scenarios}` with
`payload.out.proposed_scenarios`. Write proposals only there, not beside the
driver's state file unless those paths happen to coincide.

For `persist-learnings`, run `payload.run_path` with argv
`["--proposed-scenarios", payload.in.proposed_scenarios]` and the normal
`payload.env`, with cwd = `WORKTREE_PATH`. The engine's input path is relative
to that cwd and includes the workflow's artifact root. Pass it even when the
optional file is absent: absence is a no-op, not a stub or a search of other
runs. The explicit argument is authoritative. State-environment discovery
remains only for legacy direct script callers that omit the argument.

# `feature` / `bugfix` complete phase

Both end in a pull request, not a local merge: gate `pr-signoff` →
`mark-change-completed` → `open-pr` (requires `merge_token`) →
gate `pr-merged` → `remove-worktree` → `ticket-done` → `workflow-report`.
`open-pr` pushes the branch and runs `gh pr create`; it never merges. The run
then waits at `pr-merged`: the worktree stays for review fixes until the PR
merges. Approve the gate only once the PR is merged (`gh pr view --json state`
= `MERGED`); `remove-worktree` force-removes the worktree. `spec/changes/` is
never archived into the branch — an archive commit would land on the merged
branch and be lost.
