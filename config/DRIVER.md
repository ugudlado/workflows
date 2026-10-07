# Scenario-learning artifact handoff

For `learn`, substitute `{out.proposed_scenarios}` with
`payload.out.proposed_scenarios`. Write proposals only there, not beside the
driver's state file unless those paths happen to coincide.

Artifacts live outside the worktree. The driver must pass
`--artifacts-dir <abs run dir>/artifacts` on every `next` call: the pack
requires `ORCHESTRATOR_ARTIFACTS_DIR` (exec steps fail without it)
and no workflow declares `artifacts_root`. Artifacts go to `payload.out` /
`$ORCHESTRATOR_ARTIFACTS_DIR`; code goes to `$WORKTREE_PATH`. Never derive one
from the other.

For `persist-learnings`, run `payload.run_path` with argv
`["--proposed-scenarios", payload.in.proposed_scenarios]` and the normal
`payload.env`. The path is absolute, so cwd is irrelevant. Pass it even when the
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
= `MERGED`); `remove-worktree` force-removes the worktree. Run artifacts are
never committed to the branch, and there is no archive step — the run dir is
the archive.

`check-rerun` stops a slug whose run already finished (exits non-zero, so the
engine answers `needs_you`): its `step_history` has a completed
`workflow-report`. Start over by deleting the run dir.

# Ticket steps (judgment)

`load-ticket-context`, `ticket-start`, `ticket-review`, `ticket-qa`,
`ticket-rework` and `ticket-done` are all judgment steps. They pick the
ticketing tool themselves by inspecting the tools their subagent has (issue
tracker MCP tools, the git forge's CLI, the pack's backlog helper) following
`lib/ticket/TICKETING.md`. The driver passes nothing special: no ticketing env,
no status mapping, no ticket id.

`load-ticket-context`: the run's input is the user's message. Pass it to the
subagent in the brief as `User direction: <text>`; there is no state input. The
step writes `ticket-context.md` and, for a real ticket id, `ticket.json`
(`{"ticket_id": "ORC-123", "tracker": "<tool used>", "url": "..."}`) in the
artifacts dir. On `ticket_context_status: await_input`, relay the `ask` and
re-run the step with the answer as the new `User direction`.

The status steps take `ticket.json` as the optional `in.ticket_ref`; absent, they
report `skipped (no ticket)`. A failed tracker update fails the step.
