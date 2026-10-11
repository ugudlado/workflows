---
name: fact-check
description: "Re-open the live source for every claim in each Key Finding, run a counter-evidence search, and record verified/contested/unsupported marks in findings.md."
user-invocable: true
---

# Fact Check

**Intent:** Confirm against the live source (not our own notes) that each Key Finding is
supported by what it cites, and surface counter-evidence, so nothing unverified reaches the storyline. You check; you do not
rewrite the findings.

## Verify

- Every Key Finding has a mark (verified, unsupported or contested) in the
  `## Fact check` section of `{out.findings}`.
- Every number, quote and strength-of-claim in each finding was compared with
  the live source (or its abstract record), not only with the notes in
  `{in.sources}`.
- Every finding had one counter-evidence search; contested findings name the
  counter-source (URL you opened).
- Every cited number resolves to an entry in `{in.sources}`.
- Findings text above the Fact check section is unchanged.
- `verdict` is `needs_work` if any finding is unsupported, misstated, or cites a
  source not in `{in.sources}`; otherwise `pass`. A contested finding that is
  worded as settled is `needs_work`; one already worded with the qualification
  is `pass`.

## Instructions

**Check inputs first.** If `{in.findings}` or `{in.sources}` is missing, fail
immediately with the missing-input reason.

1. Read `{in.findings}` and `{in.sources}`.
2. **Live check, not a circular check.** For each Key Finding, list its claims:
   every number, date, quote, and the strength of the wording (causes vs
   associated with, all vs some). Re-open each cited source (`curl` the URL, or
   the scholarly API record: Europe PMC, OpenAlex, Semantic Scholar) and find the
   passage that states each claim. `sources.md` notes are a pointer only; they
   never count as the confirmation. If a page will not load (403, paywall), use
   its abstract record and say the check is abstract-only; if neither loads, the
   claim is unchecked and the finding is unsupported.
3. **Counter-evidence.** For each Key Finding run one search for sources that
   contradict or heavily qualify it (for example "<claim> no effect",
   "<claim> systematic review conflicting"), scholarly APIs first, then web.
   Open any hit before relying on it. Do not add it to `sources.md`.
4. Mark each finding **verified** (the live source states it as worded and no
   credible counter-source turned up), **contested** (verified against its
   source, but a credible source contradicts or heavily qualifies it; name the
   counter-source URL and what it says), or **unsupported** (not stated,
   overstated, misstated, or the citation is not in `sources.md`; one-line reason).
5. Append a `## Fact check` section to `{out.findings}` (replace an existing
   one) with one line per finding: its number or first words, the mark, the
   problem or counter-source if any, and the check level: `live` (full text
   re-read) or `abstract-only`. Close the section with two lists: sources
   checked live, sources checked abstract-only. Leave the rest of the file
   untouched.
6. Verdict: `needs_work` if any finding is unsupported or is contested but
   worded as settled; otherwise `pass`.

## Reporting

Report `verdict`. State which sources you checked live and which abstract-only, which findings
are contested and by what, and name any you could not check (for example, a
page and its abstract record that both fail to load).
