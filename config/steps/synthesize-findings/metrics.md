# Synthesize Findings Step Metrics

Metric keys: `source_integrity`, `audience_fit`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `source_integrity` | Checks inputs, uses accessible primary evidence, cites every key finding with a listed real URL, and marks unsupported research unresolved. | Invents a topic, facts or URLs; treats inaccessible/dated claims as established current evidence. |
| `audience_fit` | Answers the actual intake topic at the requested depth with a short Summary, Key Findings and Sources artifact. | Returns chat-only prose, ignores audience/depth, or omits required report sections. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
