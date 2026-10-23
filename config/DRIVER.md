# Scenario-learning artifact handoff

Learning runs in its own nightly `learn` workflow (see below), not inside
dev/feature/bugfix. For `learn`, substitute `{out.proposed_scenarios}` with
`payload.out.proposed_scenarios` and `{in.runs}` with `payload.in.runs`. Write
proposals only to the out path, not beside the driver's state file unless those
paths happen to coincide.

Artifacts live outside the worktree. The driver must pass
`--artifacts-dir <abs run dir>/artifacts` on every `next` call: the pack
requires `ORCHESTRATOR_ARTIFACTS_DIR` (exec steps fail without it)
and no workflow declares `artifacts_root`. Artifacts go to `payload.out` /
`$ORCHESTRATOR_ARTIFACTS_DIR`; code goes to `$WORKTREE_PATH`. Never derive one
from the other.

For `persist-learnings` (a step of the `learn` workflow), run
`payload.run_path` with argv
`["--proposed-scenarios", payload.in.proposed_scenarios]` and the normal
`payload.env`. The path is absolute, so cwd is irrelevant. Pass it even when the
optional file is absent: absence is a no-op, not a stub or a search of other
runs. The explicit argument is authoritative. State-environment discovery
remains only for legacy direct script callers that omit the argument.

A proposal's `step_id` may name any step in the pack that has a charter
(`steps/<id>/SKILL.md`); `persist-learnings` falls back to the pack's prompt
roots (`ORCHESTRATOR_PROMPT_PATH`) when the id is not in
`ORCHESTRATOR_PROMPT_DIRS`, and the append stays confined to those roots.

# Nightly `learn` workflow

`dev`, `feature` and `bugfix` no longer learn inline. A scheduler on the runner
VM runs the `learn` workflow once a night (it has no ticket, worktree or
gates): `collect-runs` → `learn` → `persist-learnings` → `mark-learned`.

- **Runs root**: `ORCHESTRATOR_RUNS_DIR` if set, else
  `Path(STATE_YAML_PATH).parent.parent` (runs live at
  `.orchestrator/runs/<slug>/state.yaml`). Pass the env on the `next` calls'
  step environment, or give the learn run a `STATE_YAML_PATH` inside the same
  runs root.
- `collect-runs`: run `payload.run_path` with argv
  `["--runs-out", payload.out.runs]`. It lists runs whose `step_history` holds a
  completed `workflow-report` (the same "finished" fact as `check-rerun`), that
  have no `learned.json` marker in their run dir, and that are not the current
  learn run or any run of the `learn` workflow. It writes `runs.json`
  (`[{slug, run_dir, state_path, artifacts_dir, finished_at}]`) and outputs
  `run_count`. Zero runs is success; `learn` then reports `learn_skipped`.
- `learn` reads every run listed in `payload.in.runs` and looks for patterns
  that repeat across runs.
- `mark-learned`: run `payload.run_path` with argv
  `["--runs", payload.in.runs]` (absent or empty is a no-op; optionally
  `--scenarios-appended N`, the `persist-learnings` count). It writes
  `<run_dir>/learned.json` (`{learned_at, learn_run, scenarios_appended?}`) for
  each listed run and outputs `marked`. Idempotent: an existing marker is never
  rewritten. To make a run eligible again, delete its `learned.json`.

# `feature` / `bugfix` complete phase

Both end in a pull request, not a local merge: gate `pr-signoff` →
`mark-change-completed` → `open-pr` (requires `merge_token`) →
gate `pr-merged` → `remove-worktree` → `workflow-report`.
`open-pr` pushes the branch and runs `gh pr create`; it never merges. The run
then waits at `pr-merged`: the worktree stays for review fixes until the PR
merges. Approve the gate only once the PR is merged (`gh pr view --json state`
= `MERGED`); `remove-worktree` force-removes the worktree. Run artifacts are
never committed to the branch, and there is no archive step — the run dir is
the archive.

`check-rerun` stops a slug whose run already finished (exits non-zero, so the
engine answers `needs_you`): its `step_history` has a completed
`workflow-report`. Start over by deleting the run dir.

# Tickets

Workflows read the ticket and never move it: the tracker does that itself
(Linear moves an issue when a branch or PR names its id). Use the ticket id as
the run's slug so the branch carries it. the branch is
`<type>/<slug>`: dev's `name-branch` renames it `feature/`, `fix/` or `chore/`
from triage's call; feature and bugfix keep the workflow's name; `open-pr` also links
the ticket in the PR body.

`load-ticket-context` is a judgment step. It picks the ticketing tool itself by
inspecting the tools its subagent has (issue tracker MCP tools, the git forge's
CLI, the pack's backlog helper) following `lib/ticket/TICKETING.md`. The driver
passes nothing special: no ticketing env, no ticket id.

`load-ticket-context`: the run's input is the user's message. Pass it to the
subagent in the brief as `User direction: <text>`; there is no state input. The
step writes `ticket-context.md` and, for a real ticket id, `ticket.json`
(`{"ticket_id": "ORC-123", "tracker": "<tool used>", "url": "..."}`) in the
artifacts dir. On `ticket_context_status: await_input`, relay the `ask` and
re-run the step with the answer as the new `User direction`.

# Worktree setup and environment blockers

A fresh worktree has none of a repo's untracked setup (node_modules, a venv,
sibling checkouts its build expects), and judgment steps run in a sandbox with
no network, so they cannot install any of it. `create-worktree` runs the repo's
committed `.orchestrator/setup.sh`, if present, once in the new worktree,
outside the sandbox and with network, with `REPO_ROOT` set to the main checkout.
Because it runs unsandboxed, it is read from the commit the worktree branched
from (never the working tree) and runs only when the branch is new: a reused
branch may hold an earlier run's agent commits. That commit is only as trusted
as the main checkout's refs: the self-hosted driver's sandbox denies agents
writes to its `HEAD`, current branch ref and `packed-refs`; another driver must
do the same. Treat `setup.sh` like a committed git hook: it runs with the
driver user's environment and network. A non-zero exit removes the new worktree and branch, so a retry
starts clean, and fails the step. Consumers commit it next to their bindings:

```gitignore
.orchestrator/*
!.orchestrator/bindings.yaml
!.orchestrator/setup.sh
```

An environment blocker (commit signing that the sandbox cannot reach, a missing
dependency, a check the sandbox blocks) is not a code failure: `implement`
reports `outcome: await_input` and `code-review` reports `verdict: await_input`,
each with an `ask` naming the blocker. Relay it like any other question; failing
instead would send the run back to design or implement, which cannot fix the
machine.
