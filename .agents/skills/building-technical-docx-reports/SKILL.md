---
name: building-technical-docx-reports
description: Builds a designed, print-ready Word (.docx) technical report from a structured HTML source — cover band, shaded tables with repeating headers, screenshot-plus-prose rows, KPI strips, callouts, code blocks, Mermaid diagrams, a table of contents with real page numbers, running header and page numbers. Use when the deliverable is a long technical document as .docx (app or system documentation, architecture or audit report, technical manual, project dossier) and its visual design matters, or when a .docx must show UI screenshots and diagrams. Not for letters, invoices, forms, or short memos.
---

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
