# Load Ticket Context Step Metrics

Metric keys: `no_invention`, `routing_correctness`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `no_invention` | Ticket body is fetch output verbatim, or the user's own words; a failed fetch is reported as failed with no ticket file. | Fills in scope, acceptance criteria or a body the user or API never supplied. |
| `routing_correctness` | Fetches only for a well-formed id with ticketing configured; stubs with a not-fetched note otherwise; writes ticket.json only for a real id; asks one question when input is empty, vague or malformed. | Guesses an id, fetches without ticketing, writes ticket.json for free text, or proceeds on a vague request. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
