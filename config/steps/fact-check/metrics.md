# Fact Check Step Metrics

Metric keys: `claim_verification`, `verdict_accuracy`, `counter_evidence`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `claim_verification` | Re-opens the live source (or abstract record) for every number, quote and strength-of-claim, never confirming against sources.md notes alone, and records a reasoned mark per finding in a Fact check section. | Skips findings, rubber-stamps them, or marks without reading the source. |
| `verdict_accuracy` | needs_work for any unsupported, misstated or non-listed citation, pass otherwise, and findings left unedited. | Passes a finding the source does not state, fails a supported one, or rewrites the findings itself. |
| `counter_evidence` | Runs one contradicting/qualifying search per finding, opens hits, marks findings contested with the counter-source URL, and lists sources checked live vs abstract-only. | Skips the search, marks contested without a source, or confirms findings only against our own notes. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
