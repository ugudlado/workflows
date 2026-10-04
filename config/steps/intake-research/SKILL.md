---
name: intake-research
description: "Normalize a research topic and gather a short completeness checklist before synthesize. Use when starting or resuming research intake."
user-invocable: true
---

# Intake Research

**Intent:** Turn the user's topic (and any follow-up answers) into a complete
intake brief. Stay on this step until the checklist is full — do **not** invent
durable `*_state.yaml`. Session state lives in Redis; you only write artifacts.

## Session workspace

- `$CHANGE_ID` / `$ORCHESTRATOR_CHANGE_ID` is the **session id** (not a topic slug).
- The workflow (not the engine) owns artifact placement: use
  the run's artifacts dir as the workspace — the engine resolves
  `{out.intake}` and `{out.topic}` inside it.
- Read/write:
  - `{out.intake}` — structured checklist (source of truth)
  - `{out.topic}` — short human-readable brief (written only when complete)

## Checklist (keep small)

| Field      | Meaning               | Example                                    |
| ---------- | --------------------- | ------------------------------------------ |
| `topic`    | What to research      | "postgres indexing for write-heavy OLTP"   |
| `audience` | Who the report is for | "platform engineers and DBAs"              |
| `depth`    | How deep / what shape | "practical ops guide" or "executive brief" |

Optional (fill if the user volunteers; do not block on them): `constraints`, `out_of_scope`.

## Instructions

1. **Load prior intake** — If `{out.intake}` exists, parse it.
   Merge new facts from the latest user direction (prompt / User direction).
2. **Seed topic** — If `topic` is empty, take it from the latest user text
   (first turn is usually the topic). Do not invent a different topic.
3. **Score completeness** — A field is present when it has a non-empty concrete
   value (not "TBD" / "unknown").
4. **If anything required is missing** — Update `intake.json` with what you have,
   then report `intake_status: await_input` with an `ask` (the run stops; the
   driver relays it and re-runs this step with the answer). Ask for **one**
   missing field at a time.
5. **If checklist is full** — Write `intake.json` and `topic.md`, then report
   `intake_status: complete`. Downstream `synthesize-findings` reads these files.

### `intake.json` shape

```json
{
  "topic": "...",
  "audience": "...",
  "depth": "...",
  "constraints": "",
  "out_of_scope": ""
}
```

### `topic.md` (only when completing)

```markdown
# Research Topic

**Topic:** …
**Audience:** …
**Depth:** …
**Session:** <CHANGE_ID>
```

## Reporting

Report `intake_status: await_input` while the checklist is still missing
`topic`, `audience`, or `depth` — include the `ask` for the next missing
field (one at a time). Report `intake_status: complete` once all three are
filled and `{out.topic}` is written.

## Rules

- Prefer `await_input` over guessing audience/depth.
- Never write `*_state.yaml` under the session folder.
- On re-entry after `await_input`, treat the new user text as the answer to
  the previous `ask` (or as free-form updates), merge into `intake.json`, and
  re-check the checklist.
