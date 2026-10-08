---
name: storyline
description: "Turn verified findings into a message-first storyline: one core message, an SCQA frame and a 10-slide outline with action headlines."
user-invocable: true
---

# Storyline

**Intent:** Decide what the deck says before it is built. Message first,
slides later: practice is the Pyramid Principle with an SCQA frame and a
dot-dash outline (https://thinkinsights.net/consulting/storyboard). Content
comes only from verified findings.

## Verify

- `{out.storyline}` has the core message, the SCQA frame and exactly 10 slide
  entries (slide 1 title, slides 2-9 content, slide 10 sources).
- Every content slide has an action headline, 3-5 dash bullets with citation
  numbers, and a one-line image idea.
- Bullets use only findings marked verified in the `## Fact check` section of
  `{in.findings}`; nothing unsupported or new.
- Reading only the headlines tells the story, in order.

## Instructions

**Check inputs first.** If `{in.findings}` or `{in.intake}` is missing, fail
immediately with the missing-input reason.

1. Read `{in.intake}` (topic, audience, depth) and `{in.findings}`. Keep only
   findings marked verified in its Fact check section.
2. If the verified findings cannot support 8 distinct content slides, report
   failed with the reason. Do not pad or invent.
3. Write `{out.storyline}`:
   - **Core message** — the one sentence the audience should remember.
   - **SCQA** — Situation, Complication, Question, Answer, a line each.
   - **Outline** — 10 slides matching the presentation step's structure: slide 1
     title (topic and audience line), slides 2-9 content, slide 10 sources. For each
     content slide: an action headline (a full-sentence takeaway that reads
     alone), 3-5 dash bullets with citation numbers, and a one-line image idea.
4. Order the headlines so they read as an argument that leads to the core
   message. One idea per slide.

The file is the deliverable — do not return it as chat prose.

## Reporting

Report that `storyline.md` is written. State how many verified findings you had
and which, if any, you left out and why.
