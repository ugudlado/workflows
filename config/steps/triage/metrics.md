# Triage Step Metrics

Metric keys: `classification_accuracy`, `rationale_grounding`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `classification_accuracy` | Calls feature vs fix by whether the behaviour should already work; reads through request-style wording of bugs; asks only when the ticket is genuinely ambiguous. | Classifies by title keywords or ticket wording, asks about clear tickets, or guesses on a genuinely ambiguous one. |
| `rationale_grounding` | triage.md names the call and cites the ticket text behind it in one paragraph; no invented scope, severity or solution. | Rationale is generic, uncited, invents requirements, or drifts into diagnosis or design. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
