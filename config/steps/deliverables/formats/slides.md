# Format: slides

Output: `deliverables/<stem>.md` (Marp source), `.html`, `.pdf`, `<stem>.001.png`
..`.010.png`, `.pptx` (image-based, NOT editable).

## Build

1. Write `<stem>.md` with Marp front matter (`marp: true`, `paginate: true`) and
   a topic-suited theme in a `<style>` block (palette, fonts, background),
   identical on every slide. Exactly 10 slides separated by `---`, mapping 1:1
   to the storyline's 10 sections: 1 title (topic as in intake.json plus an
   audience line), 2-9 content (headline as `##` title, the 3-5 bullets with
   `[n]` markers, one image), 10 sources (as in sources.md).
2. Speaker notes go in an HTML comment at the end of each slide:
   `<!-- supporting detail, citation numbers, and "Photo by <name> on Unsplash, <url>" -->`.
   Every content slide has notes (the video format reads them for narration).
3. Images: download to `assets/` and reference relatively
   (`![bg right:35%](assets/s2.jpg)`). Never hotlink.

## Render

Run from the `deliverables/` directory, one command per output. Marp drives the
installed Google Chrome; it must run outside any sandbox that blocks Chrome.

```bash
npx -y @marp-team/marp-cli@4 <stem>.md --allow-local-files --html -o <stem>.html
npx -y @marp-team/marp-cli@4 <stem>.md --allow-local-files --pdf -o <stem>.pdf
npx -y @marp-team/marp-cli@4 <stem>.md --allow-local-files --images png -o <stem>.png   # writes <stem>.001.png ...
npx -y @marp-team/marp-cli@4 <stem>.md --allow-local-files --pptx -o <stem>.pptx
```

Run commands as written (one Marp invocation per command, no shell variable
holding the flags: unquoted variable expansion breaks in zsh). If a conversion
shows no output after about 90 seconds, kill it (`pkill -f marp`) and run it again;
the first attempt after a kill can hang.

## Render check (up to 3 rounds)

After rendering PNGs, read EVERY slide PNG with the image-reading tool and look
for: text overflowing the slide or its box, clipped bullets, text over images
or other text, unreadable contrast, images covering text, empty slides. Fix the
Markdown/CSS (shorter bullets, smaller `font-size`, move the image), re-render
all outputs, read every PNG again. Stop when clean or after 3 rounds; if issues
remain, report failed. Report: rounds used, issues found and fixed per slide.

## Verify

Exactly 10 PNGs exist; the .pptx opens (python-pptx reports 10 slides); notes
present on slides 2-9; no URL beyond sources.md.
