---
name: fact-check
description: "Check every Key Finding against the sources it cites and record a verified/unsupported verdict in findings.md."
user-invocable: true
---

# Fact Check

**Intent:** Confirm that each Key Finding is actually supported by the source
it cites, so nothing unverified reaches the storyline. You check; you do not
rewrite the findings.

## Verify

- Every Key Finding has a verified or unsupported mark in the `## Fact check`
  section of `{out.findings}`.
- Every cited number resolves to an entry in `{in.sources}`.
- Findings text above the Fact check section is unchanged.
- `verdict` is `needs_work` if any finding is unsupported, misstated, or cites a
  source not in `{in.sources}`; otherwise `pass`.

## Instructions

**Check inputs first.** If `{in.findings}` or `{in.sources}` is missing, fail
immediately with the missing-input reason.

1. Read `{in.findings}` and `{in.sources}`.
2. For each Key Finding, find the source(s) it cites by number and compare the
   claim (including numbers, dates, scope, and strength of wording) with the
   facts extracted for that source in `sources.md`.
3. When the extracted facts are not enough to decide, re-open the source URL
   and read the relevant passage. Do not search for new sources.
4. Mark each finding **verified** (the source states it as worded),
   or **unsupported** (not stated, overstated, misstated, or the citation is
   not in `sources.md`). Give the reason in one line for each unsupported one.
5. Append a `## Fact check` section to `{out.findings}` (replace an existing
   one) with one line per finding: its number or first words, the mark, and the
   problem if any. Leave the rest of the file untouched.
6. Verdict: `needs_work` if any finding is unsupported; otherwise `pass`.

## Reporting

Report `verdict`. State which findings you checked against extracted facts only
and which you re-checked at the live URL, and name any you could not check
(for example, a page that no longer loads).
