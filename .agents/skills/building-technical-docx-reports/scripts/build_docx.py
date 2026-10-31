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
