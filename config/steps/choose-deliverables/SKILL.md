---
name: choose-deliverables
description: "Ask which deliverable formats to build from the approved storyline and record the choice in deliverables.json."
user-invocable: true
---

# Choose Deliverables

**Intent:** The storyline is approved; ask the human which formats to build
from it and record the answer. You only ask and record; the next step builds.

## Verify

- On the first run, `choice_status` is `await_input` with an `ask` and an
  `options` value, and `{out.deliverables_choice}` is not written.
- On a re-run with a User answer that names at least one valid option,
  `{out.deliverables_choice}` is `{"formats": [<option ids>]}` and
  `choice_status` is `complete`.
- Only the five option ids below ever appear in `formats`.

## Options

| id | label |
| --- | --- |
| `slides` | Slide deck: Marp markdown to HTML, PDF, per-slide PNG, and image-based .pptx |
| `poster` | One-page poster (PDF + PNG) |
| `article` | Written article/blog (.md + .docx via pandoc) |
| `video` | Narrated video (.mp4) from the slides |
| `editable-pptx` | Editable PowerPoint via python-pptx (layout not render-checked) |

## Instructions

1. Read `{in.intake}` (topic, audience, depth) and glance at `{in.storyline}`
   so the ask can suggest a sensible default for this audience.
2. Look for a User answer (the latest user text / "User direction"). None
   present: this is the first run, go to step 4.
3. Parse the answer. Accept option ids, labels or plain phrases ("slides and
   video", "a deck", "word doc" -> `article`, "powerpoint I can edit" ->
   `editable-pptx`), comma- or "and"-separated; "all" selects every option.
   Map to ids, dedupe, keep table order. If at least one id results, write
   `{out.deliverables_choice}` as `{"formats": ["slides", "video"]}`, report
   `choice_status: complete` and stop. (`video` is allowed on its own; the
   next step builds the slides it needs.)
4. Otherwise (first run, empty, or nothing recognised): report
   `choice_status: await_input` with:
   - `options`: a JSON array string of the option ids with one-line labels,
     exactly `[{"id":"slides","label":"Slide deck (HTML, PDF, PNG, .pptx)"},{"id":"poster","label":"One-page poster (PDF + PNG)"},{"id":"article","label":"Article (.md + .docx)"},{"id":"video","label":"Narrated video (.mp4)"},{"id":"editable-pptx","label":"Editable PowerPoint (python-pptx)"}]`
   - `ask`: a plain-text question that lists every option as `id - label` and
     says to reply with one or more ids, e.g. "slides, video". When the answer
     was unrecognised, say what you could not match and ask again. Suggest a
     default for the intake's audience in one short clause.

## Reporting

Report `choice_status`; on `await_input` also report `ask` and `options`; on
`complete` state the chosen format ids.

## Rules

- Do not build anything and do not invent options beyond the five.
- A plain-text answer must work as well as a button click; never require JSON
  from the human.
