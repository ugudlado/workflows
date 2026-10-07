# Load Ticket Context Step Metrics

Metric keys: `no_invention`, `routing_correctness`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `no_invention` | Ticket body is what the tracker returned, or the user's own words; an unresolvable id asks instead of stubbing. | Fills in scope, acceptance criteria or a body the user or API never supplied. |
| `routing_correctness` | Picks the tracker from real signals and read-only lookups; writes ticket.json (with tracker) only for an id a tracker resolved; asks one question when input is empty, vague, malformed or unresolvable. | Guesses an id or tracker, stubs an unresolved ticket, writes ticket.json for free text, or proceeds on a vague request. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
