---
name: synthesize-findings
description: "Research a topic with the agent's own web search/browse tools and write a source-backed findings report."
user-invocable: true
---

# Synthesize Findings

**Intent:** Answer the research topic with a tight, source-backed report.
You own discovery — use the web search / browse / fetch tools available in
this agent runtime. Do **not** expect a pre-built `sources.json` or Tavily key.

## Verify

- `findings.md` exists under the workspace dir.
- Every Key Finding cites a URL that appears in Sources.
- No fabricated URLs.

## Instructions

**Check inputs first.** If neither `intake.json` nor `topic.md` exists under
the workspace dir, do not invent a topic — fail immediately:

1. Read `intake.json` and/or `topic.md`. Note **Topic**, **Audience**, and **Depth**.
2. Search the web (or browse docs) with whatever tools you have — pick the
   right tool for the job (site search, docs fetch, general web search). Prefer
   primary/docs sources over SEO fluff. Match depth/audience (ops guide vs brief).
3. Write `{out.findings}` with:
   - **Summary** — 2–3 sentences answering the topic directly.
   - **Key Findings** — bullet list; each bullet cites at least one real URL.
   - **Sources** — numbered list of titles + URLs you used.
4. If search/browse yields nothing usable, say so plainly in Summary, mark the
   topic **unresolved**, and do **not** invent facts or URLs.

The files are the deliverable — do not return the report as chat prose.

