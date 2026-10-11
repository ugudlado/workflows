---
name: storyline
description: "Turn verified findings into a format-neutral content bundle: core message, SCQA, 10 sections with headlines and cited bullets, key figures and a practical "What you can do" section."
user-invocable: true
---

# Storyline

**Intent:** Decide what every deliverable says before any is built. The
storyline is a format-neutral content bundle (slides, poster, article, video
and PowerPoint all read it): message first, formats later. Practice is the
Pyramid Principle with an SCQA frame and a dot-dash outline
(https://thinkinsights.net/consulting/storyboard). Content comes only from
verified findings, pitched at the intake's audience and depth.

## Verify

- `{out.storyline}` has the core message, the SCQA frame, exactly 10 numbered
  sections (1 title, 2-9 content, 10 sources), key figures and a "What you can
  do" section.
- Every content section has a headline (full-sentence takeaway), 3-5 dash
  bullets with citation numbers, and a one-line image idea.
- Bullets use only findings marked verified (or contested, with the
  qualification stated) in the `## Fact check` section of `{in.findings}`;
  nothing unsupported or new.
- "What you can do" is built from the findings' Practical takeaways; every
  number in it is stated by a verified source and carries its `[n]`.
- Vocabulary, length and examples fit the intake's audience and depth.
- Reading only the headlines tells the story, in order.

## Instructions

**Check inputs first.** If `{in.findings}` or `{in.intake}` is missing, fail
immediately with the missing-input reason.

1. Read `{in.intake}` (topic, audience, depth) and `{in.findings}`. Keep only
   findings marked verified or contested in its Fact check section; carry a
   contested finding's qualification into its bullet.
2. If the usable findings cannot support 8 distinct content sections, report
   failed with the reason. Do not pad or invent.
3. Write `{out.storyline}`, with no assumption about the output format:
   - **Core message** — the one sentence the audience should remember.
   - **SCQA** — Situation, Complication, Question, Answer, a line each.
   - **Sections** — 10 numbered sections so slides map 1:1: section 1 title
     (topic and audience line), sections 2-9 content, section 10 sources. For
     each content section: a headline, 3-5 dash bullets with citation numbers,
     and a one-line image idea.
   - **Key figures** — 2-4 numbers or charts worth showing (value, what it
     measures, `[n]`), each from a verified source.
   - **What you can do** — 3-5 practical actions for this audience, built from
     findings.md's Practical takeaways (skip invented advice; if the findings
     have no Practical takeaways, derive actions only from verified findings
     and say so). Each cites its `[n]`.
4. Order the headlines so they read as an argument that leads to the core
   message. One idea per section. Match the audience and depth throughout.

The file is the deliverable — do not return it as chat prose.

## Reporting

Report that `storyline.md` is written. State how many verified findings you had
and which, if any, you left out and why.
