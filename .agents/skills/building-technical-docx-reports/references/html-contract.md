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
