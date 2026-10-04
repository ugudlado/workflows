# Verify Changes Step Metrics

Metric keys: `criterion_coverage`, `verification_evidence`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `criterion_coverage` | Derives the checklist from requirement artifacts, maps every item to branch code/tests, and rejects undelivered or partially met work. | Trusts completion claims, averages away missing criteria, or judges the wrong branch. |
| `verification_evidence` | Runs existing project checks and records real results, failures or the explicit absence of checks in the contract-resolved `{out.verification}` artifact (currently `verify-changes.md`). | Assumes passing output, conceals failures, or claims unavailable checks ran. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
