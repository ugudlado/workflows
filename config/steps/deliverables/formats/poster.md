# Format: poster

Output: `deliverables/<stem>-poster.pdf` and `<stem>-poster.png` (one page,
portrait, 1190x1684 px, A-series ratio).

## Build

A Marp deck with ONE slide and a custom theme that sets the page size. The size
must come from a theme file passed with `--theme`; an inline `<style>` or
front-matter `style:` does not change the page size (PNG stays 1280x720).

`poster-theme.css`:

```css
/* @theme poster */
@import 'default';
section { width: 1190px; height: 1684px; padding: 60px; font-size: 34px; }
h1 { font-size: 76px; }
```

`<stem>-poster.md` starts with `marp: true` and `theme: poster`. Layout, from
the storyline: core message as the title, the SCQA answer as a subtitle, 3-4
content headlines each with one short cited bullet (`[n]`), the key figures as
large numbers, the "What you can do" actions in a box, a hero image (local file
in `assets/`, credit in a small credits line), and a one-line sources list with
a pointer to the full source list. Large type, few words, high contrast.

## Render

```bash
npx -y @marp-team/marp-cli@4 <stem>-poster.md --theme poster-theme.css --allow-local-files --pdf -o <stem>-poster.pdf
npx -y @marp-team/marp-cli@4 <stem>-poster.md --theme poster-theme.css --allow-local-files --images png -o <stem>-poster.png   # writes <stem>-poster.001.png
```

Rename `<stem>-poster.001.png` to `<stem>-poster.png` after the check. If a
conversion shows no output after about 90 seconds, `pkill -f marp` and rerun.

## Render check (up to 3 rounds)

Read the poster PNG. Check the PNG is 1190x1684, then look for overflow past the
bottom or edges, clipped or overlapping text, an image covering text, empty
bands, tiny text. Fix the CSS/Markdown, re-render, read again. Stop when clean
or after 3 rounds; if issues remain, report failed. Report rounds and fixes.
