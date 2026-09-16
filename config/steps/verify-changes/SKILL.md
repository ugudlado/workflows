---
name: verify-changes
description: "Verify the implemented changes satisfy the requirement. Use after implementation to confirm every acceptance criterion is actually in place on the run branch before the workflow advances."
user-invocable: true
---

# Verify Changes

**Intent:** Confirm the work exists and matches the requirement — not who did
it or how it arrived. Transport concerns (message signatures, agent identity)
are handled before this step ever runs; you judge the changes only.

## Verifier

You check the run branch against the requirement and own the verdict.

### Rules

- Verify against the requirement artifacts, not the conversation: the ticket
  context (`{in.ticket}` when present) and the
  design's acceptance criteria (`{in.design}`).
- Evidence over claims: for every acceptance criterion, point at the concrete
  code or test on the branch that satisfies it. "The reply said it's done" is
  not evidence.
- Run the project's own checks when they exist (test suite, lint, build) and
  report real output, never assumed results.
- A partially met requirement is `needs_work`, with the unmet items listed —
  do not average a verdict.

## Steps

1. Fetch the branch; if it does not exist or has no commits beyond base,
   report `verdict: needs_work` (reason: no changes delivered).
2. Build the checklist: acceptance criteria from `{in.design}`, else tasks from
   `{in.tasks}`, else the ticket's stated outcome.
3. For each item, locate the satisfying change in the diff (file + what it
   does) or the test that proves it. Note items with no evidence.
4. Run the project's verification commands when present (e.g. the test
   suite). Capture pass/fail and the failing output when any.
5. Write the evidence table to `{out.verification}`.
6. Report `verdict: pass` only when every checklist item has evidence and the
   project checks pass; otherwise `verdict: needs_work`, with the unmet items
   and failing output recorded in `{out.verification}`.

## Verify

- Every acceptance criterion maps to a concrete diff hunk or test, cited.
- Project checks were actually executed (output quoted), or their absence
  stated.
- The verdict lists unmet items explicitly when failing.
