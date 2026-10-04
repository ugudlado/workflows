# Run Learn Cycle Step Metrics

Metric keys: `learning_pipeline`, `scenario_quality`

| Metric              | 10 looks like                                                                                                              | 0 looks like                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `learning_pipeline` | Uses driver-supplied active history; checks recalled agentmemory outcomes against observed verification and current code; fails soft and logged.         | Treats memory as authority, accepts confidence-only/stale fixes, reads stale state, or lets a learning failure block completion.    |
| `scenario_quality`  | Verified lessons become fresh train proposals at the contract artifact with 3-4 observable expects and wrapper provenance; train coverage deduplicated. | Scenarios derive from dev/holdout, leak the rule, lack observed evidence, duplicate train coverage, or go to project.yaml. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
