"""
Professional Report Generator
Builds a structured multi-section report with cover page, TOC placeholder,
styled headings, data tables, and embedded charts.

Usage: python report_generator.py config.json output.docx
Or import: from report_generator import ReportBuilder
"""

import json
import sys
from datetime import datetime
from io import BytesIO
from typing import Any

import requests
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


PRIMARY  = RGBColor(0x1a, 0x36, 0x5d)
ACCENT   = RGBColor(0x2c, 0x5f, 0x8a)
MUTED    = RGBColor(0x64, 0x74, 0x8b)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
HDR_BG   = '1A365D'
STRIPE   = 'F0F4F8'


def _shade(cell, hex_color):
    el = cell._tc.get_or_add_tcPr().makeelement(
        qn('w:shd'), {qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): hex_color})
    cell._tc.get_or_add_tcPr().append(el)


def _remove_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else tbl.makeelement(qn('w:tblPr'), {})
    bdr = tblPr.makeelement(qn('w:tblBorders'), {})
    for name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        bdr.append(bdr.makeelement(qn(f'w:{name}'), {qn('w:val'): 'nil'}))
    tblPr.append(bdr)


class ReportBuilder:
    def __init__(self, scheme='corporate'):
        self.doc = Document()
        self._setup_page()
        self._setup_styles(scheme)

    def _setup_page(self):
        sec = self.doc.sections[0]
        sec.page_width    = Inches(8.5)
        sec.page_height   = Inches(11)
        sec.top_margin    = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin   = Inches(1.0)
        sec.right_margin  = Inches(1.0)

    def _setup_styles(self, scheme):
        schemes = {
            'corporate': dict(h1=RGBColor(0x1a,0x36,0x5d), h2=RGBColor(0x2c,0x5f,0x8a),
                               body='Calibri', heading='Calibri'),
            'modern':    dict(h1=RGBColor(0x0f,0x17,0x2a), h2=RGBColor(0x33,0x41,0x55),
                               body='Arial', heading='Arial'),
            'traditional': dict(h1=RGBColor(0x5c,0x21,0x18), h2=RGBColor(0x78,0x35,0x0f),
                                 body='Georgia', heading='Georgia'),
        }
        s = schemes.get(scheme, schemes['corporate'])

        normal = self.doc.styles['Normal']
        normal.font.name = s['body']
        normal.font.size = Pt(11)
        normal.paragraph_format.space_after = Pt(8)
        normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        normal.paragraph_format.line_spacing = 1.15

        for level, size, before in [(1, 20, 30), (2, 14, 20), (3, 12, 14)]:
            h = self.doc.styles[f'Heading {level}']
            h.font.name = s['heading']
            h.font.size = Pt(size)
            h.font.bold = True
            h.font.color.rgb = s['h1'] if level == 1 else s['h2']
            h.paragraph_format.space_before = Pt(before)
            h.paragraph_format.space_after  = Pt(8)
            h.paragraph_format.keep_with_next = True

        self.doc.styles['Title'].font.name = s['heading']
        self.doc.styles['Title'].font.size = Pt(32)
        self.doc.styles['Title'].font.bold = True
        self.doc.styles['Title'].font.color.rgb = s['h1']

    # ── Cover Page ──────────────────────────────────────────────────────────
    def add_cover_page(self, title, subtitle='', author='', date='',
                       logo_url='', classification=''):
        for _ in range(8):
            self.doc.add_paragraph()

        if logo_url:
            try:
                r = requests.get(logo_url, timeout=8)
                p = self.doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(BytesIO(r.content), width=Inches(1.8))
                self.doc.add_paragraph()
            except Exception:
                pass

        p = self.doc.add_paragraph(title, style='Title')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if subtitle:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(subtitle)
            r.font.size = Pt(16)
            r.font.color.rgb = MUTED

        for _ in range(4):
            self.doc.add_paragraph()

        for line in filter(None, [author, date, classification]):
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line)
            r.font.size = Pt(11)
            r.font.color.rgb = MUTED
            p.paragraph_format.space_after = Pt(2)

        self.doc.add_page_break()

    # ── TOC Placeholder ─────────────────────────────────────────────────────
    def add_toc(self, title='Table of Contents'):
        self.doc.add_heading(title, level=1)
        p = self.doc.add_paragraph()
        run = p.add_run()
        for xml_tag, text in [('begin', ''), ('instrText', ' TOC \\o "1-3" \\h \\z \\u '), ('end', '')]:
            r = p.add_run()
            if xml_tag == 'instrText':
                el = r._r.makeelement(qn('w:instrText'), {})
                el.text = text
                r._r.append(el)
            else:
                el = r._r.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): xml_tag})
                r._r.append(el)
        note = self.doc.add_paragraph()
        note.add_run('[Right-click above and select "Update Field" to populate TOC]')\
            .font.color.rgb = MUTED
        note.runs[0].font.size = Pt(9)
        self.doc.add_page_break()

    # ── Header / Footer ─────────────────────────────────────────────────────
    def set_header_footer(self, left_text='', right_text='', show_page_numbers=True):
        sec = self.doc.sections[0]

        hdr = sec.header
        hdr.is_linked_to_previous = False
        p = hdr.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        t = hdr.add_table(rows=1, cols=2, width=sec.page_width - sec.left_margin - sec.right_margin)
        _remove_borders(t)
        lp = t.rows[0].cells[0].paragraphs[0]
        lp.add_run(left_text).font.color.rgb = MUTED
        rp = t.rows[0].cells[1].paragraphs[0]
        rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rp.add_run(right_text).font.color.rgb = MUTED
        for cell in t.rows[0].cells:
            cell.paragraphs[0].runs[0].font.size = Pt(8)
        # Thin rule under header via border on paragraph
        pPr = p._p.get_or_add_pPr()
        pBdr = pPr.makeelement(qn('w:pBdr'), {})
        bottom = pBdr.makeelement(qn('w:bottom'), {
            qn('w:val'): 'single', qn('w:sz'): '4', qn('w:space'): '1', qn('w:color'): 'D1D5DB'})
        pBdr.append(bottom)
        pPr.append(pBdr)

        if show_page_numbers:
            ftr = sec.footer
            fp = ftr.paragraphs[0]
            fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for fld_type, text in [('begin', None), ('instrText', ' PAGE '), ('end', None)]:
                r = fp.add_run()
                if fld_type == 'instrText':
                    el = r._r.makeelement(qn('w:instrText'), {})
                    el.text = text
                    r._r.append(el)
                    r.font.size = Pt(8)
                    r.font.color.rgb = MUTED
                else:
                    el = r._r.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): fld_type})
                    r._r.append(el)

    # ── Content Sections ────────────────────────────────────────────────────
    def add_heading(self, text, level=1):
        self.doc.add_heading(text, level=level)

    def add_paragraph(self, text, bold=False, italic=False, align='left'):
        p = self.doc.add_paragraph()
        p.alignment = {'left': WD_ALIGN_PARAGRAPH.LEFT,
                       'center': WD_ALIGN_PARAGRAPH.CENTER,
                       'right': WD_ALIGN_PARAGRAPH.RIGHT,
                       'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
        r = p.add_run(text)
        r.bold   = bold
        r.italic = italic
        return p

    def add_bullets(self, items: list[str], numbered=False):
        style = 'List Number' if numbered else 'List Bullet'
        for item in items:
            self.doc.add_paragraph(item, style=style)

    def add_table(self, headers: list[str], rows: list[list[Any]],
                  col_widths: list[float] | None = None):
        tbl = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        tbl.style = 'Table Grid'
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        if col_widths:
            for row in tbl.rows:
                for i, w in enumerate(col_widths):
                    row.cells[i].width = Inches(w)

        # Header
        for i, h in enumerate(headers):
            _shade(tbl.rows[0].cells[i], HDR_BG)
            p = tbl.rows[0].cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            r.bold = True
            r.font.color.rgb = WHITE
            r.font.size = Pt(9)

        # Data
        for ri, row_data in enumerate(rows, 1):
            if ri % 2 == 0:
                for c in tbl.rows[ri].cells:
                    _shade(c, STRIPE)
            for ci, val in enumerate(row_data):
                p = tbl.rows[ri].cells[ci].paragraphs[0]
                p.add_run(str(val)).font.size = Pt(10)

        return tbl

    def add_image(self, path_or_url: str, width_inches=5.5, caption=''):
        if path_or_url.startswith('http'):
            r = requests.get(path_or_url, timeout=10)
            stream = BytesIO(r.content)
            self.doc.add_picture(stream, width=Inches(width_inches))
        else:
            self.doc.add_picture(path_or_url, width=Inches(width_inches))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption:
            cp = self.doc.add_paragraph(caption)
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cp.runs[0].font.size = Pt(9)
            cp.runs[0].font.italic = True
            cp.runs[0].font.color.rgb = MUTED

    def add_page_break(self):
        self.doc.add_page_break()

    def add_callout(self, text: str, style='info'):
        """Highlighted callout box (info, warning, tip)."""
        colors = {'info': 'EFF6FF', 'warning': 'FFFBEB', 'tip': 'F0FDF4'}
        tbl = self.doc.add_table(rows=1, cols=1)
        _shade(tbl.rows[0].cells[0], colors.get(style, 'F3F4F6'))
        p = tbl.rows[0].cells[0].paragraphs[0]
        p.add_run(text).font.size = Pt(10)

    def save(self, path: str):
        order = {
            'pPr': ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl',
                    'numPr', 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens',
                    'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE',
                    'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid', 'spacing',
                    'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
                    'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr',
                    'sectPr', 'pPrChange'],
            'rPr': ['rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike',
                    'dstrike', 'outline', 'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid',
                    'vanish', 'webHidden', 'color', 'spacing', 'w', 'kern', 'position', 'sz',
                    'szCs', 'highlight', 'u', 'effect', 'bdr', 'shd', 'fitText', 'vertAlign',
                    'rtl', 'cs', 'em', 'lang', 'eastAsianLayout', 'specVanish', 'oMath'],
            'tblPr': ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize',
                      'tblStyleColBandSize', 'tblW', 'jc', 'tblCellSpacing', 'tblInd',
                      'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook', 'tblCaption',
                      'tblDescription'],
            'pBdr': ['top', 'left', 'bottom', 'right', 'between', 'bar'],
            'tcBorders': ['top', 'start', 'left', 'bottom', 'end', 'right', 'insideH', 'insideV',
                          'tl2br', 'tr2bl'],
            'tcPr': ['cnfStyle', 'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd',
                     'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark'],
        }
        def _norm(root):
            for tag, seq in order.items():
                idx = {qn(f'w:{n}'): i for i, n in enumerate(seq)}
                for pr in root.iter(qn(f'w:{tag}')):
                    kids = list(pr)
                    srt = sorted(kids, key=lambda k: idx.get(k.tag, 999))
                    if srt != kids:
                        for k in kids:
                            pr.remove(k)
                        for k in srt:
                            pr.append(k)
        _norm(self.doc.element)
        _norm(self.doc.styles.element)
        for sec in self.doc.sections:
            for hf in (sec.header, sec.footer, sec.first_page_header, sec.first_page_footer):
                _norm(hf._element)
        for z in self.doc.settings.element.findall(qn('w:zoom')):
            z.set(qn('w:percent'), '100')
        self.doc.save(path)
        print(f'Report saved: {path}')


# ── JSON-driven builder ──────────────────────────────────────────────────────
def build_from_config(cfg: dict, output_path: str):
    rb = ReportBuilder(scheme=cfg.get('scheme', 'corporate'))

    cover = cfg.get('cover', {})
    if cover:
        rb.add_cover_page(**cover)

    if cfg.get('toc', True):
        rb.add_toc()

    rb.set_header_footer(
        left_text=cfg.get('header_left', cover.get('title', '')),
        right_text=cfg.get('header_right', 'Confidential'),
        show_page_numbers=True,
    )

    for section in cfg.get('sections', []):
        kind = section.get('type', 'paragraph')
        if kind == 'heading':
            rb.add_heading(section['text'], level=section.get('level', 1))
        elif kind == 'paragraph':
            rb.add_paragraph(section['text'], bold=section.get('bold', False),
                             align=section.get('align', 'left'))
        elif kind == 'bullets':
            rb.add_bullets(section['items'], numbered=section.get('numbered', False))
        elif kind == 'table':
            rb.add_table(section['headers'], section['rows'],
                         col_widths=section.get('col_widths'))
        elif kind == 'image':
            rb.add_image(section['src'], width_inches=section.get('width', 5.5),
                         caption=section.get('caption', ''))
        elif kind == 'page_break':
            rb.add_page_break()
        elif kind == 'callout':
            rb.add_callout(section['text'], style=section.get('style', 'info'))

    rb.save(output_path)


EXAMPLE_CONFIG = {
    "scheme": "corporate",
    "cover": {
        "title": "Q1 2026 Performance Report",
        "subtitle": "Business Review & Strategic Outlook",
        "author": "Analytics Team",
        "date": "March 2026",
        "classification": "CONFIDENTIAL"
    },
    "toc": True,
    "header_left": "Q1 2026 Performance Report",
    "header_right": "Confidential",
    "sections": [
        {"type": "heading", "text": "Executive Summary", "level": 1},
        {"type": "paragraph", "text": "Q1 2026 showed strong growth across all segments, with revenue up 28% YoY driven by enterprise expansion and new product adoption.", "align": "justify"},
        {"type": "callout", "text": "Key Highlight: MRR crossed $2M for the first time in company history.", "style": "tip"},
        {"type": "heading", "text": "Financial Performance", "level": 2},
        {"type": "table",
         "headers": ["Metric", "Q1 2025", "Q1 2026", "YoY Change"],
         "rows": [
             ["Revenue", "$1.56M", "$2.00M", "+28%"],
             ["Gross Margin", "72%", "76%", "+4pp"],
             ["MRR", "$520K", "$666K", "+28%"],
             ["Customers", "842", "1,124", "+33%"]
         ],
         "col_widths": [1.8, 1.4, 1.4, 1.4]},
        {"type": "heading", "text": "Recommendations", "level": 2},
        {"type": "bullets", "items": [
            "Increase enterprise sales headcount by 40% in Q2",
            "Launch self-serve tier to capture SMB market",
            "Invest in customer success to reduce churn below 2%",
            "Expand to APAC region in H2 2026"
        ]}
    ]
}

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        build_from_config(cfg, sys.argv[2])
    else:
        build_from_config(EXAMPLE_CONFIG, 'report_demo.docx')
        print('Demo: report_demo.docx')
