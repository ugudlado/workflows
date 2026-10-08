# Storyline Step Metrics

Metric keys: `message_clarity`, `evidence_discipline`, `structure_fit`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `message_clarity` | One memorable core message, a coherent SCQA frame, and action headlines that tell the whole story when read alone. | Topic labels as headlines, no single message, or an SCQA that does not lead to the answer. |
| `evidence_discipline` | Every bullet comes from a verified finding with a citation number; unsupported findings are excluded; fails honestly when fewer than 8 slides are supported. | Uses unverified or new claims, drops citations, or pads slides to reach the count. |
| `structure_fit` | Exactly 10 slides (title, 8 content, sources), 3-5 dash bullets and an image idea per content slide, pitched at the intake's audience and depth. | Wrong slide count, missing image ideas, dense bullets, or ignored audience. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
