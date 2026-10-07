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

# `feature` complete phase

`feature` ends in a pull request, not a local merge: gate `pr-signoff` →
`mark-change-completed` → `open-pr` (requires `merge_token`) →
`workflow-report`. `open-pr` pushes the branch and runs `gh pr create`; it
never merges. The worktree is kept for review fixes, `spec/changes/` is not
archived into the branch, and `ticket-done` is not run — the ticket is done
when the PR merges. The merge/teardown steps remain in `complete.yaml` and
`feature-remote.yaml`.
