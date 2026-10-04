---
name: human-review
description: "After code-review passes, gather human feedback. Approve to ship, or reset the DAG (implement/design/…) with updated tasks. Use when a feature is waiting on human input after review."
user-invocable: true
---

# Human Review

**Intent:** Pause for a human after automated `code-review` passes. Offer
deterministic options (approve / send back to a specific step). Every human
reply returns to you as User direction on a re-run of this step; you interpret
it — see step 3.

## Context

- Upstream: `code-review` passed (see `{in.code_review}` and `{out.tasks}`).
- Resume text arrives as **User direction** in the prompt (CLI:
  `orchestrator feature <ticket> "<text>"`). Empty direction means first ask.
- Prefer reading the existing review artifacts over guessing.

## Allowed `reset_to` targets (feature workflow)

Only emit a step id that exists on this workflow:

`explore` · `ux-design` · `design` · `implement`

## Instructions

1. **Load context** — Skim `{in.code_review}` (or the step_history summary)
   and `{out.tasks}`. Note what passed and what is still open.

2. **First ask (no User direction yet)** — Report `decision: await_input` with
   an `ask` and an options list. Reporting `await_input` stops the run; the
   driver relays `ask` to the user and re-runs you with their answer as User
   direction. Always include `approve` and at least the
   `implement` rework option; add `design`/`explore`/`ux-design` options only
   when there's a specific known concern for that layer.

3. **User direction present (from the driver's brief)** — interpret it:
   - Exactly an offered option label or number (e.g. "implement", "2") →
     apply that option directly (approve, or rework with that `reset_to`);
     never re-ask.
   - Clearly approval-shaped (ship / approve / LGTM / merge / "looks good") →
     report `decision: approved`.
   - Describes concrete rework → update `{out.tasks}` (add/reopen tasks with
     the feedback in `reviews[]`) and, if design/AC changed, update the design
     too. Report `decision: rework` with `reset_to` set to the earliest step
     that must re-run and a reason summarizing the ask.
   - Still unclear → report `decision: await_input` again with a clarifying
     `ask` and the same (or narrowed) options list. Do not guess `reset_to`.

## Rules

- Prefer `await_input` over guessing approval.
- Always set `reset_to` on a `rework` decision (otherwise the workflow falls
  back to the static `on_failure: implement` edge).
- Never `reset_to` a step after `human-review` in the DAG.
