---
name: synthesize-findings
description: "Write a source-backed findings report from the vetted sources.md, and repair flagged findings after a fact check."
user-invocable: true
---

# Synthesize Findings

**Intent:** Answer the research topic with a tight, source-backed report built
only from the vetted sources in `{in.sources}`. Discovery is done: you do not
search for new sources.

## Verify

- `{out.findings}` exists under the workspace dir.
- Every Key Finding cites at least one `[n]` that exists in `{in.sources}`.
- No source or URL appears that is not in `{in.sources}`.
- On a re-run, the old `## Fact check` section is removed and every flagged
  finding is fixed or dropped.

## Instructions

**Check inputs first.** If `{in.sources}` is missing, or neither `{in.intake}`
nor `{in.topic}` exists, do not invent anything — fail immediately with the
missing-input reason.

1. Read `{in.intake}` and/or `{in.topic}`. Note **Topic**, **Audience**, and
   **Depth**. Read `{in.sources}` in full.
2. Write `{out.findings}` using only facts from `{in.sources}`. You may re-open
   a listed URL to read more of it, but add no new sources. Match depth and
   audience (ops guide vs brief):
   - **Summary** — 2-3 sentences answering the topic directly.
   - **Key Findings** — bullet list; each bullet cites at least one `[n]`
     matching the numbered list in `sources.md`.
   - **Practical takeaways** — only if the depth is a practical guide.
3. **Re-run after a fact check.** If an existing `{out.findings}` has a
   `## Fact check` section, fix or drop each flagged finding against the
   sources (do not defend an unsupported claim), then remove the old Fact check
   section. Leave verified findings as they are.
4. If the sources cannot answer the topic, say so plainly in Summary, mark the
   topic **unresolved**, and do **not** invent facts or citations.

The files are the deliverable — do not return the report as chat prose.

## Reporting

Report that `findings.md` is written. On a re-run, list the findings you fixed
or dropped. State which sources you re-opened and what you did not check.
