# Deliverables Step Metrics

Metric keys: `source_fidelity`, `render_quality`, `format_coverage`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `source_fidelity` | Checks inputs, builds every format only from the storyline, findings and sources, keeps citation numbers, lists real sources, and pitches at the intake's audience and depth. | Invents claims or URLs, adds unverified numbers, or ignores audience and depth. |
| `render_quality` | Renders slides and poster to PNG, reads every PNG, fixes overflow/clipping/overlap within 3 rounds, uses a consistent topic-suited theme and credited local images, and reports what was checked. | Skips the render check, ships clipped or overlapping text, hotlinks images, or omits credits. |
| `format_coverage` | Builds exactly the chosen formats (video builds slides first), reports every path and an honest count, and fails with the reason when a format cannot be built. | Builds unchosen formats, skips a chosen one silently, or reports success on a missing file. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
