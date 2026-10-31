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
