# Source Search Step Metrics

Metric keys: `source_credibility`, `extraction_fidelity`, `coverage`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `source_credibility` | Opens every source, applies CRAAP plus lateral reading, prefers primary/official sources, and drops weak or unloadable pages. | Keeps SEO or consumer pages, lists unopened or invented URLs, or skips the credibility check. |
| `extraction_fidelity` | Each source carries title, URL, publisher, date, a CRAAP note and key facts that match the page, quoted or closely paraphrased. | Facts that the page does not state, missing fields, or snippets presented as read content. |
| `coverage` | A 4-8 query plan, at least 6 credible sources spanning the topic's main questions, and an honest failed report when fewer exist. | No plan, padded list of weak sources to reach six, or a gap hidden instead of reported. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
