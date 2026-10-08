# Presentation Step Metrics

Metric keys: `source_fidelity`, `audience_fit`, `visual_quality`

| Metric | 10 looks like | 0 looks like |
| --- | --- | --- |
| `source_fidelity` | Checks inputs, builds every content slide only from the findings, keeps citation numbers in notes, and lists only real sources; fails honestly when findings are too thin. | Invents claims or URLs, pads slides with unsupported content, or ships a partial deck as complete. |
| `audience_fit` | Exactly 10 slides named after the topic: title, 8 one-idea content slides with 3-5 plain bullets and speaker notes at the audience's depth, and a sources slide. | Wrong slide count or file name, dense or jargon-heavy slides, missing speaker notes. |
| `visual_quality` | Topic-suited palette, fonts and background applied consistently; every content slide has an embedded, legally usable image or drawn illustration, with credits in notes for sourced images. | Generic default template, inconsistent styling, bare content slides, hotlinked or unlicensed images, missing credits. |

## Eval context

Scenarios are evaluated as a single text response with no file or shell
access. The response IS the artifact: score inline artifact content (file
bodies, sections, COMPLETION blocks) as the artifact itself, and explicitly
named commands with their expected outcomes as performed verification. Do
not penalize a response for being unable to literally write files or execute
commands in this context.
