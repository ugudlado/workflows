# Intake Research Step Metrics

Metric keys: `intake_completeness`, `resume_integrity`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `intake_completeness` | Requires concrete topic, audience and depth; asks one missing field at a time; writes the brief only on completion. | Accepts placeholders or invents audience/depth; blocks on optional fields. |
| `resume_integrity` | Merges user answers into prior intake, preserves unchanged facts, and writes artifacts rather than invented state files. | Replaces the topic with an answer, loses prior constraints, or creates durable *_state.yaml. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
