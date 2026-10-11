# Format: article

Output: `deliverables/<stem>-article.md` and `<stem>-article.docx`.

## Build

Write a readable article from the storyline for the intake's audience and
depth (an overview brief is about 600-900 words; a practical guide may be
longer): title, a lead paragraph stating the core message, the SCQA as the
opening, one `##` section per content section (headline as the heading, bullets
turned into prose with `[n]` markers), a "What you can do" section as a
numbered list, then `## Sources` (the numbered list from sources.md). Images
as `![caption](assets/x.jpg)` with a credit line under each. Add only what the
findings and sources support.

## Render

```bash
/opt/homebrew/bin/pandoc <stem>-article.md -o <stem>-article.docx
```

(Run from the `deliverables/` directory so image paths resolve. `pandoc` on
PATH works too.) No LibreOffice; do not convert to PDF.

## Verify

Reopen the docx: `/opt/homebrew/bin/pandoc <stem>-article.docx -t plain | head`
shows the title and sections; every `[n]` resolves to a Sources entry; word
count fits the depth.
