---
name: presentation
description: "Turn the research findings into a 10-slide, topic-themed, illustrated PowerPoint deck named after the topic."
user-invocable: true
---

# Presentation

**Intent:** Build the approved storyline into a 10-slide PowerPoint deck the
intake's audience can be presented with. Slides follow `{in.storyline}`;
content comes only from the findings and sources, nothing is added.

## Verify

- The `.pptx` exists, opens, and has exactly 10 slides.
- Every content slide has speaker notes.
- Slide titles, bullets and order follow `{in.storyline}`.
- Nothing appears beyond `{in.findings}` and `{in.sources}`: no extra claims or URLs.
- The theme (palette, fonts, background style) is the same on every slide.
- Every content slide has at least one image, a photo wherever one was found.
- Every sourced image has its credit in that slide's speaker notes.
- Reopen the saved file to count slides, notes and images; do not rely on your
  build code. If you can render slides to images, look for overflowing or
  overlapping text; if you cannot, say so.

## Instructions

**Check inputs first.** If `{in.findings}`, `{in.storyline}` or `{in.intake}` is missing, fail
immediately with the missing-input reason. Do not invent content.

1. Read `{in.intake}` (topic, audience, depth), `{in.storyline}`, `{in.findings}`
   and, if present, `{in.sources}`.
2. File name: the intake's topic as a kebab-case slug (lowercase, every run of
   non-alphanumerics becomes `-`, trimmed) plus `.pptx`. Write it into
   `$ORCHESTRATOR_ARTIFACTS_DIR`; if that is unset, into the directory holding
   `{in.findings}`.
3. Theme: choose a palette, fonts and background style that suit the topic and
   audience (for example calm greens and blues for health and wellbeing), not a
   generic default template. Apply it consistently on every slide.
4. Build exactly 10 slides with whatever slide-authoring tool you have (a
   presentation library or skill):
   - Slide 1, title: the topic as written in `intake.json`, plus an audience line.
   - Slides 2-9, content: the storyline's action headline as the slide title and
     its 3-5 bullets, with content drawn only from `findings.md`. One idea per
     slide, plain language matched to the audience and depth. Speaker notes on
     each carry the supporting detail and citation numbers. Each has at least
     one relevant image, using the storyline's image idea as the search term.
   - Slide 10, sources: the sources used, as listed in the findings/sources.
5. Images: photos first. Search Unsplash (unsplash.com, free to use under the
   Unsplash License) with each slide's image idea from the storyline, download
   the image file, confirm it is a real image, and embed it. Credit it in that
   slide's speaker notes as `Photo by <name> on Unsplash, <photo page URL>`. If
   Unsplash has nothing suitable, use another openly licensed image (public
   domain or Creative Commons) with its credit, and only then an illustration
   you draw yourself. Embed every image in the file; never hotlink. Never leave
   a content slide bare, and name every slide without a photo in the report.
6. If the storyline cannot support 8 distinct content slides, or you cannot
   produce 10 valid slides, report failed with the reason. Do not ship a partial
   or padded deck.

The deck file is the deliverable. Do not return it as chat prose.

## Reporting

Report `deck` (absolute path of the written `.pptx`) and `slide_count`. State
what you verified and what you did not, and name any slide that got a drawn
illustration because no sourced image was available.
