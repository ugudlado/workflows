# Format: editable-pptx

Output: `deliverables/<stem>-editable.pptx`, built with python-pptx (installed
for `python3`). Unlike the Marp .pptx (slides are flat images), every title,
bullet and note is real, editable text. The layout is NOT render-checked here
(no LibreOffice, and Marp cannot render this file); say so in the report.

## Build

```python
from pptx import Presentation
from pptx.util import Inches, Pt
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)   # 16:9
s = prs.slides.add_slide(prs.slide_layouts[5])                    # title only
s.shapes.title.text = "Headline"
tb = s.shapes.add_textbox(Inches(0.7), Inches(1.6), Inches(6.5), Inches(5))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.text = "bullet [1]"; p.font.size = Pt(22)
s.shapes.add_picture("assets/s2.jpg", Inches(7.6), Inches(1.6), width=Inches(5))
s.notes_slide.notes_text_frame.text = "Notes, citations, Photo by <name> on Unsplash, <url>"
prs.save("<stem>-editable.pptx")
```

Exactly 10 slides mapping 1:1 to the storyline sections, same theme on every
slide (set a background fill and font colours/sizes explicitly; keep bullets to
short lines at 20 pt or larger and at most 5 per slide, since overflow is not
checked). Images are local files from `assets/` with credits in notes; slide 10
lists the sources.

## Verify

Reopen with `Presentation("<stem>-editable.pptx")`: 10 slides, every content
slide has a title, text, a picture and notes. State in the report that visual
layout was not render-checked.
