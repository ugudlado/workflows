# Answer Step Metrics

Metric keys: `directness`, `source_integrity`, `project_first`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `directness` | Never restates the question; says plainly in one or two sentences when the allowed sources do not answer it; otherwise opens with the answer in at most five sentences, then only the detail needed to act on or check it; asks one focused question when the request cannot be answered as put. | Background before the answer, a survey where one answer was asked for, or a guess at an ambiguous question. |
| `source_integrity` | Every claim names a file or page that was opened in this run; open points sit under Not known; `source_count` matches the list. | Unopened or invented URLs, search snippets presented as read pages, or gaps filled with unsourced claims. |
| `project_first` | Searches and reads the project's own files before the web, lets a project fact outrank a general one, and reports a disagreement with both sources. | Answers from the web alone when the project holds the answer, or silently overrides what the project states. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
