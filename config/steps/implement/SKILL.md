---
name: developer
description: "Implement pending tasks from tasks.yaml (or derive from ticket context). Use when coding a change, implementing a feature, or executing implementation tasks."
user-invocable: true
---

# Implement Tasks

**Intent:** Work through all pending tasks in `tasks.yaml` in dependency order. Build
ready batches from `depends_on`; independent tasks with disjoint `files` may be
delegated to separate agents concurrently. Shared-file tasks stay serial. Skip tasks
already marked `status: completed`.

## Capability

Before acting, read the installed `developer` skill's `SKILL.md` and use its
implementation rules and named `implementation` result. This file is only the
workflow adapter: it selects pending tasks, supplies file and verification
limits, commits completed work, records task progress, and emits the completion
protocol. Do not use an `extends` prompt.

## Instructions

### Pre-flight

1. Read `design.md` for context: goals, acceptance criteria, component breakdown.
2. **Both `design.md` and `tasks.yaml` absent (patch schema)? Do NOT block or stop** —
   Read `developer/reference/edge-cases.md` before
   proceeding; it tells you to derive work from `ticket-context.md` instead.
   **Only one of the two present** (design.md without tasks.yaml, or vice
   versa) is not the patch case — that's a broken/partial prior run. Do not
   invent scope from the codebase; fail immediately instead:
3. Read `tasks.yaml`. Identify all tasks where `status` is `pending` (or absent).
   Tasks with `status: completed` are done — skip them entirely.
   Reopened tasks (`status: pending` with a non-empty `reviews` list) are in
   scope: treat the latest `reviews[].comment` as the work order for this pass.
4. Resolve execution order: respect `depends_on` — do not start a task until all
   its dependencies have `status: completed`.
5. **Shell capability probe**: before starting the first task, run `git status` and `echo ok` to confirm shell commands are not blocked. If either command fails or is rejected, record the failure in `known_concerns` and fail the step with a reason — do NOT attempt any task. This prevents wasting tool budget on a task loop that cannot commit.

### Per-task loop

For a ready batch, use the available agent delegation mechanism when it can preserve
the task's file scope and verification commands. Give every worker the task id,
declared files, dependencies, and the instruction to return only its implementation
result and `task_updates`. Do not let workers edit `tasks.yaml` directly. If delegation
is unavailable, process the same batch serially; correctness takes precedence over
parallelism.

For each pending task in dependency order:

1. **Read** the task fields: `id`, `title`, `files`, `verify`, `test_scenarios`,
   `change`, `why`.
2. **Read** relevant source files before making changes.
3. **Implement** the change described in `change` (or inferred from `title` and
   `test_scenarios` when `change` is absent).
4. **Cover** all `test_scenarios` with tests.
5. **Verify**: run every command in `verify`. Fix until all pass.
6. **Commit** after all verify commands pass:
   - Message: `<prefix>(<change-id>): <task-id> <task-title>`
     where prefix is `feat` for feature, `fix` for bugfix/fix task, `chore` for
     config/docs-only.
   - Stage only files changed by this task — do NOT `git add -A`.
   - Skip the commit if `git status --porcelain` shows no changes.
   - Include `Co-Authored-By: Claude <noreply@anthropic.com>` trailer.
7. **Return a `task_updates` entry** for this task:
   - `status: completed`
   - `tokens_in: <input tokens used>`
   - `tokens_out: <output tokens used>`
   - `duration_s: <wall-clock seconds from task start to commit>`
     The orchestrator merges it into `tasks.yaml` immediately after committing.
8. Move to the next pending task.

### After all tasks

**All tasks committed and verified** — return:

Hit a non-mainline outcome — zero tasks attempted, or partial progress then an
unrecoverable blocker? Read `developer/reference/edge-cases.md`
for the failed / partial completion forms.

Facing a design contradiction, missing design coverage, or scope ambiguity? See
`developer/reference/edge-cases.md` for returning `status: failed` with a design-input reason.

## Rules

- Work through tasks in dependency order — never start a task whose `depends_on`
  tasks are not yet `status: completed`.
- Touch only the files listed in each task's `files`. If a necessary file is missing
  from the list, note it in `known_concerns` — do NOT modify unlisted files.
- Run every `verify` command before marking a task completed. Fix failures before
  moving on.
- Never edit `tasks.yaml` directly when running in a parallel batch; the recorder owns
  the read-merge-write under its worktree lock.
- When a task removes or renames a sentinel, type, or parameter, grep the same file
  for docstrings or inline comments referencing the old value and update them
  atomically — stale docstrings cap `code_quality` to 7 at phase review.
- `verify` commands are repo-root-relative — run them from `$REPO_ROOT`.
- Never `git add -A` — stage only task files.
- If git commit commands cannot be executed (shell rejected, permission error, or any failure that prevents the commit from landing in HEAD), do NOT mark the task `status: completed` in `{out.tasks}` and do NOT finish the step successfully as if the task landed — record the failure in `known_concerns` AND stop implementation. A task is only complete when its commit is confirmed in `git log`. Claiming completion with uncommitted work causes the phase reviewer to flag a critical finding (CF) that blocks the phase.

## Verify

- All `verify` commands for every completed task pass
- `tasks.yaml` has `status: completed` on every task implemented this pass
- One commit per task exists in git log (unless task produced no file changes)
