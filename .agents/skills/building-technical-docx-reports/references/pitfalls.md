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
