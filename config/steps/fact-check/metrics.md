# Fact Check Step Metrics

Metric keys: `claim_verification`, `verdict_accuracy`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `claim_verification` | Compares every Key Finding with its cited source, re-opens the URL when extracts are thin, and records a reasoned mark per finding in a Fact check section. | Skips findings, rubber-stamps them, or marks without reading the source. |
| `verdict_accuracy` | needs_work for any unsupported, misstated or non-listed citation, pass otherwise, and findings left unedited. | Passes a finding the source does not state, fails a supported one, or rewrites the findings itself. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
