---
name: deliverables
description: "Build every chosen deliverable format (slides, poster, article, video, editable pptx) from the approved storyline, render-checking slides and poster."
user-invocable: true
---

# Deliverables

**Intent:** Build each format the human chose from the one approved storyline,
so all deliverables say the same thing. Content comes only from
`{in.storyline}`, `{in.findings}` and `{in.sources}`; nothing is added.

## Verify

- One output per chosen format exists on disk at the reported path and opens
  (reopen the saved files; do not trust your build code).
- Slides and poster were rendered to PNG, every PNG was read, and overflow,
  clipping and overlap were fixed within 3 render rounds; what was checked is
  reported.
- Nothing appears beyond the findings and sources: no extra claims or URLs.
- Every number in the output traces to a verified source cited in the storyline.
- Vocabulary and length fit the intake's audience and depth.
- Every image is a downloaded local file with its credit recorded.
- `formats` equals the number of chosen formats actually built.

## Instructions

**Check inputs first.** If `{in.deliverables_choice}`, `{in.storyline}`,
`{in.findings}` or `{in.intake}` is missing, fail immediately with the
missing-input reason. Do not invent content.

1. Read `{in.deliverables_choice}` (`{"formats": [...]}`), `{in.intake}`,
   `{in.storyline}`, `{in.findings}` and `{in.sources}` if present. Work in a
   `deliverables/` folder inside `$ORCHESTRATOR_ARTIFACTS_DIR` (the directory
   holding `{in.findings}` if that is unset). File stem: the intake topic as a
   kebab-case slug.
2. `video` needs the slide PNGs: if `video` is chosen and `slides` is not,
   build slides first, then the video, and say so. Build order: slides,
   poster, article, editable-pptx, video.
3. For each chosen format, read its instruction file in this step's directory
   (`$ORCHESTRATOR_STEP_DIR/formats/<id>.md`, i.e. `formats/slides.md`,
   `formats/poster.md`, `formats/article.md`, `formats/video.md`,
   `formats/editable-pptx.md`) and follow it exactly.
4. Shared images: fetch each section's image once into
   `deliverables/assets/` and reuse it across formats (photos first from
   Unsplash, credit `Photo by <name> on Unsplash, <photo page URL>`; then other
   openly licensed images with credit; only then a drawn illustration). Confirm
   each file is a real image; never hotlink; name every section without a photo
   in the report.
5. Render check for slides and poster (see their format files): up to 3 rounds
   of render, read every PNG, fix, re-render.
6. If a chosen format cannot be built (a tool is missing, the storyline cannot
   support it, a render still fails after 3 rounds), report failed with the
   reason and which formats did build. Do not ship a partial deliverable as
   complete.

The files are the deliverables — do not return content as chat prose.

## Reporting

Report `deliverables` (absolute paths of every produced file, one per line)
and `formats` (count of formats built). State per format what you verified
(render rounds, issues fixed, files reopened) and what you did not (the
`editable-pptx` layout is not render-checked), and name sections that got a
drawn illustration.

## Rules

- Image credits go in speaker notes (decks), the credits line (poster, article)
  or the video description file; never omit them.
- LibreOffice is not available; do not use it.
