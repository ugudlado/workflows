---
name: ticket-review
description: "Move the run's ticket to in review using the tracker recorded in ticket.json. Skips when the run has no ticket."
user-invocable: true
---

# Ticket Review

**Intent:** Set the run's ticket to the closest "in review" state its tracker
has. Tracker choice and lookup rules live in `<pack>/lib/ticket/TICKETING.md`
(`<pack>` is the directory two levels above `$ORCHESTRATOR_STEP_DIR`).

## Verify

- With no `{in.ticket_ref}`, nothing was touched and the report says skipped.
- Otherwise the ticket's state in the tracker, re-read after the update, is the
  target state (or already was).

## Instructions

1. No `{in.ticket_ref}`: report `completed` with
   `ticket_status_set: skipped (no ticket)`. Stop.
2. Read `TICKETING.md` and use the tracker named in `ticket.json`. If it names
   none, follow the guide to find one; if none resolves the id, report
   `completed` with `ticket_status_set: skipped (no tracker resolves <ID>)`.
3. **Backlog helper tracker:** run
   `ORCHESTRATOR_STEP_ID=ticket-review <pack>/lib/ticket/set-status.sh <ID> "Review"`.
   It checks the current state, updates, and posts the comment itself. Exit 1
   is an update failure.
4. **Any other tracker:** read the states it offers (workflow states, columns
   or labels) and pick the closest to "in review". Never create one. Update the
   ticket, then post one short comment `ticket-review: status set to <state>.` plus a
   line `correlation: ticket=<ID> change=<$ORCHESTRATOR_CHANGE_ID> step=ticket-review`
   (drop parts whose value is unset). A failed comment is only a warning.
5. Report `completed` with `ticket_status_set: <the state you set>`.

## Reporting

- `ticket_status_set`: the state set, or `skipped (<reason>)`.

## Rules

- The ticket update itself failing (tool unavailable or unauthenticated,
  request rejected, no matching state) fails the step: report status `failed`
  with the reason. This matches the old script behaviour.
- Never invent a state, ticket or comment you did not post. Nothing besides
  state and the one comment is written.
