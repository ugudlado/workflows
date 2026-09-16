---
name: human-review
description: "After code-review passes, gather human feedback. Approve to ship, or reset the DAG (implement/design/…) with updated tasks. Use when a feature is waiting on human input after review."
user-invocable: true
---

# Human Review

**Intent:** Pause for a human after automated `code-review` passes. Offer
deterministic options (approve / send back to a specific step); the engine
matches a label or option number and routes without re-dispatching this
step. Only genuinely freeform text (no option match) reaches you to
interpret — see the escape-hatch instruction below.

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
   an `ask` and an options list. Always include `approve` and at least the
   `implement` rework option; add `design`/`explore`/`ux-design` options only
   when there's a specific known concern for that layer.

3. **Escape hatch — User direction present but didn't match an offered
   option** (the engine already tried; you're only reached because nothing
   matched). Interpret it:
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
- The escape-hatch instructions only apply when the engine did NOT already
  match User direction to an offered option — that match short-circuits this
  step entirely (advance or reset applied directly, no re-dispatch).
