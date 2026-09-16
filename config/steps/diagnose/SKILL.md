---
name: diagnose
description: "Diagnose a bug and write a diagnosis brief. Use when investigating failures, root-causing bugs, or starting a bugfix."
user-invocable: true
---

# Diagnose

**Intent:** Reproduce a reported defect, trace it to an exact root cause, and
persist a diagnosis brief.

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
- Do NOT propose a fix. Diagnosis and fix are separate concerns.
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
