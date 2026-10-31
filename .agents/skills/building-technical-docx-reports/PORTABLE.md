# building-technical-docx-reports — single-file skill

> Portable, self-contained edition of the `building-technical-docx-reports` agent skill.
> Everything is inlined below: the instructions, the three reference documents, the five
> scripts and the two example inputs. Nothing is fetched at runtime, with one exception: the
> optional Mermaid renderer loads `mermaid.min.js` from a CDN into headless Chromium. Offline, vendor
> that file locally and point the `<script src>` in `scripts/render_mermaid.js` at it.
>
> **How to use this file.** If you are an agent reading it: work through section 1 (the skill
> instructions), then write the files from sections 2-4 to disk under
> `skills/building-technical-docx-reports/` (or any working directory), keeping the exact
> relative paths shown in each heading, and follow the pipeline in section 1. If you cannot write
> files, treat the scripts as reference implementations and reproduce their behaviour.
>
> **Runtime:** Python 3.9+ (`python-docx`, `lxml`, `Pillow`), LibreOffice `soffice` on PATH,
> Node 18+ with Playwright + Chromium only for Mermaid rendering. The Carlito fonts are
> metric-compatible with Calibri and are required for correct pagination - install them from
> the system or from `assets/fonts/` in the full bundle.

## 0. Skill metadata (frontmatter)

```yaml
name: building-technical-docx-reports
description: Builds a designed, print-ready Word (.docx) technical report from a structured HTML source — cover band, shaded tables with repeating headers, screenshot-plus-prose rows, KPI strips, callouts, code blocks, Mermaid diagrams, a table of contents with real page numbers, running header and page numbers. Use when the deliverable is a long technical document as .docx (app or system documentation, architecture or audit report, technical manual, project dossier) and its visual design matters, or when a .docx must show UI screenshots and diagrams. Not for letters, invoices, forms, or short memos.
```

---

# 1. SKILL.md

# Building technical .docx reports

A repeatable pipeline for long technical documents whose design has to look deliberate: dark cover
band, navy/indigo headings, shaded table headers, screenshots paired with their explanation, KPI
strips, callouts, code blocks, diagrams, and an index with page numbers that actually match the pages.

## Contents
- Pipeline
- Quick start
- Five rules that keep the build honest
- Scripts
- Reference files
- Dependencies

## Pipeline

```
source.html  ──build_docx.py──▶  report.docx  ──fill_toc.py──▶  report.docx (numbered index)
     │                                │
     │ content only                   └──verify_docx.py──▶ structure/geometry PASS-FAIL
     └ assets/*.png, *.mmd                 check_layout.py──▶ page count, sparse pages, overflow
```

Content lives in HTML, design lives in the builder. That split is the whole point: the prose stays
diffable and re-editable, the same source can also be rendered to PDF, and the builder can never
invent or drop a sentence. `build_docx.py` aborts on any element it does not handle, so a new block
type fails loudly instead of silently vanishing from the document.

## Quick start

```bash
S=<skill>/scripts            # this skill's scripts/ directory
cd /path/to/project

cp <skill>/assets/config.example.json ./config.json          # then edit paths, palette, header
python3 $S/build_docx.py config.json                         # HTML -> DOCX
python3 $S/fill_toc.py report.docx                           # measure pages, number the index
python3 $S/verify_docx.py report.docx config.json            # must print ALL PASS
python3 $S/check_layout.py report.docx --min-lines 8         # must print LAYOUT OK
```

Diagrams first, if the document has any:

```bash
node $S/render_mermaid.js diagrams/arch.mmd diagrams/er.mmd --out assets --scale 3
```

`assets/source.example.html` + `assets/config.example.json` are a working demo of every block type:
copy both plus the two `example-*.png` files into a scratch directory, point `html` at the example,
and the four commands above produce a 5-page document that passes every check.

Then open the `.docx` once in a real Word (or LibreOffice) before delivering: the checks prove
structure and geometry, not that the design reads well.

## Five rules that keep the build honest

1. **Prose never enters the Python.** If a sentence is in `build_docx.py`, it is in the wrong file.
   The builder reads text, captions, figure paths and cover lines from the HTML.
2. **Unhandled element = hard stop.** Never add a silent `else: pass`. Either write the handler or
   list the class in `ignore_classes` deliberately.
3. **Measure, don't assume.** `verify_docx.py` catches dropped/reordered images, tables wider than
   the text column, cells whose longest word cannot fit, rows that split across pages, a missing
   cover line or TOC. `check_layout.py` catches the near-empty page that an orphaned bullet creates.
4. **Render with metric-compatible fonts.** Calibri is usually absent on Linux; Carlito is
   metric-identical and ships in `assets/fonts`. Without it, the width checks are fiction.
5. **Screenshots are captured at device resolution and scaled by width in the builder.** Never
   pre-resize a screenshot to "save space" — the builder keeps the aspect ratio and the print
   quality.

## Config

`config.json` is the only file you edit per document. Paths resolve against the config's directory
unless `base_dir` overrides it (useful when the HTML and its `assets/` live elsewhere).

| Key | Meaning |
|---|---|
| `html`, `out`, `base_dir` | source file, output `.docx`, root for image paths |
| `header_label`, `title`, `language` | running header text, document title, proofing language |
| `page` | `width_cm`, `height_cm`, `margin_cm`, `top_cm`, `bottom_cm` |
| `palette` | `navy`, `accent`, `slate`, `highlight`, `body`, `alt`, `grid`, `code_bg` (hex, no `#`) |
| `fonts` | `sans` (Calibri), `mono` (Consolas) |
| `table` | cell margins in twips — the main lever on pagination |
| `screen_width_cm` | width of a screenshot in a `div.screen` (7.2 fits a phone capture) |
| `figure_widths` | per-`src` width in cm for diagrams without an inline `width:` |
| `cover` | band height, title size, and which meta fields print large and in what order |
| `toc.depth` | `"1"` or `"1-2"` |
| `expect` | what `verify_docx.py` asserts: image list/order, figure/table/heading/code counts, cover strings |
| `ignore_classes` | classes to skip instead of aborting (use deliberately, never as a catch-all) |

## Scripts

| Script | Does | Fails loudly when |
|---|---|---|
| `scripts/build_docx.py` | HTML → styled DOCX (config-driven) | an element is unhandled, an image is missing |
| `scripts/fill_toc.py` | renders to PDF, finds each heading's page, writes the numbers into the index | no `TOC 1`/`TOC 2` paragraphs exist |
| `scripts/verify_docx.py` | structure + geometry checks against the config's `expect` block | any check fails (exit 1) |
| `scripts/check_layout.py` | page count, sparse pages, text past the margin, clipped images | reports, does not exit non-zero |
| `scripts/render_mermaid.js` | `.mmd`/`.html` → 3× PNG via Playwright | Mermaid fails to render |

## Reference files

- `references/html-contract.md` — every node type the builder accepts, with markup and rules.
- `references/ooxml-recipes.md` — the OOXML fragments behind the design (shading, borders, cell
  margins, repeating headers, field codes, schema ordering) and why each one is needed.
- `references/pitfalls.md` — the failures that actually happen, and the fix for each.

## Dependencies

`python-docx`, `beautifulsoup4`, `lxml`, `Pillow`, `pymupdf`, LibreOffice (`soffice`), Node with
Playwright (only for Mermaid). `validate.py` from the docx tooling is used when present.

---

# 2. Reference files

These are loaded on demand by the instructions above. Write each one to the path in its heading.

## `references/html-contract.md`

````markdown
# HTML source contract

The builder reads one HTML file and turns it into the document. This file is the complete list of
what it accepts; anything else aborts the build with the element name.

## Contents
- Document skeleton
- Cover — `section.cover`
- Index — `div.toc-page`
- Chapters — `section.chapter` / `section.chapter-flow`
- Headings
- Prose and inline markup
- Lists
- Tables
- Code blocks
- Diagrams — `figure.diagram`
- Screens — `div.screen`
- KPI strip — `div.kpis`
- Callouts — `div.note` / `div.warn`
- Rules that apply everywhere

## Document skeleton

```html
<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>…</title></head>
<body>
  <section class="cover"> … </section>
  <div class="toc-page"> … </div>
  <section class="chapter"> … </section>
  <section class="chapter-flow"> … </section>
</body></html>
```

`<script>` elements are removed before parsing, so a source written for the browser (with a
Paged.js or Mermaid tag) can be reused as-is. Only `<body>` is read.

## Cover — `section.cover`

```html
<section class="cover">
  <div class="brand"><div class="logo"></div>ACME · Platform</div>
  <div class="bar"></div>
  <h1>Acme</h1>
  <div class="subtitle">Documentación técnica de la plataforma: funcionalidades, funcionamiento…</div>
  <div class="meta">
    <b>Fecha:</b> 30 de octubre de 2026<br>
    <b>Frontend:</b> Android · Kotlin + Jetpack Compose<br>
    <b>Backend:</b> Rust · Axum + SQLx · PostgreSQL<br>
    <b>Repositorios:</b> acme/app (b307723) · acme/server (c47680c)<br><br>
    Nota al pie de portada, en cursiva y tamaño pequeño.
  </div>
</section>
```

The builder renders the band (navy, `cover.band_height_cm` tall), the brand line in the highlight
colour, the `h1` at `cover.title_pt` with a highlight rule under it, the subtitle, then the meta
lines. `div.logo` and `div.bar` are ignored (they exist for the PDF/HTML render).

Meta parsing: each `<b>Label:</b>` starts a field, the text after it is the value, `<br>` separates
fields. Text that follows the last field without a label becomes the cover note. Which fields get
the larger size, and in which order they print, is set by `cover.meta_groups` in the config — any
field not listed still prints, after the grouped ones, at the small size.

## Index — `div.toc-page`

```html
<div class="toc-page"><h2>Índice</h2></div>
```

That is all it needs: the entries are generated from the document's own `h1`/`h2` headings, in
order, with the `span.num` prefix preserved. `toc.depth` (`"1"` or `"1-2"`) controls whether
second-level headings are listed. Do not hand-write the entries — they would drift from the body.

## Chapters — `section.chapter` / `section.chapter-flow`

Both class names are accepted and behave identically; the distinction only matters for the HTML/PDF
render. Each chapter starts with an `h1`, which forces a page break and draws the rule under it.
Content order inside a chapter is preserved exactly.

## Headings

```html
<h1 id="s2"><span class="num">2.</span>Visión general y arquitectura</h1>
<h2>2.1 Backend: capas «handler → SQL»</h2>
<h3>Login</h3>
```

`span.num` is optional; when present its text is prepended to the heading and to the index entry.
Numbering is manual by design — it is content, and the author decides it. `h2`/`h3` must not carry
a `span.num` (their number is part of the text).

## Prose and inline markup

`<p>` becomes a body paragraph. Inside any paragraph, table cell, caption or list item the builder
understands:

| Markup | Result |
|---|---|
| `<strong>` / `<b>` | bold |
| `<em>` | italic |
| `<code>` | inline code (mono, indigo, smaller) |
| `<span style="color:#RRGGBB">` | coloured run |
| `<br>` | line break inside the paragraph |

Whitespace is collapsed to single spaces and the paragraph's first/last run is trimmed, so
pretty-printed HTML does not produce ragged text. Markdown syntax is **not** interpreted: `**bold**`
stays literal and `verify_docx.py` fails on it.

## Lists

`<ul>` and `<ol>` with direct `<li>` children. Ordered lists restart at 1 for every list (each one
gets its own numbering instance), so a chapter can hold several independent step lists. Inline
markup inside `<li>` works as above.

## Tables

```html
<table>
  <caption data-label="Tabla 1">Módulos del backend y su responsabilidad</caption>
  <thead><tr><th>Módulo</th><th class="r">Líneas</th><th>Responsabilidad</th></tr></thead>
  <tbody>
    <tr><td><code>main.rs</code></td><td class="r">119</td><td>Arranque, pool, migraciones</td></tr>
  </tbody>
</table>
```

- `caption[data-label]` prints as a bold label plus the caption text, above the table, kept with it.
- A row made only of `<th>` is the header row: indigo fill, white bold text, and it repeats on every
  page the table spans.
- `class="r"` right-aligns a cell, `class="c"` centres it. Use `r` for numbers.
- Body rows alternate between white and `palette.alt`.
- Column widths are computed from content: the longest unbreakable token sets the floor, and
  `style="width:35%"` on a `<th>` sets that column's preference. Do not hand-set widths on `<td>`.
- Every row is marked "do not split across pages", so a tall row moves whole to the next page.

## Code blocks

```html
<pre>GET /api/notes
Authorization: Bearer &lt;jwt&gt;</pre>
```

Rendered as one shaded, left-ruled paragraph with hard line breaks — so it never breaks across
pages mid-block, and copy-paste from Word keeps the lines. Escape `<` and `&` as usual HTML.

## Diagrams — `figure.diagram`

```html
<figure class="diagram">
  <img alt="Diagrama de componentes" src="assets/arch.png" style="width: 13cm;">
  <figcaption data-label="Figura 1">Diagrama de componentes: app ↔ API ↔ PostgreSQL</figcaption>
</figure>
```

Width comes from `style="width: Xcm"`, else from `figure_widths` in the config keyed by `src`, else
the full text width. Height is derived from the file's real pixel size, so the aspect ratio is
always exact. Produce the PNG with `scripts/render_mermaid.js` (3× scale) or any other tool.

## Screens — `div.screen`

A screenshot on the left and its explanation on the right, in a borderless two-column table.

```html
<div class="screen">
  <figure>
    <img alt="Pantalla de login" src="assets/01_login.png">
    <figcaption data-label="Figura 2">Pantalla de acceso (login)</figcaption>
  </figure>
  <div class="desc">
    <div class="tagline">AuthScreen · modo «Acceso»</div>
    <h3>Login</h3>
    <p>Es la primera pantalla cuando no hay sesión guardada…</p>
    <ul><li><strong>Selector Acceso / Registro</strong> arriba a la derecha.</li></ul>
  </div>
</div>
```

The image is scaled to `screen_width_cm` (7.2 cm fits a 1080×2400 phone capture beside a readable
prose column). The caption sits under the image, inside the same cell. The right column accepts
`div.tagline`, `h3`, `p`, `ul`, `ol` — in any order, repeated as needed.

## KPI strip — `div.kpis`

```html
<div class="kpis">
  <div class="kpi"><b>21</b><span>endpoints REST<br>(4 públicos · 17 con JWT)</span></div>
  <div class="kpi"><b>5</b><span>tablas en<br>PostgreSQL</span></div>
</div>
```

One row of equal cells, each with a big number and a small label, separated by white gutters and a
highlight rule on top. Keep it to 3–5 items; more than that and the numbers stop being readable at
print size.

## Callouts — `div.note` / `div.warn`

```html
<div class="note"><p><strong>Estado del proyecto.</strong> Texto…</p></div>
<div class="warn"><p>Texto…</p></div>
```

Each `<p>` inside becomes a shaded, left-ruled block (indigo for `note`, amber for `warn`). Keep a
callout to one or two paragraphs; it is a margin note, not a section.

## Rules that apply everywhere

- **Image paths** resolve against `base_dir` (the config's directory unless `base_dir` says
  otherwise). A missing file aborts the build with its path.
- **`data-label`** is the figure/table number as the author wants it printed ("Figura 7",
  "Tabla 12"). The builder does not renumber — the HTML stays the single source of numbering, so
  inserting a figure means updating the labels that follow it.
- **No prose in the builder, no design in the HTML.** Classes carry meaning (what the block *is*),
  never appearance (no `style="color:…"` on blocks, no font sizes). The one exception is
  `width: Xcm` on a diagram `<img>`, which is a layout decision about that specific figure.
- **Alt text on every `<img>`.** It is not used by the DOCX, but the same source feeds the HTML/PDF
  render and accessibility there.
````

---

## `references/ooxml-recipes.md`

````markdown
# OOXML recipes behind the design

python-docx covers paragraphs, runs, tables and images; everything that makes the document look
designed is raw OOXML appended to property elements. These are the fragments, with the reason each
one exists. All of them are already implemented in `scripts/build_docx.py` — this file is for when
you need to change or extend the design.

## Contents
- The `el()` helper and namespaces
- Shading a cell or paragraph
- Borders on a paragraph
- Table borders, cell margins, fixed widths
- Repeating header rows and rows that never split
- Field codes: page numbers and the index
- Restarting ordered lists
- Schema ordering — the one thing that breaks Word silently
- Fonts and the `w:zoom` attribute

## The `el()` helper and namespaces

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def el(tag, **attrs):
    e = OxmlElement(tag)                      # tag without prefix, e.g. "w:shd"
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e
```

`OxmlElement("w:shd")` maps the `w:` prefix to the wordprocessingml namespace; `qn()` does the same
for attribute names. Never build these strings by hand — a wrong namespace URI produces a file Word
refuses to open with no useful message.

## Shading a cell or paragraph

```python
pr.append(el("w:shd", val="clear", color="auto", fill="36519E"))
```

`fill` is the background, `color` is the pattern colour (only relevant when `val` is a pattern, so
`"auto"` is right for solid fills). Applies to `<w:tcPr>` for cells and `<w:pPr>` for paragraphs.
Remove any existing `<w:shd>` first, or you get two and Word uses the first.

## Borders on a paragraph

```python
def pborder(ppr, side, sz, color, space=4):
    b = ppr.find(qn("w:pBdr"))
    if b is None:
        b = el("w:pBdr"); ppr.append(b)
    b.append(el("w:" + side, val="single", sz=sz, space=space, color=color))
```

`sz` is eighths of a point (12 ≈ 1.5 pt), `space` is the gap in points between the rule and the
text. Sides: `top`, `left`, `bottom`, `right`, `between`, `bar`. This is how the heading rule, the
code block's left bar, the callout box and the cover's underline are drawn — no images involved.

## Table borders, cell margins, fixed widths

```python
# all six borders, or val="nil" for none
b = el("w:tblBorders")
for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
    b.append(el("w:" + side, val="single", sz=4, space=0, color="C9D1DE"))
tbl._tbl.tblPr.append(b)

# padding inside every cell, in twentieths of a point (twips)
m = el("w:tblCellMar")
for side, v in (("top", 30), ("left", 90), ("bottom", 30), ("right", 90)):
    m.append(el("w:" + side, w=v, type="dxa"))
tbl._tbl.tblPr.append(m)
```

Cell margins are the single most effective lever on pagination: at 100 twips a long table pushes a
row onto a fresh page and leaves a nearly empty page behind; at 30–90 it fits. That is why the
default is tight.

Fixed widths need three coordinated writes — the table width, the grid, and every cell:

```python
tbl.autofit = False
tw = tblPr.find(qn("w:tblW")) or el("w:tblW")
tw.set(qn("w:w"), str(int(sum(widths_cm) / 2.54 * 1440))); tw.set(qn("w:type"), "dxa")
for gc, w in zip(tbl._tbl.tblGrid.findall(qn("w:gridCol")), widths_cm):
    gc.set(qn("w:w"), str(int(w / 2.54 * 1440)))
for row in tbl.rows:
    for c, w in zip(row.cells, widths_cm):
        c.width = Cm(w)
```

Set only the grid and Word redistributes on edit; set only the cells and the grid still wins on
first layout. 1440 twips = 1 inch = 2.54 cm.

## Repeating header rows and rows that never split

```python
trPr = row._tr.get_or_add_trPr()
trPr.append(el("w:cantSplit"))     # the row moves whole to the next page
trPr.append(el("w:tblHeader"))     # this row repeats at the top of every page
```

`tblHeader` on the first row is what makes a 40-row table readable across pages. `cantSplit` on
every row prevents the ugly half-row break. `verify_docx.py` checks both, and counts data tables by
the presence of `tblHeader`.

## Field codes: page numbers and the index

A field is three runs: `begin`, the instruction, `separate`, the cached result, `end`.

```python
def field_run(p, kind, instr=None):
    r = p.add_run()
    if instr is None:
        r._r.append(el("w:fldChar", fldCharType=kind))
    else:
        it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr
        r._r.append(it)

field_run(p, "begin"); field_run(p, "x", " PAGE "); field_run(p, "separate")
p.add_run("1")                      # cached result — what a viewer shows before refreshing
field_run(p, "end")
```

The footer uses `PAGE`. The index uses ` TOC \o "1-2" \h \u ` — but with a **static result region**:
the `begin`/`separate` pair sits in one paragraph, then one `TOC 1`/`TOC 2` paragraph per heading,
then `end` in a final paragraph. Fields may span paragraphs, and this gives the best of both:

- every viewer (Word, LibreOffice, Google Docs, PDF export) shows the entries immediately, with no
  "update this field" placeholder;
- Word can still refresh it with F9 and regenerate the same structure.

`scripts/fill_toc.py` then replaces the placeholder numbers with the real page numbers measured
from the rendered PDF. Do not skip that step — a TOC full of `1`s is worse than no TOC.

## Restarting ordered lists

python-docx's `List Number` style shares one numbering instance, so every `<ol>` would continue
1, 2, 3… across the document. Each list gets its own `<w:num>` pointing at the same abstract
definition, with a start override:

```python
num = el("w:num", numId=new_id)
num.append(el("w:abstractNumId", val=abstract_id))
ov = el("w:lvlOverride", ilvl=0); ov.append(el("w:startOverride", val=1)); num.append(ov)
numbering.append(num)
# then on the paragraph: <w:numPr><w:ilvl w:val="0"/><w:numId w:val="new_id"/></w:numPr>
```

## Schema ordering — the one thing that breaks Word silently

`w:pPr`, `w:rPr`, `w:tcPr` and `w:tblPr` are **sequences**, not sets: children must appear in the
schema's order. python-docx appends at the end, so a `<w:shd>` added after `<w:spacing>` lands in
the wrong place. Word may open the file anyway, or refuse it, or drop the property — and
`validate.py` reports it as `Element 'w:ind': This element is not expected`.

The builder therefore re-sorts every property element against an explicit order table before saving
(`ORDER` in `build_docx.py`, covering `pPr`, `rPr`, `tblPr`, `pBdr`, `tcBorders`, `tcPr`). If you
add a new property, add it to that table in its schema position — for example `ind` belongs between
`spacing` and `contextualSpacing`.

## Fonts and the `w:zoom` attribute

Set fonts on all four slots, or Word substitutes per script:

```python
rf = rpr.find(qn("w:rFonts")) or el("w:rFonts")
for a in ("ascii", "hAnsi", "cs", "eastAsia"):
    rf.set(qn("w:" + a), name)
for a in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
    rf.attrib.pop(qn("w:" + a), None)     # a theme font overrides the explicit one
```

Finally, python-docx writes `<w:zoom w:val="0"/>` in `settings.xml`, which some validators reject
because `w:percent` is required. One line before `doc.save()`:

```python
for z in doc.settings.element.findall(qn("w:zoom")):
    z.set(qn("w:percent"), "100")
```
````

---

## `references/pitfalls.md`

````markdown
# Pitfalls and their fixes

Every item here was hit in production while building a 47-page technical document. They are ordered
by how much time they cost when you meet them unprepared.

## Contents
- Calibri is not installed, so the layout checks lie
- The index shows "update this field" instead of entries
- A table runs past the right margin
- A cell's longest word cannot fit and the column explodes
- A nearly empty page appears at the end of a chapter
- An image is stretched, or is missing from the build
- Word refuses the file, or silently drops a property
- LibreOffice and Word paginate differently
- Mermaid renders blank
- The document is 47 pages and nobody knows why

## Calibri is not installed, so the layout checks lie

Calibri ships with Office, not with Linux. LibreOffice substitutes DejaVu Sans, which is ~8% wider,
so every width measurement and every page break is wrong — tables that fit in Word overflow in the
render, and vice versa.

Fix: install Carlito (metric-compatible with Calibri, OFL licensed). It ships in
`assets/fonts/`; copy it to `~/.fonts/` and refresh the cache:

```bash
mkdir -p ~/.fonts && cp assets/fonts/Carlito-*.ttf ~/.fonts/ && fc-cache -f
```

Consolas has no metric clone, so inline code renders in DejaVu Sans Mono on Linux: wider, and it
reads as slightly letter-spaced next to Carlito. That is a render artefact, not a document defect —
in Word with real Consolas it tightens up. Do not "fix" it by changing the code font size.

`verify_docx.py` measures unbreakable tokens with Carlito when it can find it, and prints
`SKIP token-width check` when it cannot — treat that SKIP as a failure of the environment, not as a
pass. The mono estimate uses 0.55 em, which is close enough for a column-width check.

## The index shows "update this field" instead of entries

A bare `TOC` field has no cached result, so every viewer that does not auto-update shows the
placeholder text. Word only fills it on F9 or on print, and LibreOffice's PDF export shows the
placeholder verbatim — which is what ends up in the delivered PDF.

Fix: give the field a static result region (see `references/ooxml-recipes.md`) and number it with
`scripts/fill_toc.py`. If you edit the document afterwards, re-run `fill_toc.py`; the numbers are
measurements, not constants.

## A table runs past the right margin

Usually one of three causes: `autofit` left on, a `<w:tblW>` in `pct` rather than `dxa`, or widths
set on cells but not on the grid. All three are handled by `fixed_widths()`; the check is
`verify_docx.py`'s "no table wider than the text column", which sums the grid columns and compares
against `page.width_cm - 2 * margin_cm`.

If a table is *legitimately* wider (a wide comparison matrix), do not fight it — split it into two
tables or drop a column. A table that needs landscape is a signal the content is wrong for the page.

## A cell's longest word cannot fit and the column explodes

Word will not hyphenate an unbreakable token (a URL, `POST /api/notes/{id}/attachments`, a long
identifier). If the column is narrower than that token, Word widens the column and the table
overflows — even though the grid says otherwise.

Fix: the width algorithm in `build_docx.py` measures the longest token per column and uses it as a
floor. When it still fails, the token is genuinely too long for the page: insert a zero-width space
(`&#8203;`) at a sensible break point in the HTML, or shorten the token. `verify_docx.py` lists the
offending token, its width and the available width, so you know which one to fix.

## A nearly empty page appears at the end of a chapter

Two orphaned bullets, or a single table row, pushed onto a fresh page. The cause is cumulative
height: cell margins, paragraph spacing, and `keep_with_next` on captions.

Fix, in order of preference:

1. Tighten cell margins — `table.cell_margin_*` in the config. Going from 100 to 30 twips routinely
   removes a page from a long document.
2. Reduce `space_after` on the list style, or the caption's `space_before`.
3. Accept it if the page holds a real block (a diagram, a code listing) — `check_layout.py` only
   flags pages with fewer than `--min-lines` lines *and* no image.

Do not "fix" it by deleting content or by shrinking the body font.

## An image is stretched, or is missing from the build

Stretching comes from passing both a width and a height that do not match the file's aspect ratio.
The builder always computes height from the real pixel size (`Image.open(path).size`), so this only
happens if you bypass `picture_para()`.

A missing image aborts the build with its path — that is deliberate. The alternative (skip silently)
produces a document that looks complete and is not.

## Word refuses the file, or silently drops a property

Schema ordering. See the ordering section in `references/ooxml-recipes.md`. Run `validate.py` on the
output; a single `Element 'w:ind': This element is not expected` means one property is in the wrong
position, and Word's behaviour in that state is undefined.

Known false positive: `w:zoom` without `w:percent` — fixed in the builder, but if you write your own
save step, set it.

## LibreOffice and Word paginate differently

They will never agree exactly: line breaking of long words, table row heights and widow/orphan
handling all differ slightly. A 47-page LibreOffice render can be 46 or 48 in Word.

Practical rule: use the LibreOffice render for *relative* checks (is this page nearly empty, does
this table overflow) and never promise an exact page count to the user. If the count matters, open
the file in Word once and adjust.

## Mermaid renders blank

`render_mermaid.js` waits for `.mermaid svg`; a syntax error in the diagram means that selector never
appears and the script times out after 30 s. Two causes: a node label containing an unescaped quote
or parenthesis, or a `%%{init}%%` directive placed after the diagram type instead of before it.

Also: the script loads Mermaid from a CDN. On a machine without outbound access, vendor
`mermaid.min.js` locally and point the `<script src>` at the file.

## The document is 47 pages and nobody knows why

Normal for a document with 12 chapters, 39 tables and 14 figures. What matters is that no page is
wasted: `check_layout.py` prints the line count per page, so a page with 7 lines stands out
immediately against neighbours with 60. Fix those, not the total.
````

---

## `scripts/build_docx.py`

````python
#!/usr/bin/env python3
"""Build a styled, print-ready .docx technical report from a structured HTML source.

The HTML is the single source of truth for content (prose, tables, captions, figure
paths, cover text). This script owns only the *design*: page setup, styles, OOXML
shading/borders, table geometry, cover band, TOC field, header/footer.

Usage:
    python3 build_docx.py config.json [--out other.docx]

Config keys (all optional except "html"): see references/html-contract.md and the
DEFAULTS dict below. Relative paths resolve against the config file's directory.

Design contract: every content element in the HTML must be one of the handled
node types (see references/html-contract.md). An unhandled element aborts the build
with its name, so the source never silently loses content.
"""
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

DEFAULTS = {
    "html": "source.html",
    "out": "report.docx",
    "header_label": "",
    "title": "",
    "language": "es-ES",
    "page": {"width_cm": 21.0, "height_cm": 29.7, "margin_cm": 2.2,
             "top_cm": 2.3, "bottom_cm": 2.0},
    "palette": {"navy": "122440", "accent": "36519E", "slate": "5B6B82",
                "highlight": "C3DC3A", "body": "1F2937", "alt": "F2F4F8",
                "grid": "C9D1DE", "code_bg": "F3F6FB"},
    "fonts": {"sans": "Calibri", "mono": "Consolas"},
    "body_pt": 10.5,
    "screen_width_cm": 7.2,
    "table": {"cell_margin_top": 30, "cell_margin_bottom": 30,
              "cell_margin_left": 90, "cell_margin_right": 90},
    "figure_widths": {},
    "cover": {"band_height_cm": 14.5, "title_pt": 66,
              "meta_groups": [["Frontend", "Backend"], ["Fecha", "Repositorios"]],
              "meta_sizes": [13, 11]},
    "toc": {"depth": "1-2"},
    "ignore_classes": [],
}


def die(msg):
    sys.exit("build_docx.py: " + msg)


def deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path):
    cfg = json.load(open(path, encoding="utf-8"))
    cfg = deep_merge(DEFAULTS, cfg)
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def main():
    if len(sys.argv) < 2:
        die("usage: build_docx.py config.json [--out file.docx]")
    cfg = load_config(sys.argv[1])
    base = cfg.get("base_dir") or cfg["_dir"]
    if not os.path.isabs(base):
        base = os.path.join(cfg["_dir"], base)
    out = cfg["out"] if not os.path.isabs(cfg["out"]) else cfg["out"]
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    elif not os.path.isabs(out):
        out = os.path.join(base, out)

    html_path = cfg["html"] if os.path.isabs(cfg["html"]) else os.path.join(base, cfg["html"])
    if not os.path.exists(html_path):
        die("html source not found: " + html_path)

    P = cfg["palette"]
    NAVY, INDIGO, SLATE, LIME = P["navy"], P["accent"], P["slate"], P["highlight"]
    BODY, ALT, GRID, CODEBG = P["body"], P["alt"], P["grid"], P["code_bg"]
    MONO, SANS = cfg["fonts"]["mono"], cfg["fonts"]["sans"]
    pg = cfg["page"]
    PAGE_W, MARG = pg["width_cm"], pg["margin_cm"]
    TEXT_W = PAGE_W - 2 * MARG

    soup = BeautifulSoup(open(html_path, encoding="utf-8").read(), "html.parser")
    body = soup.body or soup
    for s in body.find_all("script"):
        s.decompose()

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(PAGE_W), Cm(pg["height_cm"])
    sec.left_margin = sec.right_margin = Cm(MARG)
    sec.top_margin, sec.bottom_margin = Cm(pg["top_cm"]), Cm(pg["bottom_cm"])
    sec.header_distance, sec.footer_distance = Cm(1.0), Cm(1.0)

    # ---------------------------------------------------------------- helpers
    def el(tag, **attrs):
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(qn("w:" + k), str(v))
        return e

    def rgb(h):
        return RGBColor.from_string(h)

    def set_fonts(rpr_owner, name):
        rpr = rpr_owner.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = el("w:rFonts")
            rpr.insert(0, rf)
        for a in ("ascii", "hAnsi", "cs", "eastAsia"):
            rf.set(qn("w:" + a), name)
        for a in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            rf.attrib.pop(qn("w:" + a), None)

    def shade(pr, fill):
        for old in pr.findall(qn("w:shd")):
            pr.remove(old)
        pr.append(el("w:shd", val="clear", color="auto", fill=fill))

    def pborder(ppr, side, sz, color, space=4):
        b = ppr.find(qn("w:pBdr"))
        if b is None:
            b = el("w:pBdr")
            ppr.append(b)
        b.append(el("w:" + side, val="single", sz=sz, space=space, color=color))

    # ---------------------------------------------------------------- styles
    st = doc.styles
    normal = st["Normal"]
    normal.font.name = SANS
    set_fonts(normal.element, SANS)
    normal.font.size = Pt(cfg["body_pt"])
    normal.font.color.rgb = rgb(BODY)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.2

    for lvl, sz, before, after, color in ((1, 20, 0, 14, NAVY), (2, 14, 16, 6, INDIGO),
                                          (3, 12, 10, 4, INDIGO)):
        hs = st["Heading %d" % lvl]
        hs.font.name = SANS
        set_fonts(hs.element, SANS)
        hs.font.size = Pt(sz)
        hs.font.bold = True
        hs.font.italic = False
        hs.font.color.rgb = rgb(color)
        pf = hs.paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.keep_with_next = True
        pf.line_spacing = 1.1
    st["Heading 1"].paragraph_format.page_break_before = True
    pborder(st["Heading 1"].element.get_or_add_pPr(), "bottom", 12, INDIGO, 6)

    def add_pstyle(name, base="Normal"):
        s = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        s.base_style = st[base]
        return s

    cap = st["Caption"]
    cap.font.name = SANS
    set_fonts(cap.element, SANS)
    cap.font.size = Pt(9)
    cap.font.italic = True
    cap.font.bold = False
    cap.font.color.rgb = rgb(SLATE)
    cap.paragraph_format.space_before = Pt(4)
    cap.paragraph_format.space_after = Pt(12)
    cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    tcap = add_pstyle("Table Caption", "Caption")
    tcap.paragraph_format.space_before = Pt(10)
    tcap.paragraph_format.space_after = Pt(4)
    tcap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    tcap.paragraph_format.keep_with_next = True

    code = add_pstyle("Code Block")
    code.font.name = MONO
    set_fonts(code.element, MONO)
    code.font.size = Pt(8)
    code.font.color.rgb = rgb("1E293B")
    cpf = code.paragraph_format
    cpf.space_before, cpf.space_after, cpf.line_spacing = Pt(6), Pt(10), 1.05
    cpf.left_indent, cpf.right_indent = Cm(0.35), Cm(0.1)
    cppr = code.element.get_or_add_pPr()
    pborder(cppr, "top", 4, CODEBG, 4)
    pborder(cppr, "left", 24, INDIGO, 8)
    pborder(cppr, "bottom", 4, CODEBG, 4)
    pborder(cppr, "right", 4, CODEBG, 4)
    shade(cppr, CODEBG)

    ic = st.add_style("Inline Code", WD_STYLE_TYPE.CHARACTER)
    ic.font.name = MONO
    set_fonts(ic.element, MONO)
    ic.font.size = Pt(9)
    ic.font.color.rgb = rgb("2B3F7A")
    tic = st.add_style("Table Code", WD_STYLE_TYPE.CHARACTER)
    tic.base_style = ic
    tic.font.size = Pt(8)

    tcell = add_pstyle("Table Text")
    tcell.font.size = Pt(9)
    tcell.paragraph_format.space_after = Pt(0)
    tcell.paragraph_format.space_before = Pt(0)
    tcell.paragraph_format.line_spacing = 1.1

    tag_st = add_pstyle("Screen Tagline")
    tag_st.font.size = Pt(8.5)
    tag_st.font.bold = True
    tag_st.font.color.rgb = rgb(SLATE)
    tag_st.font.all_caps = True
    tag_st.paragraph_format.space_after = Pt(0)
    tag_st.paragraph_format.keep_with_next = True

    toc_title = add_pstyle("TOC Title")
    toc_title.font.size = Pt(22)
    toc_title.font.bold = True
    toc_title.font.color.rgb = rgb(NAVY)
    toc_title.paragraph_format.space_after = Pt(16)
    pborder(toc_title.element.get_or_add_pPr(), "bottom", 12, INDIGO, 6)

    for lst in ("List Bullet", "List Number"):
        st[lst].paragraph_format.space_after = Pt(3)
        st[lst].paragraph_format.line_spacing = 1.2

    for i, (sz, bold, color, ind, before) in enumerate(
            ((11, True, NAVY, 0, 6), (10, False, BODY, 0.6, 0)), 1):
        try:
            ts = st["TOC %d" % i]
        except KeyError:
            ts = st.add_style("TOC %d" % i, WD_STYLE_TYPE.PARAGRAPH)
            ts.base_style = normal
        ts.font.size = Pt(sz)
        ts.font.bold = bold
        ts.font.color.rgb = rgb(color)
        ts.paragraph_format.left_indent = Cm(ind)
        ts.paragraph_format.space_before = Pt(before)
        ts.paragraph_format.space_after = Pt(2)
        ppr = ts.element.get_or_add_pPr()
        tb = el("w:tabs")
        tb.append(el("w:tab", val="right", leader="dot", pos=int(TEXT_W / 2.54 * 1440) - 10))
        ppr.append(tb)

    # ---------------------------------------------------------------- inline
    WS = re.compile(r"\s+")

    def add_inline(p, node, fmt=None):
        fmt = dict(fmt or {})
        if isinstance(node, NavigableString):
            txt = WS.sub(" ", str(node))
            if not txt:
                return
            r = p.add_run(txt)
            if fmt.get("code"):
                r.style = tic if fmt.get("table") else ic
            if fmt.get("bold"):
                r.bold = True
            if fmt.get("italic"):
                r.italic = True
            if fmt.get("color"):
                r.font.color.rgb = rgb(fmt["color"])
            if fmt.get("size"):
                r.font.size = Pt(fmt["size"])
            return
        if not isinstance(node, Tag):
            return
        n = node.name
        if n == "br":
            p.add_run().add_break()
            return
        if n in ("strong", "b"):
            fmt["bold"] = True
        if n == "em":
            fmt["italic"] = True
        if n == "code":
            fmt["code"] = True
            if "#fff" in (node.get("style") or ""):
                fmt["color"] = "FFFFFF"
        if n == "span":
            m = re.search(r"color:\s*#([0-9A-Fa-f]{6})", node.get("style") or "")
            if m:
                fmt["color"] = m.group(1).upper()
        for c in node.children:
            add_inline(p, c, fmt)

    def tidy(p):
        runs = p.runs
        if runs:
            runs[0].text = runs[0].text.lstrip()
            runs[-1].text = runs[-1].text.rstrip()

    def para_from(container, node, style=None, fmt=None):
        p = container.add_paragraph(style=style)
        for c in node.children:
            add_inline(p, c, fmt)
        tidy(p)
        return p

    # ---------------------------------------------------------------- lists
    numbering = doc.part.numbering_part.element
    LN_NUMID = st["List Number"].element.pPr.numPr.numId.val
    abs_id = None
    for nm in numbering.findall(qn("w:num")):
        if nm.get(qn("w:numId")) == str(LN_NUMID):
            abs_id = nm.find(qn("w:abstractNumId")).get(qn("w:val"))
    next_num = [max(int(x.get(qn("w:numId"))) for x in numbering.findall(qn("w:num"))) + 1]

    def new_num():
        nid = next_num[0]
        next_num[0] += 1
        num = el("w:num", numId=nid)
        num.append(el("w:abstractNumId", val=abs_id))
        ov = el("w:lvlOverride", ilvl=0)
        ov.append(el("w:startOverride", val=1))
        num.append(ov)
        numbering.append(num)
        return nid

    def add_list(container, node):
        ordered = node.name == "ol"
        nid = new_num() if ordered else None
        for li in node.find_all("li", recursive=False):
            p = para_from(container, li, "List Number" if ordered else "List Bullet")
            if ordered:
                ppr = p._p.get_or_add_pPr()
                npr = el("w:numPr")
                npr.append(el("w:ilvl", val=0))
                npr.append(el("w:numId", val=nid))
                ppr.insert(1 if ppr.find(qn("w:pStyle")) is not None else 0, npr)

    # ---------------------------------------------------------------- tables
    def cell_margins(tbl, top=60, bottom=60, left=100, right=100):
        m = el("w:tblCellMar")
        for side, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
            m.append(el("w:" + side, w=v, type="dxa"))
        tbl._tbl.tblPr.append(m)

    def tbl_borders(tbl, color=GRID, sz=4):
        b = el("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b.append(el("w:" + side, val="single", sz=sz, space=0, color=color))
        tbl._tbl.tblPr.append(b)

    def no_borders(tbl):
        b = el("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            b.append(el("w:" + side, val="nil"))
        tbl._tbl.tblPr.append(b)

    def fixed_widths(tbl, widths_cm):
        tbl.autofit = False
        tblPr = tbl._tbl.tblPr
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = el("w:tblW")
            tblPr.append(tw)
        tw.set(qn("w:w"), str(int(sum(widths_cm) / 2.54 * 1440)))
        tw.set(qn("w:type"), "dxa")
        grid = tbl._tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), widths_cm):
            gc.set(qn("w:w"), str(int(w / 2.54 * 1440)))
        for row in tbl.rows:
            for c, w in zip(row.cells, widths_cm):
                c.width = Cm(w)

    def row_flags(row, header=False):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(el("w:cantSplit"))
        if header:
            trPr.append(el("w:tblHeader"))

    def cell_fill(cell, fill):
        shade(cell._tc.get_or_add_tcPr(), fill)

    def col_widths(tbl_node, ncols):
        """Content-aware column widths: widest unbreakable token sets the floor,
        `width:N%` on a <th> sets the preference, slack is spread by preference."""
        rows = tbl_node.find_all("tr")
        ths = rows[0].find_all(["th", "td"])
        pref = {}
        for i, th in enumerate(ths):
            m = re.search(r"width:\s*(\d+)%", th.get("style") or "")
            if m:
                pref[i] = float(m.group(1)) / 100 * TEXT_W
        minw, weight = [0.0] * ncols, [0.0] * ncols
        for r in rows:
            for i, c in enumerate(r.find_all(["th", "td"])[:ncols]):
                t = WS.sub(" ", c.get_text()).strip()
                codes = " ".join(x.get_text() for x in c.find_all("code"))
                for wd in t.split():
                    mono = wd in codes
                    per = 0.165 if mono else (0.19 if c.name == "th" else 0.17)
                    minw[i] = max(minw[i], len(wd) * per + 0.5)
                weight[i] = max(weight[i], min(len(t), 70))
        w = list(minw)
        extra = TEXT_W - sum(w)
        # Columns without an explicit width:% get a share proportional to how much text
        # they actually hold — equal shares leave long prose columns cramped.
        wt = [pref[i] if i in pref else None for i in range(ncols)]
        free = [i for i in range(ncols) if wt[i] is None]
        if free:
            known = sum(x for x in wt if x is not None)
            tot = sum(weight[i] for i in free) or 1.0
            for i in free:
                wt[i] = max((TEXT_W - known) * weight[i] / tot, minw[i])
        wt = [max(x, 1.2) for x in wt]
        if extra > 0:
            lack = [max(wt[i] - w[i], 0) for i in range(ncols)]
            tl = sum(lack)
            if tl > 0:
                k = min(1.0, extra / tl)
                w = [w[i] + lack[i] * k for i in range(ncols)]
            extra = TEXT_W - sum(w)
            if extra > 0:
                w = [w[i] + extra * wt[i] / sum(wt) for i in range(ncols)]
        else:
            w = [x * TEXT_W / sum(w) for x in w]
        return w

    def add_table(node):
        capn = node.find("caption")
        if capn is not None:
            p = doc.add_paragraph(style="Table Caption")
            lab = p.add_run((capn.get("data-label") or "") + ". ")
            lab.bold = True
            for c in capn.children:
                add_inline(p, c)
            tidy(p)
        rows = node.find_all("tr")
        ncols = max(len(r.find_all(["th", "td"])) for r in rows)
        t = doc.add_table(rows=len(rows), cols=ncols)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_borders(t)
        tm = cfg["table"]
        cell_margins(t, tm["cell_margin_top"], tm["cell_margin_bottom"],
                     tm["cell_margin_left"], tm["cell_margin_right"])
        body_i = 0
        for ri, r in enumerate(rows):
            cells = r.find_all(["th", "td"])
            is_head = all(c.name == "th" for c in cells)
            row_flags(t.rows[ri], header=is_head)
            if not is_head:
                body_i += 1
            for ci, c in enumerate(cells):
                cell = t.cell(ri, ci)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p = cell.paragraphs[0]
                p.style = tcell
                fmt = ({"bold": True, "color": "FFFFFF", "table": True} if is_head
                       else {"table": True})
                for ch in c.children:
                    add_inline(p, ch, fmt)
                tidy(p)
                cls = c.get("class") or []
                if "r" in cls:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif "c" in cls:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                if is_head:
                    cell_fill(cell, INDIGO)
                elif body_i % 2 == 0:
                    cell_fill(cell, ALT)
        fixed_widths(t, col_widths(node, ncols))
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        sp.paragraph_format.line_spacing = 0.8
        return t

    # ---------------------------------------------------------------- blocks
    def add_callout(node, kind):
        border, fill = ((INDIGO, "EEF2FA") if kind == "note" else ("C98A12", "FFF7E6"))
        for pn in node.find_all("p"):
            p = para_from(doc, pn)
            ppr = p._p.get_or_add_pPr()
            pborder(ppr, "left", 24, border, 10)
            pborder(ppr, "top", 4, fill, 6)
            pborder(ppr, "bottom", 4, fill, 6)
            pborder(ppr, "right", 4, fill, 8)
            shade(ppr, fill)
            p.paragraph_format.left_indent = Cm(0.4)
            p.paragraph_format.right_indent = Cm(0.2)
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(10)
            p.paragraph_format.keep_together = True

    def add_kpis(node):
        kpis = node.find_all("div", class_="kpi")
        t = doc.add_table(rows=1, cols=len(kpis))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(t)
        cell_margins(t, 90, 90, 80, 80)
        row_flags(t.rows[0])
        for i, k in enumerate(kpis):
            cell = t.cell(0, i)
            cell_fill(cell, "EEF2FA")
            b = el("w:tcBorders")
            b.append(el("w:top", val="single", sz=24, space=0, color=LIME))
            b.append(el("w:left", val="single", sz=18, space=0, color="FFFFFF"))
            b.append(el("w:right", val="single", sz=18, space=0, color="FFFFFF"))
            cell._tc.get_or_add_tcPr().append(b)
            p = cell.paragraphs[0]
            p.style = tcell
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(k.find("b").get_text().strip())
            r.bold = True
            r.font.size = Pt(22)
            r.font.color.rgb = rgb(INDIGO)
            p2 = cell.add_paragraph(style=tcell)
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for c in k.find("span").children:
                add_inline(p2, c, {"color": SLATE, "size": 8.5})
            tidy(p2)
        fixed_widths(t, [TEXT_W / len(kpis)] * len(kpis))
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(2)

    FIG = [0]

    def img_width_cm(img, src):
        m = re.search(r"width:\s*([\d.]+)\s*cm", img.get("style") or "")
        if m:
            return float(m.group(1))
        if src in cfg["figure_widths"]:
            return float(cfg["figure_widths"][src])
        return TEXT_W

    def picture_para(container, src, width_cm):
        p = container.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        path = src if os.path.isabs(src) else os.path.join(base, src)
        if not os.path.exists(path):
            die("image not found: " + path)
        w, h = Image.open(path).size
        p.add_run().add_picture(path, width=Cm(width_cm), height=Cm(width_cm * h / w))
        FIG[0] += 1
        return p

    def caption_para(container, fc):
        p = container.add_paragraph(style="Caption")
        p.add_run((fc.get("data-label") or "") + ". ")
        for c in fc.children:
            add_inline(p, c)
        tidy(p)
        return p

    def add_diagram(node):
        img = node.find("img")
        picture_para(doc, img["src"], img_width_cm(img, img["src"]))
        fc = node.find("figcaption")
        if fc is not None:
            caption_para(doc, fc)

    def add_screen(node):
        """Screenshot on the left, prose column on the right, inside a borderless table."""
        SW = float(cfg["screen_width_cm"])
        t = doc.add_table(rows=1, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(t)
        cell_margins(t, 0, 0, 60, 60)
        row_flags(t.rows[0])
        left, right = t.cell(0, 0), t.cell(0, 1)
        fig = node.find("figure")
        lp = left.paragraphs[0]
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.paragraph_format.space_before = Pt(4)
        lp.paragraph_format.space_after = Pt(0)
        lp.paragraph_format.keep_with_next = True
        lp.paragraph_format.line_spacing = 1.0
        src = fig.find("img")["src"]
        path = src if os.path.isabs(src) else os.path.join(base, src)
        if not os.path.exists(path):
            die("image not found: " + path)
        w, h = Image.open(path).size
        lp.add_run().add_picture(path, width=Cm(SW), height=Cm(SW * h / w))
        FIG[0] += 1
        fc = fig.find("figcaption")
        if fc is not None:
            caption_para(left, fc)
        right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        desc = node.find("div", class_="desc")
        first = True
        for c in (desc.children if desc is not None else []):
            if not isinstance(c, Tag):
                continue
            cls = c.get("class") or []
            if c.name == "div" and "tagline" in cls:
                p = right.paragraphs[0] if first else right.add_paragraph()
                p.style = tag_st
                for ch in c.children:
                    add_inline(p, ch)
                tidy(p)
                p.paragraph_format.space_before = Pt(6)
            elif c.name == "h3":
                p = right.paragraphs[0] if first else right.add_paragraph()
                p.style = st["Heading 3"]
                for ch in c.children:
                    add_inline(p, ch)
                tidy(p)
                p.paragraph_format.space_before = Pt(2)
            elif c.name == "p":
                p = para_from(right, c)
                p.paragraph_format.space_after = Pt(5)
            elif c.name in ("ul", "ol"):
                add_list(right, c)
            first = False
        fixed_widths(t, [SW + 0.6, TEXT_W - SW - 0.6])
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(6)

    def add_pre(node):
        txt = node.get_text().rstrip("\n").strip("\n")
        p = doc.add_paragraph(style="Code Block")
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            r = p.add_run(line)
            if i < len(lines) - 1:
                r.add_break()

    def field_run(p, kind, instr=None):
        r = p.add_run()
        if instr is None:
            r._r.append(el("w:fldChar", fldCharType=kind))
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            r._r.append(it)

    # ---------------------------------------------------------------- cover
    cover = body.find("section", class_="cover")
    if cover is not None:
        meta = cover.find("div", class_="meta")
        meta_items, note = {}, ""
        cur = None
        if meta is not None:
            for c in meta.children:
                if isinstance(c, Tag) and c.name == "b":
                    cur = c.get_text().strip().rstrip(":")
                    meta_items[cur] = ""
                elif isinstance(c, NavigableString) and WS.sub(" ", str(c)).strip():
                    if cur:
                        meta_items[cur] += WS.sub(" ", str(c)).strip()
                        cur = None
                    else:
                        note = WS.sub(" ", str(c)).strip()

        cv = cfg["cover"]
        band = doc.add_table(rows=1, cols=1)
        band.alignment = WD_TABLE_ALIGNMENT.CENTER
        no_borders(band)
        cell_margins(band, 300, 300, 480, 480)
        row = band.rows[0]
        row.height = Cm(cv["band_height_cm"])
        row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
        row_flags(row)
        bc = band.cell(0, 0)
        cell_fill(bc, NAVY)
        bc.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
        brand = cover.find("div", class_="brand")
        if brand is not None:
            p = bc.paragraphs[0]
            r = p.add_run(WS.sub(" ", brand.get_text()).strip())
            r.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = rgb(LIME)
            r.font.all_caps = True
            p.paragraph_format.space_after = Pt(200)
        h1 = cover.find("h1")
        if h1 is not None:
            p = bc.add_paragraph()
            r = p.add_run(h1.get_text().strip())
            r.bold = True
            r.font.size = Pt(cv["title_pt"])
            r.font.color.rgb = rgb("FFFFFF")
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.0
            pborder(p._p.get_or_add_pPr(), "bottom", 36, LIME, 10)
        sub = cover.find("div", class_="subtitle")
        if sub is not None:
            p = bc.add_paragraph()
            r = p.add_run(WS.sub(" ", sub.get_text()).strip())
            r.font.size = Pt(16)
            r.font.color.rgb = rgb("D6E6F2")
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15

        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(18)

        def meta_line(label, value, size, after):
            p = doc.add_paragraph()
            r = p.add_run(label + ": ")
            r.bold = True
            r.font.color.rgb = rgb(INDIGO)
            r.font.size = Pt(size)
            r = p.add_run(value)
            r.font.size = Pt(size)
            p.paragraph_format.space_after = Pt(after)
            p.paragraph_format.left_indent = Cm(0.3)

        groups = cv["meta_groups"] or [list(meta_items)]
        sizes = cv["meta_sizes"] or [11] * len(groups)
        placed = set()
        for gi, keys in enumerate(groups):
            for k in keys:
                if k in meta_items:
                    meta_line(k, meta_items[k], sizes[min(gi, len(sizes) - 1)], 6 if gi == 0 else 4)
                    placed.add(k)
            if gi == 0 and len(groups) > 1:
                sp = doc.add_paragraph()
                sp.paragraph_format.space_after = Pt(4)
        for k, v in meta_items.items():
            if k not in placed:
                meta_line(k, v, 11, 4)
        if note:
            p = doc.add_paragraph()
            r = p.add_run(note)
            r.italic = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = rgb(SLATE)
            pborder(p._p.get_or_add_pPr(), "top", 6, GRID, 8)
            p.paragraph_format.space_before = Pt(80)
            p.paragraph_format.left_indent = Cm(0.3)
            p.paragraph_format.right_indent = Cm(0.3)

    # ---------------------------------------------------------------- TOC
    chapters = body.find_all("section", class_=["chapter", "chapter-flow"])
    entries = []
    for secn in chapters:
        for h in secn.find_all(["h1", "h2"], recursive=False):
            lvl = 1 if h.name == "h1" else 2
            if lvl == 2 and cfg["toc"]["depth"] == "1":
                continue
            num = h.find("span", class_="num")
            n = num.get_text().strip() if num else ""
            txt = WS.sub(" ", h.get_text()).strip()
            if n and txt.startswith(n):  # the <span class="num"> is part of get_text()
                txt = txt[len(n):].strip()
            entries.append((lvl, (n + " " + txt) if n else txt))

    toc_page = body.find("div", class_="toc-page")
    if toc_page is not None:
        h2 = toc_page.find(["h2", "h1"])
        p = doc.add_paragraph((h2.get_text().strip() if h2 else "Contents"), style="TOC Title")
        p.paragraph_format.page_break_before = True
        # Field with a static result region: renders correctly everywhere, and Word
        # can still refresh it with F9. scripts/fill_toc.py rewrites the page numbers.
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        field_run(p, "begin")
        field_run(p, "x", ' TOC \\o "%s" \\h \\u ' % cfg["toc"]["depth"])
        field_run(p, "separate")
        for lvl, txt in entries:
            e = doc.add_paragraph(style="TOC %d" % lvl)
            e.add_run(txt)
            e.add_run("\t")
            e.add_run("1")
        last = doc.add_paragraph()
        last.paragraph_format.space_after = Pt(0)
        field_run(last, "end")

    # ---------------------------------------------------------------- body
    ignore = set(cfg["ignore_classes"])

    def handle(container, c):
        cls = c.get("class") or []
        if c.name == "h1":
            num = c.find("span", class_="num")
            n = num.get_text().strip() if num else ""
            if num:
                num.extract()
            p = container.add_paragraph(style="Heading 1")
            p.add_run((n + " " if n else ""))
            for ch in c.children:
                add_inline(p, ch)
            tidy(p)
        elif c.name in ("h2", "h3"):
            p = container.add_paragraph(style="Heading %s" % c.name[1])
            for ch in c.children:
                add_inline(p, ch)
            tidy(p)
        elif c.name == "p":
            para_from(container, c)
        elif c.name in ("ul", "ol"):
            add_list(container, c)
        elif c.name == "table":
            add_table(c)
        elif c.name == "pre":
            add_pre(c)
        elif c.name == "figure":
            add_diagram(c)
        elif c.name == "div" and "screen" in cls:
            add_screen(c)
        elif c.name == "div" and "kpis" in cls:
            add_kpis(c)
        elif c.name == "div" and ("note" in cls or "warn" in cls):
            add_callout(c, "note" if "note" in cls else "warn")
        elif ignore & set(cls):
            return
        else:
            die("unhandled element <%s class=%r> — add a handler or list the class in "
                "ignore_classes" % (c.name, cls))

    for secn in chapters:
        for c in secn.children:
            if isinstance(c, Tag):
                handle(doc, c)

    # ---------------------------------------------------------------- header/footer
    sec.different_first_page_header_footer = True
    if cfg["header_label"]:
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = hp.add_run(cfg["header_label"])
        r.font.size = Pt(8.5)
        r.font.color.rgb = rgb(SLATE)
        pborder(hp._p.get_or_add_pPr(), "bottom", 4, GRID, 4)
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field_run(fp, "begin")
    field_run(fp, "x", " PAGE ")
    field_run(fp, "separate")
    fp.add_run("1")
    field_run(fp, "end")
    for r in fp.runs:
        r.font.size = Pt(9)
        r.font.color.rgb = rgb(SLATE)

    cp = doc.core_properties
    cp.title = cfg["title"] or (cover.find("h1").get_text().strip() if cover is not None else "")
    cp.language = cfg["language"]
    normal.element.get_or_add_rPr().append(el("w:lang", val=cfg["language"]))

    # ---------------------------------------------------------------- schema order
    # Word rejects out-of-order property children; python-docx appends blindly.
    ORDER = {
        "pPr": ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
                "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
                "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
                "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing",
                "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection",
                "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
                "sectPr", "pPrChange"],
        "rPr": ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
                "dstrike", "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid",
                "vanish", "webHidden", "color", "spacing", "w", "kern", "position", "sz",
                "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
                "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"],
        "tblPr": ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
                  "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
                  "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
                  "tblDescription"],
        "pBdr": ["top", "left", "bottom", "right", "between", "bar"],
        "tcBorders": ["top", "start", "left", "bottom", "end", "right", "insideH", "insideV",
                      "tl2br", "tr2bl"],
        "tcPr": ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
                 "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"],
    }

    def normalise(root):
        for tag, seq in ORDER.items():
            idx = {qn("w:" + n): i for i, n in enumerate(seq)}
            for pr in root.iter(qn("w:" + tag)):
                kids = list(pr)
                srt = sorted(kids, key=lambda k: idx.get(k.tag, 999))
                if srt != kids:
                    for k in kids:
                        pr.remove(k)
                    for k in srt:
                        pr.append(k)

    normalise(doc.element)
    normalise(doc.styles.element)
    for hf in (sec.header, sec.footer, sec.first_page_header, sec.first_page_footer):
        normalise(hf._element)

    for z in doc.settings.element.findall(qn("w:zoom")):
        z.set(qn("w:percent"), "100")

    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    doc.save(out)
    print("saved %s | figures %d | tables %d | toc entries %d"
          % (out, FIG[0], len(body.find_all("table")), len(entries)))


if __name__ == "__main__":
    main()
````

---

## `scripts/fill_toc.py`

````python
#!/usr/bin/env python3
"""Fill the page numbers of a static TOC result region by measuring the rendered PDF.

The builder emits the TOC as a real Word field whose *result* is a list of
`TOC 1` / `TOC 2` paragraphs ending in a tab and a placeholder number. Word shows
that result immediately (no "update field" prompt) and can still refresh it with F9.
This script renders the .docx to PDF, finds the page where each heading actually
lands, and rewrites the placeholder numbers.

Usage:
    python3 fill_toc.py report.docx [--pdf existing.pdf] [--keep-pdf out.pdf]

Requires: libreoffice (soffice), pymupdf, python-docx.
"""
import os
import re
import subprocess
import sys
import tempfile

import pymupdf
from docx import Document
from docx.oxml.ns import qn

WS = re.compile(r"\s+")


def norm(s):
    return WS.sub(" ", s.replace("\u00ad", "")).strip().lower()


def to_pdf(docx_path, workdir):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", workdir, docx_path],
                   check=True, capture_output=True, timeout=600)
    pdf = os.path.join(workdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit("fill_toc.py: LibreOffice produced no PDF")
    return pdf


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fill_toc.py report.docx [--pdf file.pdf] [--keep-pdf out.pdf]")
    docx_path = os.path.abspath(sys.argv[1])
    keep = sys.argv[sys.argv.index("--keep-pdf") + 1] if "--keep-pdf" in sys.argv else None

    doc = Document(docx_path)
    entries = [p for p in doc.paragraphs if p.style.name in ("TOC 1", "TOC 2")]
    if not entries:
        sys.exit("fill_toc.py: no TOC 1 / TOC 2 paragraphs found — nothing to fill")
    title = next((p.text.strip() for p in doc.paragraphs if p.style.name == "TOC Title"), "")

    if "--pdf" in sys.argv:
        pdf = sys.argv[sys.argv.index("--pdf") + 1]
        tmp = None
    else:
        tmp = tempfile.mkdtemp(prefix="filltoc_")
        pdf = to_pdf(docx_path, tmp)
    if keep:
        subprocess.run(["cp", pdf, keep], check=True)

    pages = [norm(pg.get_text()) for pg in pymupdf.open(pdf)]
    # The TOC pages are the ones carrying dot leaders; skip them (and the cover) so a
    # heading is never "found" inside the index itself.
    dot_pages = [i for i, t in enumerate(pages[:12]) if re.search(r"\.{20,}", t)]
    start = max(dot_pages) + 1 if dot_pages else 0
    if not dot_pages and title:
        hits = [i for i, t in enumerate(pages) if norm(title) in t]
        if hits:
            start = hits[0] + 1

    filled, missing = 0, []
    for e in entries:
        label = norm(e.text.split("\t")[0])  # drop the tab + placeholder page number
        key = label[:45]
        found = None
        for i in range(start, len(pages)):
            if key and key in pages[i]:
                found = i
                break
        if found is None:
            missing.append(e.text[:60])
            continue
        start = found
        runs = e.runs
        if not runs:
            continue
        runs[-1].text = str(found + 1)
        filled += 1

    doc.save(docx_path)
    print("fill_toc.py: %d/%d entries numbered, %d pages" % (filled, len(entries), len(pages)))
    if missing:
        print("  not located (kept placeholder): " + " | ".join(missing[:8]))
    if tmp and not keep:
        subprocess.run(["rm", "-rf", tmp])


if __name__ == "__main__":
    main()
````

---

## `scripts/verify_docx.py`

````python
#!/usr/bin/env python3
"""Verify a built .docx against its config: structure, geometry, and no silent loss.

Checks that catch the failures that actually happen in this pipeline:
  * an image dropped, reordered, or stretched (aspect ratio / width)
  * a table wider than the text column, or a cell whose longest word cannot fit
  * a row that splits across pages, or a header row that does not repeat
  * a missing cover line, TOC field, header/footer, or code block
  * markdown leftovers and unescaped entities leaking into the text

Usage:
    python3 verify_docx.py report.docx config.json

Exit code 0 = all checks passed, 1 = at least one failed.
"""
import hashlib
import os
import re
import subprocess
import sys

from docx import Document
from docx.oxml.ns import qn
from PIL import Image, ImageFont

WS = re.compile(r"\s+")
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATE = "/opt/computersetup/abacusai_computer/tools/docx_editing_tools/validate.py"

res = []


def chk(name, ok, info=""):
    res.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (("  " + str(info)) if info else ""))


def font_pair():
    for d in (os.path.join(SKILL, "assets", "fonts"), os.path.expanduser("~/.fonts")):
        reg, bold = os.path.join(d, "Carlito-Regular.ttf"), os.path.join(d, "Carlito-Bold.ttf")
        if os.path.exists(reg) and os.path.exists(bold):
            return (ImageFont.truetype(reg, 90), ImageFont.truetype(bold, 90))
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: verify_docx.py report.docx [config.json]")
    out = os.path.abspath(sys.argv[1])
    cfg = {}
    if len(sys.argv) > 2:
        import json
        cfg = json.load(open(sys.argv[2], encoding="utf-8"))
        cfg["_dir"] = os.path.dirname(os.path.abspath(sys.argv[2]))
    base = cfg.get("base_dir") or cfg.get("_dir", os.path.dirname(out))
    if not os.path.isabs(base):
        base = os.path.join(cfg.get("_dir", os.path.dirname(out)), base)
    exp = cfg.get("expect", {})
    text_w = cfg.get("page", {}).get("width_cm", 21.0) - 2 * cfg.get("page", {}).get("margin_cm", 2.2)

    chk("zip magic", open(out, "rb").read(4) == b"PK\x03\x04")
    d = Document(out)
    chk("reopen with python-docx", True)
    body = d.element.body

    # ---- cover -------------------------------------------------------------
    cover_txt = []
    for el in body.iterchildren():
        if el.tag == qn("w:p"):
            sty = el.find(".//" + qn("w:pStyle"))
            if sty is not None and sty.get(qn("w:val")) in ("TOCTitle", "TOC Title"):
                break
        cover_txt.append("".join(t.text or "" for t in el.iter(qn("w:t"))))
    cover = "\n".join(cover_txt)
    for s in exp.get("cover_strings", []):
        chk("cover: " + s[:48], s in cover)
    first_tbl = body.find(qn("w:tbl"))
    if first_tbl is not None:
        chk("cover band is a filled table", "w:fill=" in first_tbl.xml)

    # ---- images ------------------------------------------------------------
    expected = exp.get("images")
    blips = body.findall(".//" + qn("a:blip"))
    rels = d.part.rels
    order = []
    for b in blips:
        blob = rels[b.get(qn("r:embed"))].target_part.blob
        order.append(hashlib.sha1(blob).hexdigest())
    if expected:
        src = {}
        for e in expected:
            p = e if os.path.isabs(e) else os.path.join(base, e)
            src[hashlib.sha1(open(p, "rb").read()).hexdigest()] = os.path.basename(e)
        names = [src.get(h, "?") for h in order]
        chk("%d embedded images" % len(expected), len(blips) == len(expected), len(blips))
        chk("image order matches the HTML", names == [os.path.basename(e) for e in expected], names)
    else:
        chk("images embedded", len(blips) > 0, len(blips))

    # aspect ratio + width, matched back to source files by hash
    bad = []
    if expected:
        for ext, h in zip(body.findall(".//" + qn("wp:extent")), order):
            nm = src.get(h)
            if not nm:
                continue
            p = os.path.join(base, "assets", nm)
            if not os.path.exists(p):
                p = next((os.path.join(base, e) for e in expected
                          if os.path.basename(e) == nm), None)
            if not p or not os.path.exists(p):
                continue
            w, hh = Image.open(p).size
            cx, cy = int(ext.get("cx")), int(ext.get("cy"))
            if abs(cx / cy - w / hh) > 0.01:
                bad.append(nm + " aspect")
            if cx / 360000 > text_w + 0.05:
                bad.append(nm + " too wide")
        chk("image aspect ratio and width", not bad, bad)

    caps = [p.text for p in d.paragraphs if p.style.name == "Caption"]
    caps += [p.text for t in d.tables for c in t._cells for p in c.paragraphs
             if p.style.name == "Caption"]
    nfig = len(set(c for c in caps if c.strip()))
    if exp.get("figures"):
        chk("%d figure captions" % exp["figures"], nfig == exp["figures"], nfig)
    else:
        chk("figure captions present", nfig > 0, nfig)

    # ---- tables ------------------------------------------------------------
    data = [t for t in body.iter(qn("w:tbl")) if t.find(".//" + qn("w:tblHeader")) is not None]
    if exp.get("data_tables"):
        chk("%d data tables with repeating header" % exp["data_tables"],
            len(data) == exp["data_tables"], len(data))
    else:
        chk("data tables with repeating header", len(data) > 0, len(data))
    all_rows = [tr for t in body.iter(qn("w:tbl")) for tr in t.findall(qn("w:tr"))]
    chk("every row cantSplit", all(tr.find(".//" + qn("w:cantSplit")) is not None
                                   for tr in all_rows))
    wide = []
    for t in body.iter(qn("w:tbl")):
        g = t.find(qn("w:tblGrid"))
        if g is None:
            continue
        w = sum(int(x.get(qn("w:w"))) for x in g.findall(qn("w:gridCol"))) / 1440 * 2.54
        if w > text_w + 0.05:
            wide.append(round(w, 2))
    chk("no table wider than the text column", not wide, wide)

    fp = font_pair()
    if fp:
        fR, fB = fp

        def wcm(text, bold, mono, pt):
            if mono:
                return len(text) * 0.55 * pt / 72 * 2.54
            return (fB if bold else fR).getlength(text) / 90 * pt / 72 * 2.54

        over = []
        for ti, t in enumerate(data):
            g = t.find(qn("w:tblGrid"))
            if g is None:
                continue
            grid = [int(x.get(qn("w:w"))) / 1440 * 2.54 for x in g.findall(qn("w:gridCol"))]
            for tr in t.findall(qn("w:tr")):
                for ci, tc in enumerate(tr.findall(qn("w:tc"))):
                    if ci >= len(grid):
                        continue
                    avail = grid[ci] - 2 * 100 / 1440 * 2.54
                    for r in tc.iter(qn("w:r")):
                        txt = "".join(x.text or "" for x in r.findall(qn("w:t")))
                        rs = r.find(".//" + qn("w:rStyle"))
                        mono = rs is not None and "Code" in rs.get(qn("w:val"))
                        bold = (r.find(".//" + qn("w:b")) is not None
                                or tr.find(".//" + qn("w:tblHeader")) is not None)
                        for tok in txt.split():
                            ww = wcm(tok, bold, mono, 8 if mono else 9)
                            if ww > avail:
                                over.append((ti + 1, tok, round(ww, 2), round(avail, 2)))
        chk("no unbreakable token overflows its cell", not over, over[:10])
    else:
        print("SKIP token-width check (Carlito not found — install it or bundle assets/fonts)")

    # ---- headings, TOC, text ----------------------------------------------
    h1 = [p.text for p in d.paragraphs if p.style.name == "Heading 1"]
    if exp.get("h1"):
        chk("%d Heading 1 chapters" % exp["h1"], len(h1) == exp["h1"], len(h1))
    else:
        chk("Heading 1 chapters present", len(h1) > 0, len(h1))
    if exp.get("h2"):
        n2 = sum(p.style.name == "Heading 2" for p in d.paragraphs)
        chk("%d Heading 2 sections" % exp["h2"], n2 == exp["h2"], n2)
    xml = body.xml
    chk("TOC field present", 'TOC \\o' in xml)
    toc_entries = [p for p in d.paragraphs if p.style.name in ("TOC 1", "TOC 2")]
    chk("TOC entries rendered as static text", len(toc_entries) > 0, len(toc_entries))
    if toc_entries:
        numbered = [p for p in toc_entries if p.runs and p.runs[-1].text.strip().isdigit()]
        chk("TOC page numbers filled", len(numbered) == len(toc_entries),
            "%d/%d" % (len(numbered), len(toc_entries)))
    chk("no &#x entities in text", not any("&#x" in p.text for p in d.paragraphs))
    chk("no markdown leftovers", not any(re.search(r"\*\*|^#+ ", p.text) for p in d.paragraphs))
    if exp.get("code_blocks"):
        n = sum(p.style.name == "Code Block" for p in d.paragraphs)
        chk("%d code blocks" % exp["code_blocks"], n == exp["code_blocks"], n)

    s = d.sections[0]
    chk("distinct first-page header/footer",
        s.different_first_page_header_footer and not s.first_page_header.paragraphs[0].text.strip())
    chk("running header + PAGE footer",
        bool(s.header.paragraphs[0].text.strip()) and "PAGE" in s.footer._element.xml)

    if os.path.exists(VALIDATE):
        v = subprocess.run([sys.executable, VALIDATE, out], capture_output=True, text=True)
        txt = v.stdout + v.stderr
        ok = "All validations PASSED" in txt and not re.search(r"new error\(s\)", txt)
        detail = [ln.strip() for ln in txt.splitlines()
                  if "error" in ln.lower() and "new error" not in ln.lower()][:2]
        chk("OOXML schema validation", ok, detail or txt.strip().splitlines()[-1:])
    else:
        print("SKIP schema validation (validate.py not installed)")

    print("ALL PASS" if all(res) else "SOME FAIL (%d/%d)" % (sum(res), len(res)))
    sys.exit(0 if all(res) else 1)


if __name__ == "__main__":
    main()
````

---

## `scripts/check_layout.py`

````python
#!/usr/bin/env python3
"""Render a .docx to PDF and report layout problems that only show up on the page.

Catches: near-empty pages (an orphaned bullet or a stray caption pushed a page),
text or images running past the margins, images clipped by the page edge, and the
overall page count. Run it after every build; a page with fewer than --min-lines
lines of text is almost always a spacing bug, not a design choice.

Usage:
    python3 check_layout.py report.docx [--min-lines 8] [--keep-pdf out.pdf] [--margin-cm 2.2]
"""
import os
import subprocess
import sys
import tempfile

import pymupdf

PT_CM = 72 / 2.54


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: check_layout.py report.docx [--min-lines 8] [--keep-pdf out.pdf]")
    docx_path = os.path.abspath(sys.argv[1])
    min_lines = int(sys.argv[sys.argv.index("--min-lines") + 1]) if "--min-lines" in sys.argv else 8
    keep = sys.argv[sys.argv.index("--keep-pdf") + 1] if "--keep-pdf" in sys.argv else None
    margin = float(sys.argv[sys.argv.index("--margin-cm") + 1]) if "--margin-cm" in sys.argv else 2.2

    tmp = tempfile.mkdtemp(prefix="checklayout_")
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, docx_path],
                   check=True, capture_output=True, timeout=900)
    pdf = os.path.join(tmp, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit("check_layout.py: LibreOffice produced no PDF")
    if keep:
        subprocess.run(["cp", pdf, keep], check=True)

    doc = pymupdf.open(pdf)
    sparse, overflow, clipped = [], [], []
    print("pages: %d" % doc.page_count)
    for i, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        lines = [ln for blk in page.get_text("blocks") for ln in blk[4].splitlines() if ln.strip()]
        imgs = page.get_image_info()  # images actually drawn on this page
        if len(lines) < min_lines and not imgs:
            sparse.append((i, len(lines)))
        for blk in page.get_text("blocks"):
            if blk[2] > W - margin * PT_CM + 6:
                overflow.append((i, round(blk[2] / PT_CM, 2)))
                break
        for info in page.get_image_info():
            x0, y0, x1, y1 = info["bbox"]
            if y1 > H - 4 or x1 > W - 4 or x0 < 4:
                clipped.append((i, [round(v / PT_CM, 2) for v in info["bbox"]]))
        print("  p%-3d lines %-3d images %d" % (i, len(lines), len(imgs)))

    print()
    if sparse:
        print("SPARSE PAGES (fewer than %d text lines): %s" % (min_lines, sparse))
    if overflow:
        print("TEXT PAST THE RIGHT MARGIN: %s" % overflow[:10])
    if clipped:
        print("IMAGE TOUCHING/OVERFLOWING THE PAGE EDGE: %s" % clipped[:10])
    if not (sparse or overflow or clipped):
        print("LAYOUT OK")
    if not keep:
        subprocess.run(["rm", "-rf", tmp])


if __name__ == "__main__":
    main()
````

---

## `scripts/render_mermaid.js`

````javascript
#!/usr/bin/env node
/**
 * Render Mermaid diagram sources to high-DPI PNGs for embedding in a .docx.
 *
 * Word cannot render Mermaid, so every diagram becomes a raster image at 3x scale
 * (≈288 dpi) — sharp in print, and small enough that the .docx stays a few MB.
 *
 * Usage:
 *   node render_mermaid.js diagrams/arch.mmd diagrams/er.mmd --out assets --scale 3
 *   node render_mermaid.js diagram.html --out assets            # pre-built HTML page
 *
 * A .mmd file may carry its own `%%{init: {...}}%%` theme directive; otherwise the
 * default theme below (navy/indigo, matching the report palette) is injected.
 * Output: <out>/<basename>.png, tightly cropped to the SVG.
 */
const path = require('path');
const fs = require('fs');
const os = require('os');

const PW = '/opt/computersetup/abacusai_computer/tools/html2pdf/node_modules/playwright';
const { chromium } = require(fs.existsSync(PW) ? PW : 'playwright');

const args = process.argv.slice(2);
const inputs = args.filter((a) => !a.startsWith('--') && !isValue(a));
function isValue(a) {
  const flags = ['--out', '--scale', '--width', '--height', '--theme'];
  const i = args.indexOf(a);
  return i > 0 && flags.includes(args[i - 1]);
}
const opt = (name, dflt) => (args.includes(name) ? args[args.indexOf(name) + 1] : dflt);

const OUT = opt('--out', 'assets');
const SCALE = parseFloat(opt('--scale', '3'));
const WIDTH = parseInt(opt('--width', '1100'), 10);
const HEIGHT = parseInt(opt('--height', '900'), 10);
const THEME = opt('--theme', 'base');

const THEME_VARS = {
  base: {
    primaryColor: '#E7EEFB', primaryBorderColor: '#36519E', primaryTextColor: '#122641',
    lineColor: '#36519E', fontSize: '15px', clusterBkg: '#F5F7FB', clusterBorder: '#A6B6CC',
  },
  default: {}, dark: {}, forest: {}, neutral: {},
};

if (!inputs.length) {
  console.error('usage: node render_mermaid.js <file.mmd|file.html> [...] --out assets --scale 3');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

function pageFor(file) {
  const src = fs.readFileSync(file, 'utf8');
  if (file.endsWith('.html')) return { url: 'file://' + path.resolve(file), tmp: null };
  const init = src.includes('%%{init') ? '' :
    `%%{init: ${JSON.stringify({ theme: THEME, themeVariables: THEME_VARS[THEME] || {} })}}%%\n`;
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<style>body{margin:0;padding:16px;background:#fff;font-family:Arial,Helvetica,sans-serif}</style>
</head><body><pre class="mermaid">${init}${src}</pre>
<script>mermaid.initialize({startOnLoad:true});</script></body></html>`;
  const tmp = path.join(os.tmpdir(), 'mmd_' + path.basename(file) + '.html');
  fs.writeFileSync(tmp, html);
  return { url: 'file://' + tmp, tmp };
}

(async () => {
  const browser = await chromium.launch();
  for (const file of inputs) {
    const { url, tmp } = pageFor(file);
    const page = await browser.newPage({ deviceScaleFactor: SCALE, viewport: { width: WIDTH, height: HEIGHT } });
    await page.goto(url);
    await page.waitForSelector('.mermaid svg', { timeout: 30000 });
    await page.waitForTimeout(800); // let fonts settle before the screenshot
    const el = await page.$('.mermaid svg');
    const out = path.join(OUT, path.basename(file).replace(/\.(mmd|html)$/, '') + '.png');
    await el.screenshot({ path: out });
    const box = await el.boundingBox();
    console.log('ok', out, Math.round(box.width * SCALE) + 'x' + Math.round(box.height * SCALE));
    await page.close();
    if (tmp) fs.unlinkSync(tmp);
  }
  await browser.close();
})();
````

---

## `assets/config.example.json`

````json
{
  "html": "source.html",
  "base_dir": ".",
  "out": "report.docx",
  "header_label": "Acme — Documentación técnica",
  "title": "Acme — Documentación Técnica",
  "language": "es-ES",
  "body_pt": 10.5,
  "page": {
    "width_cm": 21.0,
    "height_cm": 29.7,
    "margin_cm": 2.2,
    "top_cm": 2.3,
    "bottom_cm": 2.0
  },
  "palette": {
    "navy": "122440",
    "accent": "36519E",
    "slate": "5B6B82",
    "highlight": "C3DC3A",
    "body": "1F2937",
    "alt": "F2F4F8",
    "grid": "C9D1DE",
    "code_bg": "F3F6FB"
  },
  "fonts": {
    "sans": "Calibri",
    "mono": "Consolas"
  },
  "table": {
    "cell_margin_top": 30,
    "cell_margin_bottom": 30,
    "cell_margin_left": 90,
    "cell_margin_right": 90
  },
  "screen_width_cm": 7.2,
  "figure_widths": {
    "assets/arch.png": 13.0,
    "assets/er.png": 15.0
  },
  "cover": {
    "band_height_cm": 14.5,
    "title_pt": 66,
    "meta_groups": [
      [
        "Frontend",
        "Backend"
      ],
      [
        "Fecha",
        "Repositorios"
      ]
    ],
    "meta_sizes": [
      13,
      11
    ]
  },
  "toc": {
    "depth": "1-2"
  },
  "ignore_classes": [],
  "expect": {
    "images": [
      "example-diagram.png",
      "example-screen.png"
    ],
    "figures": 2,
    "data_tables": 1,
    "h1": 2,
    "h2": 3,
    "code_blocks": 1,
    "cover_strings": [
      "Acme",
      "Frontend: Android · Kotlin + Jetpack Compose (Material 3)",
      "Backend: Rust · Axum 0.8 + SQLx · PostgreSQL"
    ]
  }
}
````

---

## `assets/source.example.html`

````html
<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Ejemplo · Documentación técnica</title></head>
<body>

<section class="cover">
  <div class="brand"><div class="logo"></div>ACME · Platform</div>
  <div class="bar"></div>
  <h1>Acme</h1>
  <div class="subtitle">Documentación técnica de la plataforma: funcionalidades, funcionamiento, pantallas y modelo de datos</div>
  <div class="meta">
    <b>Fecha:</b> 30 de octubre de 2026<br>
    <b>Frontend:</b> Android · Kotlin + Jetpack Compose (Material 3)<br>
    <b>Backend:</b> Rust · Axum 0.8 + SQLx · PostgreSQL<br>
    <b>Repositorios:</b> acme/app (b307723) · acme/server (c47680c)<br><br>
    Este documento de ejemplo muestra cada bloque que el generador sabe maquetar. Sustituye el contenido por el tuyo y conserva las clases.
  </div>
</section>

<div class="toc-page"><h2>Índice</h2></div>

<section class="chapter">
  <h1 id="s1"><span class="num">1.</span>Resumen ejecutivo</h1>
  <p>Un párrafo de cuerpo con <strong>negrita</strong>, <em>cursiva</em>, <code>código en línea</code> y un <span style="color:#36519E">color de acento</span>. El texto se lee del HTML: el generador no contiene prosa.</p>

  <div class="kpis">
    <div class="kpi"><b>21</b><span>endpoints REST<br>(4 públicos · 17 con JWT)</span></div>
    <div class="kpi"><b>5</b><span>tablas en<br>PostgreSQL</span></div>
    <div class="kpi"><b>3</b><span>pantallas +<br>5 diálogos</span></div>
  </div>

  <div class="note"><p><strong>Estado del proyecto.</strong> Primera versión funcional; faltan tests automatizados, CI y refresh tokens.</p></div>

  <h2>1.1 Qué cubre este documento</h2>
  <ol>
    <li>Las funcionalidades, agrupadas por pantalla.</li>
    <li>El modelo de datos y las migraciones.</li>
    <li>Los riesgos técnicos y el trabajo pendiente.</li>
  </ol>

  <figure class="diagram">
    <img alt="Diagrama de componentes" src="example-diagram.png" style="width: 12cm;">
    <figcaption data-label="Figura 1">Diagrama de componentes: app ↔ API REST ↔ PostgreSQL</figcaption>
  </figure>
</section>

<section class="chapter-flow">
  <h1 id="s2"><span class="num">2.</span>Pantallas y modelo de datos</h1>
  <p>Cada pantalla se documenta con su captura a la izquierda y la explicación a la derecha.</p>

  <div class="screen">
    <figure>
      <img alt="Pantalla de acceso" src="example-screen.png">
      <figcaption data-label="Figura 2">Pantalla de acceso (login)</figcaption>
    </figure>
    <div class="desc">
      <div class="tagline">AuthScreen · modo «Acceso»</div>
      <h3>Login</h3>
      <p>Primera pantalla cuando no hay sesión guardada. Sobre el fondo azul marino aparecen el logo y la marca.</p>
      <ul>
        <li><strong>Selector Acceso / Registro</strong> arriba a la derecha.</li>
        <li>Campos Email, Username y Password.</li>
        <li>Botón lima «Entrar», que llama a <code>POST /api/auth/login</code>.</li>
      </ul>
    </div>
  </div>

  <h2>2.1 Tabla de endpoints</h2>
  <table>
    <caption data-label="Tabla 1">Endpoints públicos del backend</caption>
    <thead><tr><th>Método</th><th>Ruta</th><th class="r">Código</th><th>Descripción</th></tr></thead>
    <tbody>
      <tr><td><code>POST</code></td><td><code>/api/auth/login</code></td><td class="r">200</td><td>Devuelve el JWT y el perfil del usuario</td></tr>
      <tr><td><code>POST</code></td><td><code>/api/auth/register</code></td><td class="r">201</td><td>Crea la cuenta y devuelve el token</td></tr>
      <tr><td><code>GET</code></td><td><code>/api/health</code></td><td class="r">200</td><td>Comprueba el pool de conexiones</td></tr>
    </tbody>
  </table>

  <h2>2.2 Petición de ejemplo</h2>
  <pre>POST /api/auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "••••••"}</pre>

  <div class="warn"><p>El token se guarda sin cifrar en <code>SharedPreferences</code>; no hay refresh tokens.</p></div>
</section>

</body>
</html>
````

---

# 3. Binary assets

Two example PNGs and the four Carlito font files are binary and cannot be inlined here. They are
included in the `.zip` bundle at `assets/example-screen.png`, `assets/example-diagram.png` and
`assets/fonts/Carlito-{Regular,Bold,Italic,BoldItalic}.ttf`. Any PNG can stand in for the examples;
for the fonts, either install Carlito system-wide or drop the four TTFs into `assets/fonts/` and
point `font_dir` in `config.json` at that directory.

# 4. End of skill
