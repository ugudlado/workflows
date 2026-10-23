---
name: triage
description: "Classify a request as a feature, a fix or a quick change and record the call in triage.md. Use at the start of dev runs to route to the right path."
user-invocable: true
---

# Triage

**Intent:** Decide whether the request is a **feature** (a new capability or a
deliberate change in behaviour), a **fix** (something broken that should
already work), or a **quick** change (small and fully specified), so the workflow routes it down the right path. Judge from the
ticket alone; do not explore code or propose a solution.

## Instructions

1. Read `{in.ticket}` (the ticket or brief). If it is missing, you have nothing
   to classify: report `await_input`.
2. Classify:
   - `feature`: asks for something the product does not do today, or to change
     intended behaviour (new flag, new screen, different rule).
   - `fix`: describes behaviour that contradicts what the product already
     promises or did before (error, crash, wrong output, regression), even if
     the ticket is worded as a request.
   - `quick`: a small, well-specified, low-risk change whose whole scope is
     clear from the ticket, whether feature or fix: a copy/text change, a
     config or flag value, a dependency bump, a small bug with an obvious
     cause, touching a few files. It is NOT quick if it adds a UI flow,
     changes an API, schema or data model, touches security, auth or
     payments, or needs investigation to understand. When in doubt choose
     `feature` or `fix`; `quick` skips design and diagnosis.
   - Judge the change the ticket most likely needs, not every branch it
     hedges on. A conditional fallback ("if the API doesn't return it yet,
     add it") is not by itself an API change. When a hedge is the only thing
     against `quick`, choose `quick` and name the hedge in the rationale: a
     quick change whose implement fails escalates to design anyway.
3. Write `{out.triage}`: a heading with the call (`# Triage: feature`,
   `# Triage: fix` or `# Triage: quick`) and one paragraph of rationale that
   quotes or cites the ticket text the call rests on. Keep the heading exact:
   `name-branch` reads it to name the branch (`feature/`, `fix/`, `chore/`).
4. Use `await_input` only when the ticket is genuinely ambiguous (it reads
   equally as a bug or a request and the difference changes the path). Write
   nothing and give one focused `ask`. A bug report with a vague title is not
   ambiguous; classify it.

## Reporting

- `change_type`: `feature`, `fix`, `quick` or `await_input`.
- Outs: `triage` (always, unless `await_input`).

## Rules

- Never invent ticket content or scope; cite what the ticket says.
- Do not assess severity or urgency; that is diagnose's job.
- On re-entry after `await_input`, treat the new direction as the answer.
