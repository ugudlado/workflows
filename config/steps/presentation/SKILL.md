---
name: presentation
description: "Turn the research findings into a 10-slide, topic-themed, illustrated PowerPoint deck named after the topic."
user-invocable: true
---

# Presentation

**Intent:** Turn the findings into a 10-slide PowerPoint deck the intake's
audience can be presented with. Content comes only from the findings; nothing
is added.

## Verify

- The `.pptx` exists, opens, and has exactly 10 slides.
- Every content slide has speaker notes.
- Nothing appears beyond `{in.findings}` and `{in.sources}`: no extra claims or URLs.
- The theme (palette, fonts, background style) is the same on every slide.
- Every content slide has at least one image or illustration.
- Every sourced image has its credit in that slide's speaker notes.

## Instructions

**Check inputs first.** If `{in.findings}` or `{in.intake}` is missing, fail
immediately with the missing-input reason. Do not invent content.

1. Read `{in.intake}` (topic, audience, depth), `{in.findings}` and, if present,
   `{in.sources}`.
2. File name: the intake's topic as a kebab-case slug (lowercase, every run of
   non-alphanumerics becomes `-`, trimmed) plus `.pptx`. Write it into
   `$ORCHESTRATOR_ARTIFACTS_DIR`, beside the `in:` artifacts.
3. Theme: choose a palette, fonts and background style that suit the topic and
   audience (for example calm greens and blues for health and wellbeing), not a
   generic default template. Apply it consistently on every slide.
4. Build exactly 10 slides with whatever slide-authoring tool you have (a
   presentation library or skill):
   - Slide 1, title: the topic as written in `intake.json`, plus an audience line.
   - Slides 2-9, content: drawn only from `findings.md`. One idea per slide, 3-5
     short bullets in plain language matched to the audience and depth. Speaker
     notes on each carry the supporting detail and citation numbers. Each has at
     least one relevant image.
   - Slide 10, sources: the sources used, as listed in the findings/sources.
5. Images: use only images you may legally use. Either openly licensed images
   (public domain or Creative Commons) with the credit in that slide's speaker
   notes, or illustrations you generate yourself (simple icons, shapes,
   diagrams). Embed every image in the file; never hotlink. If no suitable image
   can be obtained for a slide, draw a topic-matched illustration instead of
   leaving it bare, and say so in the report.
6. If the findings cannot support 8 distinct content slides, or you cannot
   produce 10 valid slides, report failed with the reason. Do not ship a partial
   or padded deck.

The deck file is the deliverable. Do not return it as chat prose.

## Reporting

Report `deck` (absolute path of the written `.pptx`) and `slide_count`. State
what you verified and what you did not, and name any slide that got a drawn
illustration because no sourced image was available.
