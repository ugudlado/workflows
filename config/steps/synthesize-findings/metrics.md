# Synthesize Findings Step Metrics

Metric keys: `source_integrity`, `audience_fit`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `source_integrity` | Checks inputs, writes findings only from sources.md, cites every key finding with a listed [n], and marks unsupported research unresolved. | Invents a topic, facts or sources; adds claims that sources.md does not contain; ignores flagged findings on a re-run. |
| `audience_fit` | Answers the actual intake topic at the requested depth with a short Summary and cited Key Findings artifact, and repairs fact-check flags on a re-run. | Returns chat-only prose, ignores audience/depth, or omits required report sections. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
