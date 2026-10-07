---
name: explore
description: "Explore the codebase and write a discovery brief. Use when discovering scope, surveying a codebase, or starting a feature."
user-invocable: true
---

# Explore

**Intent:** Survey the problem space — constraints, patterns, and open questions.

## Capability

Before acting, read the installed `explorer` skill's `SKILL.md` and use its
read-only investigation rules and named `discovery` result. This file is only
the workflow adapter: it supplies ticket context, persists the result, and
emits the completion protocol. Do not use an `extends` prompt.

## Instructions

1. Search the codebase for files, patterns, and modules relevant to the description.
   First read `{in.ticket}` when it exists — that file is the
   ticket body (title, description, ACs). Treat it as the source of truth for
   scope; do not invent a different feature from the codebase.
   Read architecture from the repo docs (CLAUDE.md / AGENTS.md / README) and directly related source files.
   Do NOT web-search unless the description explicitly references external technology.
2. Identify existing codebase conventions that constrain the solution space.
3. Identify key constraints, integration points, and affected components.
4. List unresolved questions that will inform design choices.
5. Write discovery brief to {out.discovery}, using the
   template at explore/templates/$SCHEMA/discovery.md as
   structural guide. All required sections must be populated (use "N/A" for irrelevant
   sections). Required sections, in order: Frontmatter (`feature-id`, `linear-ticket`),
   Feature Summary, Personas & Actors, Use Cases (Happy Path + Error & Edge Cases),
   Scope (In Scope + Out of Scope), UI Direction, Key Decisions, Open Questions.
   **Producing discovery.md? First Read `explore/reference/discovery-format.md`**
   for the exact per-section format, field rules, and identifier conventions.
6. Do not return the brief as chat prose — the file is the artifact.

### Rules (constraints on how)

- Focus on problem-space survey, NOT solution design (design owns that).
- Capture unresolved questions explicitly.
- Scope research to the codebase unless description references external technology.

## Verify

Before finishing, confirm:

- Discovery brief written to {out.discovery}
- Brief covers constraints and integration points (not design approaches — those belong in design)
- Unresolved questions explicitly listed (not hidden)
- At least 2 use cases defined (minimum 1 happy path UC-N, minimum 1 error/edge UC-EN)
- Build-or-reuse decision is explicitly stated (Key Decisions section addresses whether to build new or reuse/extend existing)
