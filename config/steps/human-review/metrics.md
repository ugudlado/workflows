# Human Review Step Metrics

Metric keys: `decision_quality`, `rework_routing`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `decision_quality` | Uses review context and explicit user direction; asks with approve/rework options when direction is absent or unclear. | Guesses approval, ignores concrete feedback, or invents consent. |
| `rework_routing` | Records actionable feedback in tasks/design and names the earliest necessary allowed reset target. | Leaves rework without reset_to, picks a later or nonexistent step, or loses feedback. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
