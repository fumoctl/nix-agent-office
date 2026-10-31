"""
Professional Invoice Generator
Usage: python invoice_generator.py config.json output.docx
Config JSON format: see bottom of file for example.
"""

import json
import sys
from datetime import datetime
from io import BytesIO

import requests
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


# ── colours ────────────────────────────────────────────────────────────────
PRIMARY   = RGBColor(0x1a, 0x36, 0x5d)   # navy
MUTED     = RGBColor(0x64, 0x74, 0x8b)   # slate
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG  = 'F8FAFC'
HEADER_BG = '1A365D'


def _shade(cell, hex_color: str):
    el = cell._tc.get_or_add_tcPr().makeelement(
        qn('w:shd'), {qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): hex_color})
    cell._tc.get_or_add_tcPr().append(el)


def _cell_margins(cell, top=60, bottom=60, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = tcPr.makeelement(qn('w:tcMar'), {})
    for side, val in [('top', top), ('left', left), ('bottom', bottom), ('right', right)]:
        tcMar.append(tcMar.makeelement(qn(f'w:{side}'), {qn('w:w'): str(val), qn('w:type'): 'dxa'}))
    tcPr.append(tcMar)


def _remove_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else tbl.makeelement(qn('w:tblPr'), {})
    bdr = tblPr.makeelement(qn('w:tblBorders'), {})
    for name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        bdr.append(bdr.makeelement(qn(f'w:{name}'), {qn('w:val'): 'nil'}))
    tblPr.append(bdr)


def generate_invoice(cfg: dict, output_path: str):
    doc = Document()

    # ── page setup ──────────────────────────────────────────────────────────
    sec = doc.sections[0]
    sec.page_width  = Inches(8.5)
    sec.page_height = Inches(11)
    sec.top_margin    = Inches(0.75)
    sec.bottom_margin = Inches(0.75)
    sec.left_margin   = Inches(0.9)
    sec.right_margin  = Inches(0.9)

    # ── global styles ───────────────────────────────────────────────────────
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(10)
    doc.styles['Normal'].font.color.rgb = RGBColor(0x1f, 0x29, 0x37)

    # ── header: logo | INVOICE block ────────────────────────────────────────
    hdr_table = doc.add_table(rows=1, cols=2)
    _remove_borders(hdr_table)
    hdr_table.columns[0].width = Inches(3.5)
    hdr_table.columns[1].width = Inches(3.2)

    # Left: logo + company
    left = hdr_table.rows[0].cells[0]
    logo_url = cfg.get('company', {}).get('logo_url')
    if logo_url:
        try:
            r = requests.get(logo_url, timeout=10)
            run = left.paragraphs[0].add_run()
            run.add_picture(BytesIO(r.content), width=Inches(1.6))
        except Exception:
            pass
    company = cfg.get('company', {})
    for line in [company.get('name', ''), company.get('address', ''),
                 company.get('city_state_zip', ''), company.get('email', ''), company.get('phone', '')]:
        if line:
            p = left.add_paragraph(line)
            p.paragraph_format.space_after = Pt(0)
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.color.rgb = MUTED

    # Right: INVOICE label + meta
    right = hdr_table.rows[0].cells[1]
    title_p = right.paragraphs[0]
    title_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = title_p.add_run('INVOICE')
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = PRIMARY

    for label, key in [('Invoice #', 'invoice_number'), ('Date', 'date'), ('Due Date', 'due_date')]:
        p = right.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(f'{label}: ')
        run.font.bold = True
        run.font.size = Pt(9)
        run = p.add_run(cfg.get(key, ''))
        run.font.size = Pt(9)

    doc.add_paragraph()  # spacer

    # ── bill-to / ship-to ───────────────────────────────────────────────────
    bt_table = doc.add_table(rows=1, cols=2)
    _remove_borders(bt_table)

    def _address_block(cell, heading, addr: dict):
        hp = cell.paragraphs[0]
        hp.paragraph_format.space_after = Pt(2)
        r = hp.add_run(heading)
        r.font.bold = True
        r.font.color.rgb = PRIMARY
        r.font.size = Pt(9)
        for line in [addr.get('name', ''), addr.get('address', ''),
                     addr.get('city_state_zip', ''), addr.get('email', '')]:
            if line:
                p = cell.add_paragraph(line)
                p.paragraph_format.space_after = Pt(0)
                p.runs[0].font.size = Pt(10)

    _address_block(bt_table.rows[0].cells[0], 'BILL TO', cfg.get('bill_to', {}))
    if cfg.get('ship_to'):
        _address_block(bt_table.rows[0].cells[1], 'SHIP TO', cfg.get('ship_to', {}))

    doc.add_paragraph()  # spacer

    # ── line items table ────────────────────────────────────────────────────
    items = cfg.get('items', [])
    tbl = doc.add_table(rows=1 + len(items), cols=5)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    col_widths = [0.4, 3.2, 0.8, 1.0, 1.0]
    for row in tbl.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = Inches(w)

    # Header row
    for cell in tbl.rows[0].cells:
        _shade(cell, HEADER_BG)
        _cell_margins(cell)
    headers = ['#', 'Description', 'Qty', 'Unit Price', 'Amount']
    for i, h in enumerate(headers):
        p = tbl.rows[0].cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i != 1 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.size = Pt(9)

    # Data rows
    subtotal = 0.0
    for ri, item in enumerate(items, 1):
        qty   = float(item.get('qty', 1))
        rate  = float(item.get('unit_price', 0))
        amount = qty * rate
        subtotal += amount

        row = tbl.rows[ri]
        if ri % 2 == 0:
            for cell in row.cells:
                _shade(cell, LIGHT_BG)
        for cell in row.cells:
            _cell_margins(cell)

        values = [str(ri), item.get('description', ''), str(qty if qty != int(qty) else int(qty)),
                  f"${rate:,.2f}", f"${amount:,.2f}"]
        for ci, val in enumerate(values):
            p = row.cells[ci].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in (0, 2, 3, 4) else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.size = Pt(10)

    # ── totals ──────────────────────────────────────────────────────────────
    tax_rate    = float(cfg.get('tax_rate', 0))
    discount    = float(cfg.get('discount_amount', 0))
    tax_amount  = subtotal * (tax_rate / 100)
    total       = subtotal + tax_amount - discount

    totals_data = [('Subtotal', subtotal)]
    if tax_rate:
        totals_data.append((f'Tax ({tax_rate:.0f}%)', tax_amount))
    if discount:
        totals_data.append(('Discount', -discount))
    totals_data.append(('TOTAL DUE', total))

    totals_tbl = doc.add_table(rows=len(totals_data), cols=2)
    _remove_borders(totals_tbl)
    totals_tbl.alignment = WD_TABLE_ALIGNMENT.RIGHT
    totals_tbl.columns[0].width = Inches(4.7)
    totals_tbl.columns[1].width = Inches(1.5)

    for ri, (label, amount) in enumerate(totals_data):
        is_total = label == 'TOTAL DUE'
        for ci, val in enumerate([label, f"${amount:,.2f}"]):
            p = totals_tbl.rows[ri].cells[ci].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.size = Pt(11 if is_total else 10)
            r.font.bold = is_total
            r.font.color.rgb = PRIMARY if is_total else RGBColor(0x1f, 0x29, 0x37)

    # ── footer: notes + payment terms ───────────────────────────────────────
    doc.add_paragraph()
    if cfg.get('notes'):
        np = doc.add_paragraph()
        run = np.add_run('Notes: ')
        run.bold = True
        run.font.size = Pt(9)
        run = np.add_run(cfg['notes'])
        run.font.size = Pt(9)
        run.font.color.rgb = MUTED

    if cfg.get('payment_terms'):
        pp = doc.add_paragraph()
        run = pp.add_run('Payment Terms: ')
        run.bold = True
        run.font.size = Pt(9)
        run = pp.add_run(cfg['payment_terms'])
        run.font.size = Pt(9)
        run.font.color.rgb = MUTED

    order = {
        'pPr': ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl',
                'numPr', 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens',
                'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE',
                'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid', 'spacing',
                'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
                'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr',
                'sectPr', 'pPrChange'],
        'tblPr': ['tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize',
                  'tblStyleColBandSize', 'tblW', 'jc', 'tblCellSpacing', 'tblInd',
                  'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook', 'tblCaption',
                  'tblDescription'],
        'tcPr': ['cnfStyle', 'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd',
                 'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark'],
    }
    for tag, seq in order.items():
        idx = {qn(f'w:{n}'): i for i, n in enumerate(seq)}
        for pr in doc.element.iter(qn(f'w:{tag}')):
            kids = list(pr)
            srt = sorted(kids, key=lambda k: idx.get(k.tag, 999))
            if srt != kids:
                for k in kids:
                    pr.remove(k)
                for k in srt:
                    pr.append(k)
    for z in doc.settings.element.findall(qn('w:zoom')):
        z.set(qn('w:percent'), '100')
    doc.save(output_path)
    print(f'Invoice saved: {output_path}')


# ── example config ──────────────────────────────────────────────────────────
EXAMPLE_CONFIG = {
    "invoice_number": "INV-2026-001",
    "date": "March 3, 2026",
    "due_date": "April 2, 2026",
    "company": {
        "name": "Acme Design Studio",
        "address": "123 Creative Street",
        "city_state_zip": "San Francisco, CA 94105",
        "email": "billing@acme.com",
        "phone": "(415) 555-0100",
        "logo_url": ""
    },
    "bill_to": {
        "name": "TechCorp Inc.",
        "address": "456 Innovation Ave, Suite 200",
        "city_state_zip": "New York, NY 10001",
        "email": "accounts@techcorp.com"
    },
    "items": [
        {"description": "Brand Identity Design", "qty": 1, "unit_price": 3500},
        {"description": "Website Redesign (10 pages)", "qty": 1, "unit_price": 4800},
        {"description": "Logo Variations & Guidelines", "qty": 1, "unit_price": 800},
        {"description": "Revision Rounds", "qty": 3, "unit_price": 150}
    ],
    "tax_rate": 8.5,
    "discount_amount": 200,
    "notes": "Payment due within 30 days. Late payments subject to 1.5% monthly interest.",
    "payment_terms": "Bank transfer: Chase Bank | Account: 123456789 | Routing: 021000021"
}

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        with open(sys.argv[1]) as f:
            cfg = json.load(f)
        generate_invoice(cfg, sys.argv[2])
    else:
        # Demo with example config
        generate_invoice(EXAMPLE_CONFIG, 'invoice_demo.docx')
        print('Demo invoice created: invoice_demo.docx')
