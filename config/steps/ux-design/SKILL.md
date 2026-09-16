---
name: ux-designer
description: "Design and validate UI/UX through prototyping and critique. Use when designing interfaces or producing UX artifacts."
user-invocable: true
---

# UX Design

**Intent:** Design and validate UI/UX through playground prototyping and critique.

## Capability

Before acting, read the installed `ux-designer` skill's `SKILL.md` and use its
UX rules and named `ux_design` result. This file is only the workflow adapter:
it supplies product context, persists the prototype and metadata, updates the
discovery artifact, and emits the completion protocol. Do not use an `extends`
prompt.

## Instructions

1. Read the discovery brief's "UI Direction" section for context.
   **If the UI Direction is "N/A" or explicitly states no UI components,
   stop this step — do NOT generate prototypes or artifacts:**
2. Generate 3 design options via the playground skill (when available).
   - If playground fails: escalate to user with error. Do not proceed silently.
3. Present options to user for selection.
   - If no selection (timeout or skip): use the first option as stable default.
4. Polish the chosen direction with the frontend-design skill.
   - If frontend-design fails: escalate to user.
5. Validate with the ux-critique skill procedure — apply fixes autonomously.
   - If ux-critique finds autonomously fixable issues (CSS, accessibility): apply and re-run ux-critique.
   - If ux-critique finds issues requiring user input: escalate to user.
   - Max 2 ux-critique retry loops. After that, proceed with current state.
6. Record final UI direction in the discovery brief's "UI Direction" section.
7. Persist UX artifacts:
   a. Save the final polished prototype HTML to
   {out.ux_prototype}
   b. Write {out.ux_artifacts} with:
   - prototype.file: ux-prototype.html
   - prototype.description: one-line summary of the design direction
   - prototype.options_considered: number of options generated (typically 3)
   - prototype.selected_option: which option was chosen
   - prototype.critique_status: passed|passed-with-fixes|skipped
   - prototype.critique_rounds: number of ux-critique iterations run
   - review: stub mapping for ux-critique to fill
     (`verdict` / `overall` / `scores` / `findings` / `guidance` — see
     `ux-reviewer/reference/feedback-format.md`). Leave `verdict` unset or
     `pending` until critique runs.
8. Report `skipped` (true when there was no UI surface, false otherwise).
   Do not report a `ux_direction` value — it is already in `{out.ux_artifacts}`
   and discovery.md.

### Rules (constraints on how)

- Use playground for rapid prototyping, frontend-design for polish, ux-critique for validation.

## Verify

Before finishing, confirm:

- UI Direction section updated in discovery brief
- At least 3 options were generated and one selected
- `{out.ux_prototype}` exists
- `{out.ux_artifacts}` exists and follows § UX Artifact Contract format
