# building-technical-docx-reports — portable skill bundle

A self-contained agent skill for producing designed, print-ready Word technical reports
(dark cover band, shaded tables with repeating headers, screenshot rows, KPI strips, callouts,
code blocks, Mermaid diagrams, a table of contents with real page numbers, running header and
page numbers) from a structured HTML source.

Everything the skill needs is inside `building-technical-docx-reports/`. No external service, no API
key, no account. The one network dependency is optional and confined to diagram rendering:
`render_mermaid.js` loads `mermaid.min.js` from a CDN into a headless Chromium page. If the receiving
machine is offline, vendor `mermaid.min.js` next to the script and point the `<script src>` in
`render_mermaid.js` at that local file — the rest of the pipeline (HTML → DOCX → TOC → checks) is
fully offline.

---

## What is in the bundle

```
building-technical-docx-reports/
├── SKILL.md                     entry point — read this first
├── scripts/
│   ├── build_docx.py            HTML + config  ->  styled .docx  (config-driven, schema-safe)
│   ├── fill_toc.py              renders PDF, measures headings, writes real TOC page numbers
│   ├── verify_docx.py           25 structural/geometry checks on the produced .docx
│   ├── check_layout.py          page count, sparse/orphan pages, content overflow
│   └── render_mermaid.js        Mermaid .mmd -> 3x PNG via Playwright
├── references/
│   ├── html-contract.md         the exact HTML block vocabulary the builder accepts
│   ├── ooxml-recipes.md         the raw OOXML snippets behind each visual element
│   └── pitfalls.md              failure modes already paid for — read before debugging
└── assets/
    ├── config.example.json      every config knob, commented by example
    ├── source.example.html      one instance of every supported block type
    ├── example-screen.png       sample screenshot asset
    ├── example-diagram.png      sample diagram asset
    └── fonts/Carlito-*.ttf      metric-compatible with Calibri; required for correct pagination
```

---

## Install — pick the row that matches your agent

| Agent / runtime | Where to put it | How it gets picked up |
|---|---|---|
| Abacus AI Agent, Claude Code, and any runtime using the `skills/<name>/SKILL.md` convention | `skills/building-technical-docx-reports/` (project-level) or `~/.claude/skills/building-technical-docx-reports/` (user-level) | Auto-discovered from the `name` + `description` frontmatter in `SKILL.md` |
| Agent with a system-prompt / instructions file only (no skill loader) | Paste `PORTABLE.md` into the instructions, or keep it as a file the agent can read | The agent follows it as plain instructions |
| Agent with a file system but no skill loader | Unzip anywhere, then tell it: *"Read `building-technical-docx-reports/SKILL.md` and follow it."* | Explicit instruction |
| One-off chat agent (no file system) | Paste `PORTABLE.md` — it inlines every script and reference | Plain text |

`PORTABLE.md` is the same skill flattened into one file: SKILL.md, all three references and all
five scripts, each in a fenced block. Use it when you cannot hand over a folder.

---

## Runtime requirements

- Python 3.9+ with `python-docx`, `lxml`, `Pillow`
- LibreOffice (`soffice`) on `PATH` — used by `fill_toc.py` and `check_layout.py` to render PDFs
- Node 18+ with `playwright` and a Chromium install — only for `render_mermaid.js`
- The bundled Carlito fonts (metric-compatible with Calibri). Install them or point
  `font_dir` in the config at `assets/fonts/`; without them pagination drifts and the
  TOC page numbers come out wrong.

```bash
pip install python-docx lxml Pillow
npm i -g playwright && npx playwright install chromium   # only if you render diagrams
```

---

## Use

```bash
S=<bundle>/building-technical-docx-reports/scripts
cd /path/to/project

cp <bundle>/building-technical-docx-reports/assets/config.example.json ./config.json   # then edit it
cp <bundle>/building-technical-docx-reports/assets/source.example.html ./source.html   # then replace the content

python3 $S/build_docx.py config.json                       # HTML -> DOCX (config names the html + out)
python3 $S/fill_toc.py report.docx                         # measure pages, write real index numbers
python3 $S/verify_docx.py report.docx config.json          # must print ALL PASS
python3 $S/check_layout.py report.docx --min-lines 8       # page count, sparse pages, overflow
```

Diagrams first, if the document has any:

```bash
node $S/render_mermaid.js diagrams/arch.mmd diagrams/er.mmd --out assets --scale 3
```

The config file is the single source of truth for input and output paths (`html`, `base_dir`, `out`)
plus palette, page geometry, cover band, TOC depth and the `expect` block that `verify_docx.py`
checks against. `--out` overrides the output path on the command line.

**Verified demo.** `assets/source.example.html` + `assets/config.example.json` + the two
`example-*.png` files are a working document containing one instance of every supported block type.
Copied into a scratch directory with `html` pointed at the example, the four commands above produce a
5-page `.docx` that reports `ALL PASS` from `verify_docx.py` — so the bundle is known-good out of the
box, and any failure you hit is in your own source or config, not in the pipeline.

`build_docx.py` aborts on any HTML element it does not handle, so an unsupported block fails loudly
instead of silently disappearing from the document. `verify_docx.py` and `check_layout.py` exit
non-zero on failure — treat a non-zero exit as "not done".

---

## Notes for the receiving agent

- Content lives in HTML, design lives in the builder. Do not hand-edit the `.docx`; edit the HTML
  and rebuild. That keeps the prose diffable and the layout reproducible.
- Never let the builder invent or drop a sentence. If a block type is missing, add it to the
  builder and to `references/html-contract.md` — do not fall back to raw XML patching.
- The TOC is a real Word field with a static result region: it renders immediately everywhere and
  stays refreshable with F9. Page numbers come from `fill_toc.py`, not from guesswork.
- LibreOffice and Microsoft Word paginate slightly differently. Numbers are measured from the
  LibreOffice render; if the document must match Word exactly, re-run `fill_toc.py` against a
  Word-exported PDF.
