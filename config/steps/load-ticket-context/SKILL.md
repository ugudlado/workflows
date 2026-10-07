---
name: load-ticket-context
description: "Turn the user's direction into ticket-context.md: fetch a named ticket, or capture a free-text request. Use at the start of feature and bugfix runs."
user-invocable: true
---

# Load Ticket Context

**Intent:** Produce the one context document every later step reads
(`{out.ticket}`) from the `User direction` in the brief. Fetch a ticket's real
body when one is named and ticketing is configured; otherwise capture the
request as written. Never invent ticket content or scope.

## Verify

- `{out.ticket}` exists and is non-empty when you report `complete`.
- Its body is either fetch-ticket output verbatim, or the user's own words. No
  scope, acceptance criteria or requirements of your own.
- `{out.ticket_ref}` exists only when a ticket id was identified, and holds
  exactly `{"ticket_id": "<ID>"}` with the id upper-cased.

## Instructions

1. Read `User direction` from the brief. Nothing else is an input; this step
   has no `{in.*}`.
2. Look for a ticket id: a whole token shaped letters/digits starting with a
   letter, a hyphen, then digits (`^[A-Za-z][A-Za-z0-9]*-[0-9]+$`, e.g.
   `ORC-123`), either the entire message or one token in it. Upper-case it.
   A near-miss (`ORC-`, `ORC-12x`, `123`) is malformed: go to step 6.
3. **Ticket id and ticketing configured.** Ticketing is configured when
   `source <pack>/lib/ticket/backlog-api.sh; backlog_api_ticketing` prints
   `backlog`. Run `<pack>/lib/ticket/fetch-ticket.sh <ID>`, where `<pack>` is
   the directory two levels above `$ORCHESTRATOR_STEP_DIR`.
   Write its stdout to `{out.ticket}`, write `{out.ticket_ref}`, report
   `ticket_context_status: complete`. If it exits non-zero, report status
   `failed` with its stderr as the reason; write no ticket file.
4. **Ticket id, ticketing not configured.** Write `{out.ticket}` as: the user's
   text, the id, and a line stating the ticket body was not fetched because
   ticketing is not configured. Write `{out.ticket_ref}`. Report `complete`.
5. **No ticket id, usable request** (it says what to build or fix): write
   `{out.ticket}` as `# Brief` followed by the user's text. No `{out.ticket_ref}`.
   Report `complete`.
6. **Otherwise** (empty, vague, or malformed id): report
   `ticket_context_status: await_input` with one focused `ask`: a ticket id or a
   one-line description of the change. Write nothing.

## Reporting

- `ticket_context_status`: `complete` or `await_input`. A failed fetch is
  reported as step status `failed`, not as an enum value.
- Outs: `ticket` (always on complete), `ticket_ref` (only when an id was found).

## Rules

- Never guess an id, expand a vague request, or fill in a failed fetch.
- Write `{out.ticket_ref}` only for a real ticket id.
- On re-entry after `await_input`, treat the new `User direction` as the answer.
