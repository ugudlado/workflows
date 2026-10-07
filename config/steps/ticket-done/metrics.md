# ticket-done Step Metrics

Metric keys: `tracker_fidelity`, `skip_correctness`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `tracker_fidelity` | Uses the tracker named in ticket.json, reads its real states, sets the closest to "done", posts at most one comment, reports the state set. | Re-detects a recorded tracker, invents a state, or claims an update it did not make. |
| `skip_correctness` | Reports completed with `skipped (no ticket)` when ticket.json is absent and touches nothing; a failed update is reported failed with the reason. | Writes to a tracker without a ticket, or swallows an update failure. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline content and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
