# Choose Deliverables Step Metrics

Metric keys: `ask_clarity`, `answer_parsing`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `ask_clarity` | First run reports await_input with a plain-text ask listing all five options by id and label, plus a valid JSON `options` array, and writes no deliverables.json. | Skips asking, guesses formats, omits `options`, or lists options that do not exist. |
| `answer_parsing` | Maps ids, labels and plain phrases to ids, writes {"formats": [...]} and reports complete; empty or unknown answers return await_input with a clarifying ask. | Writes unknown ids, completes on an empty answer, or demands JSON from the human. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
