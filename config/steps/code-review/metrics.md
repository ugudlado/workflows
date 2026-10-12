# Run Code Review Step Metrics

Metric keys: `verification_evidence`, `gate_integrity`, `criterion_coverage`

Use these metrics only for step-specific scenarios. Base reviewer metrics are
scored separately on base scenarios.

| Metric                  | 10 looks like                                                                                                                                    | 0 looks like                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `verification_evidence` | repo's discovered verify commands actually run; ACs verified with fresh evidence (N/N counts, re-run searches); spot audit of recorded evidence; real check output (or the stated absence of checks) recorded in the contract-resolved `{out.verification}` artifact (currently `verify-changes.md`). | Scores without running commands, trusts stale counts or self-reported evidence unchecked.            |
| `criterion_coverage`    | Derives the checklist from requirement artifacts, maps every item to branch code/tests in the contract-resolved `{out.verification}` artifact (currently `verify-changes.md`), rejects undelivered or partially met work. | Trusts completion claims, averages away missing criteria, or judges the wrong branch.                |
| `gate_integrity`        | Pending tasks → incomplete_phase + status failed; quarantine → critical cap; fix tasks minimal, sequential, status pending.                      | Advances with pending tasks or unresolved criticals, needs_work as completed, scope-creep fix tasks. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
