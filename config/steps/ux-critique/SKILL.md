---
name: ux-reviewer
description: "UX design critique with staff-level evaluation. Use when reviewing UI/UX, critiquing designs, or before shipping a UI feature."
user-invocable: true
---

# Run UX Critique

**Intent:** Critique UI changes, apply fixable issues, and record verdict +
findings on the UX design artifact (`ux-artifacts.yaml` → `review:`), using
the shared feedback template — not a separate critique result file.

## Capability

Before acting, read the installed `ux-reviewer` skill's `SKILL.md` and use its
review rules and named `review` result. This file is only the workflow adapter:
it supplies scoring and edit authorization, persists the review metadata,
commits permitted fixes, and maps the verdict to workflow status. Do not use an
`extends` prompt.

## Instructions

1. Quality thresholds are step-owned (vendor this pack to change them):
   - target_score = 8
   - max_retries = 3
   - Caps: critical_cap 5, important_cap 7, green_base 9

2. Check if any files modified in this phase touch UI:
   Match: `*.html`, `*.css`, `*.scss`, `*.tsx`, `*.jsx`, `*.svelte`, `*.vue`,
   `*.astro`, or paths under `components/`, `pages/`, `views/`, `layouts/`,
   `templates/`. Also treat an existing `ux-prototype.html` as UI surface.

   If NO UI surface → write `review:` with `verdict: skipped`,
   `guidance: "No UI changes — skipped."`, log once, return completed.

3. Read `ux-reviewer/reference/feedback-format.md` and the feedback template.
   Critique the target UI (modified files + prototype) for the four
   dimensions: accessibility, hierarchy, consistency, friction.

4. Score each dimension 1–10 with the same severity caps as design-review
   (critical → critical_cap, important → important_cap). Overall = min of
   dimensions.

5. If overall >= target_score and no critical findings: PASS.
   Write/replace `review:` on `ux-artifacts.yaml` (Verdict pass, scores,
   Findings "None — pass.", Guidance "Ship."). Return completed.

6. If overall < target_score or critical findings:
   a. Parse findings into fix tasks; apply autonomously fixable issues only
   (CSS, accessible names, obvious consistency) scoped to those findings.
   b. Run the repo's verify commands (from CLAUDE.md / AGENTS.md / README /
   manifests) after edits.
   c. Increment an in-memory retry counter; re-critique.
   d. If retries >= max_retries: write `review:` with `verdict: needs_work`,
   full findings + guidance for a human, return `status: failed`.
   e. Otherwise continue the fix loop.

7. On the way out after a successful fix loop: write `review:` with
   `verdict: pass`, final scores, and guidance noting fixes applied.
   Commit UX improvements:

   ```
   style(<change-id>): UX critique improvements (score: N/10)
   ```

8. Keep `ux-artifacts.yaml` prototype metadata (file, description, options)
   intact — only replace the `review:` mapping.

### Rules (constraints on how)

- Only runs when the phase includes UI-facing changes (else skipped).
- Do not invent a separate `ux-critique.md` output — `{out.ux_artifacts}` is the report.
- Target score is 8 (step-owned).

## Verify

- `ux-artifacts.yaml` has a complete `review:` block per the feedback format
- The `review:` verdict matches the `verdict` value you report
  (`pass` / `needs_work` / `skipped`)
- Discoverable verify commands pass after any applied fixes
