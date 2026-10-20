---
name: triage
description: "Classify a request as a feature or a fix and record the call in triage.md. Use at the start of dev runs to route to the right path."
user-invocable: true
---

# Triage

**Intent:** Decide whether the request is a **feature** (a new capability or a
deliberate change in behaviour) or a **fix** (something broken that should
already work), so the workflow routes it down the right path. Judge from the
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
3. Write `{out.triage}`: a heading with the call (`# Triage: feature` or
   `# Triage: fix`) and one paragraph of rationale that quotes or cites the
   ticket text the call rests on.
4. Use `await_input` only when the ticket is genuinely ambiguous (it reads
   equally as a bug or a request and the difference changes the path). Write
   nothing and give one focused `ask`. A bug report with a vague title is not
   ambiguous; classify it.

## Reporting

- `change_type`: `feature`, `fix` or `await_input`.
- Outs: `triage` (always, unless `await_input`).

## Rules

- Never invent ticket content or scope; cite what the ticket says.
- Do not assess severity or urgency; that is diagnose's job.
- On re-entry after `await_input`, treat the new direction as the answer.
