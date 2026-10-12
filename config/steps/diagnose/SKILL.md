---
name: diagnose
description: "Diagnose a bug and write a diagnosis brief. Use when investigating failures, root-causing bugs, or starting a bugfix."
user-invocable: true
---

# Diagnose

**Intent:** Reproduce a reported defect, trace it to an exact root cause, and
persist a diagnosis brief, then plan the fix (design.md + tasks.yaml) in the
same pass.

## Capability

Before acting, read the installed `explorer` skill's `SKILL.md` and use its
read-only investigation rules and named `diagnosis` result. This file is only
the workflow adapter: it supplies ticket context and diagnosis format,
persists the result, and emits the completion protocol. Do not use an
`extends` prompt.

## Diagnose-flavored scenarios (bug tickets, root cause)

If the surrounding task is a bug diagnosis (ticket + reproduce + trace + document):

- Read `{in.ticket}` (or `{in.ticket}`) first. Do not invent a different bug from the
  code.
- Reproduction MUST be a runnable command or minimal script (e.g. a `repro.js`
  or `repro.py`) with copy-pasteable code and captured expected-vs-actual
  output — not a prose description.
- If ticket repro steps do not fail, investigate why before marking
  unreproducible: diff runtime/dependency versions, `git log` since the ticket
  date for silent fixes, re-read the ticket for implicit preconditions
  (feature flags, DB state, timezone, locale, data shape), run with verbose
  logging, and read the implicated code path to check whether the defect is
  latent even without a live failure.
- Root cause must name the EXACT `file:line` where behavior diverges, with the
  expression and why it is wrong. Common patterns to check: wrong type check
  (`isinstance` vs `type()`), missing edge case, incorrect string/path
  manipulation, off-by-one, stale state, UTC/local date conversion, silent
  double-conversion.
- Keep `discovery.md` free of fix proposals: the fix belongs in `design.md`
  (see "Plan the fix"), not in the diagnosis.
- Pattern-based bugs: search the ENTIRE source tree (including gitignored
  source dirs), cross-check the affected-site count with
  `find … | xargs grep … | wc -l`. If fresh count differs from an earlier
  count, update Impact to use the fresh count; if >20% different, investigate
  the discrepancy before proceeding.
- Before writing `discovery.md`, Read
  `diagnose/reference/diagnosis-format.md` for
  the required section structure and field rules. The document has sections:
  Symptoms, Reproduction Steps, Expected vs Actual, Investigation (Evidence
  Gathered + Data Flow Trace), Root Cause (file + line + why), Impact
  (Severity + Affected Areas + Since When), Linear Ticket. List unresolved
  questions explicitly.
- Write the artifact to `{out.discovery}` — do not return diagnosis prose in
  chat. The file is the artifact.

## Plan the fix

After `discovery.md` is written, produce `{out.design}` and `{out.tasks}` in
this same spawn (this step replaced the separate bugfix design and
design-review steps; the `design-signoff` gate is the only review).

- Read the `designer` skill's `SKILL.md` for design rules (as `design` does).
  Skip the 2-3 approach exploration: pick the smallest fix that addresses the
  root cause; note rejected alternatives in one line each under Trade-offs.
  Report the chosen approach's `complexity` (XS/S/M/L/XL) as the declared
  `complexity` output.
- design.md: Read `../design/reference/design-format.md` and start from
  `../design/templates/feature/design.md` (use `bugfix-id` in the frontmatter
  in place of `feature-id`; Context is the root cause from `discovery.md`).
  Acceptance criteria must be testable and trace to the reproduction.
- tasks.yaml: Read `../design/reference/tasks-format.md` and start from
  `../design/templates/bugfix/tasks.yaml`. First task MUST be the regression
  test (the reproduction), second task MUST be the fix. Fewest tasks that
  cover every AC; verify commands repo-root-relative with no absolute paths;
  no `model:` field; every task's verify must be satisfiable from its `files`
  plus its `depends_on` chain. RED tasks must exit 0 at commit time (pytest
  `xfail(strict=False)`, Bun `test.todo`, Vitest/Jest `it.todo`), stated in
  the task's `change:`.
- Validate: `bash ../design/validate-tasks-yaml.sh {out.tasks}` must pass.
- Verify design claims about data shapes, call sites, and field names against
  live code (grep) before finalizing.
- Do not pause for human review; `design-signoff` shows `design.md` and
  `tasks.yaml`. On regeneration after a rejection, address the reviewer's
  feedback in the artifacts.

## Anti-patterns (what makes an Explorer response fail at staff level)

- All-methodology, no-artifact: describing what you would search for without
  producing the concrete report / file:line / call chain the role owes.
- Placeholder commands (`grep <keyword> <file>`) instead of real commands with
  real flags and paths.
- Root cause as hypothesis ("likely a UTC conversion in the formatter")
  without a specific `file:line` and the exact expression.
- Repro as prose instead of runnable code.
- Raw finding lists instead of severity-classified tables.
- Silent overclaim: "all callers validate" without having grepped for
  repository-layer bypasses (bulk jobs, migrations, admin scripts).
- Hidden gaps: presenting an incomplete scan as complete. Always name what you
  did not check and the search that would close it.
- Plan-by-assumption: tasks.yaml or design.md that restate the symptom
  instead of the root-cause `file:line`, or that skip the regression-test-first
  ordering.
