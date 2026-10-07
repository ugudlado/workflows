---
name: load-ticket-context
description: "Turn the user's direction into ticket-context.md: fetch a named ticket, or capture a free-text request. Use at the start of feature and bugfix runs."
user-invocable: true
---

# Load Ticket Context

**Intent:** Produce the one context document every later step reads
(`{out.ticket}`) from the `User direction` in the brief. Fetch a ticket's real
body when one is named; otherwise capture the
request as written. Which tracker holds the ticket is decided by inspecting the
tools you have, not assumed. Never invent ticket content or scope.

## Verify

- `{out.ticket}` exists and is non-empty when you report `complete`.
- Its body is the ticket as the tracker returned it (title, description,
  acceptance criteria and labels if present, url), or the user's own words. No
  scope, acceptance criteria or requirements of your own.
- `{out.ticket_ref}` exists only when a ticket id was identified and a tracker
  resolved it, and holds `{"ticket_id": "<ID>", "tracker": "<name>"}` plus
  `url` when known (see the guide).

## Instructions

1. Read `User direction` from the brief. Nothing else is an input; this step
   has no `{in.*}`.
2. Look for a ticket id: a whole token (the entire message or one token in it)
   shaped `KEY-123` (`^[A-Za-z][A-Za-z0-9]*-[0-9]+$`, upper-case it), or a
   forge issue reference `#123` / a bare number given as a ticket. A near-miss
   (`ORC-`, `ORC-12x`) is malformed: go to step 5. A bare number in a longer
   sentence is not an id.
3. **Ticket id present.** Read `<pack>/lib/ticket/TICKETING.md` (`<pack>` is
   the directory two levels above `$ORCHESTRATOR_STEP_DIR`) and follow it with
   no recorded `ticket.json`: gather signals, list your tools, look the id up
   read-only until one tracker returns it. The backlog helper is
   `<pack>/lib/ticket/fetch-ticket.sh <ID>` (prints the task as markdown).
   - **Resolved:** write `{out.ticket}` from the fetched ticket (title,
     description, acceptance criteria and labels if present, url), write
     `{out.ticket_ref}` including `tracker`, report `complete`.
   - **No tracker resolves it** (none available, not authenticated, id not
     found, or ambiguous): report `await_input` with one `ask` naming what you
     tried and asking which tracker to use or to confirm the id. Write
     nothing. Do not stub a ticket file.
4. **No ticket id, usable request** (it says what to build or fix): write
   `{out.ticket}` as `# Brief` followed by the user's text. No `{out.ticket_ref}`.
   Report `complete`.
5. **Otherwise** (empty, vague, or malformed id): report
   `ticket_context_status: await_input` with one focused `ask`: a ticket id or a
   one-line description of the change. Write nothing.

## Reporting

- `ticket_context_status`: `complete` or `await_input`. An unresolvable id is
  `await_input`, never a stub.
- Outs: `ticket` (always on complete), `ticket_ref` (only when an id was found).

## Rules

- Never guess an id or tracker, expand a vague request, or fill in a failed fetch.
- Write `{out.ticket_ref}` only for a real ticket id that a tracker resolved.
- On re-entry after `await_input`, treat the new `User direction` as the answer.
