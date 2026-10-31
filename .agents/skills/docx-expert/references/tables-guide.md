# Tables — Complete Guide

## Basic Table Creation

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()
table = doc.add_table(rows=4, cols=3)
table.style = 'Table Grid'          # Visible borders
table.alignment = WD_TABLE_ALIGNMENT.CENTER
```

## Extending an Existing Styled Table

`existing_table.add_row()` appends a row with **default cell properties** — no inherited shading, borders, fonts, or padding. New rows render unstyled while the original rows keep their styling.

To preserve styling, deep-copy an existing row's `<w:tr>` element and append the clone:

```python
from copy import deepcopy

def clone_row(table, source_row_index=-1):
    """Append a row that inherits cell shading/borders/fonts from an existing row."""
    template_tr = table.rows[source_row_index]._tr
    table._tbl.append(deepcopy(template_tr))
    return table.rows[-1]

new_row = clone_row(existing_table)              # clones the last row's styling
new_row.cells[0].text = 'col 1 value'
new_row.cells[1].text = 'col 2 value'
```

**Note:** setting `cell.text = "..."` replaces the cell's paragraphs with a single fresh paragraph; run-level formatting (font size, color, bold) on the cloned cell is reset on that paragraph. To preserve run formatting, edit `paragraph.runs[0].text` directly:

```python
for paragraph in new_row.cells[0].paragraphs:
    if paragraph.runs:
        paragraph.runs[0].text = 'col 1 value'
        for run in paragraph.runs[1:]:
            run.text = ''
```

If the source row contains placeholder text from the original document, clear it before writing new content (otherwise `cell.text = "..."` is fine; you only need the run-preservation pattern when you specifically want to inherit run formatting).

## Setting Column Widths

```python
# Method: set preferred width on each cell in the column
for row in table.rows:
    row.cells[0].width = Inches(1.5)
    row.cells[1].width = Inches(3.0)
    row.cells[2].width = Inches(1.5)
```

## Setting Row Height

```python
row = table.rows[0]
row.height = Cm(1.2)
row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY  # EXACTLY, AT_LEAST, AUTO
```

## Header Row Styling

```python
def style_header_row(table, bg_color='1A365D', text_color='FFFFFF'):
    """Style the first row as a header with background color and white text."""
    for cell in table.rows[0].cells:
        # Background
        shading = cell._tc.get_or_add_tcPr().makeelement(qn('w:shd'), {
            qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): bg_color,
        })
        cell._tc.get_or_add_tcPr().append(shading)
        # Text
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor.from_string(text_color)
                run.font.size = Pt(10)
```

## Alternating Row Colors (Zebra Striping)

```python
def zebra_stripe(table, even_color='F8FAFC', odd_color='FFFFFF'):
    """Apply alternating row colors starting from row 1 (skip header)."""
    for i, row in enumerate(table.rows[1:], 1):
        color = even_color if i % 2 == 0 else odd_color
        for cell in row.cells:
            shading = cell._tc.get_or_add_tcPr().makeelement(qn('w:shd'), {
                qn('w:val'): 'clear', qn('w:color'): 'auto', qn('w:fill'): color,
            })
            cell._tc.get_or_add_tcPr().append(shading)
```

## Merging Cells

```python
# Horizontal merge
table.cell(0, 0).merge(table.cell(0, 2))  # Merge row 0, cols 0-2

# Vertical merge
table.cell(1, 0).merge(table.cell(3, 0))  # Merge col 0, rows 1-3
```

## Cell Padding / Margins

```python
def set_cell_margins(cell, top=50, bottom=50, left=100, right=100):
    """Set cell margins in twips (1 inch = 1440 twips)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.makeelement(qn('w:tcMar'), {})
    for side, val in [('top', top), ('bottom', bottom), ('start', left), ('end', right)]:
        el = tcMar.makeelement(qn(f'w:{side}'), {qn('w:w'): str(val), qn('w:type'): 'dxa'})
        tcMar.append(el)
    tcPr.append(tcMar)
```

## Vertical Alignment in Cells

```python
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER  # TOP, CENTER, BOTTOM
```

## Cell Borders (Fine Control)

```python
def set_cell_border(cell, **kwargs):
    """Set border for a cell.
    kwargs: top, bottom, start, end, insideH, insideV
    Each value: dict with 'val', 'sz', 'color', 'space'
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.makeelement(qn('w:tcBorders'), {})
    for edge, attrs in kwargs.items():
        element = tcBorders.makeelement(qn(f'w:{edge}'), {
            qn('w:val'): attrs.get('val', 'single'),
            qn('w:sz'): str(attrs.get('sz', '4')),
            qn('w:space'): str(attrs.get('space', '0')),
            qn('w:color'): attrs.get('color', '000000'),
        })
        tcBorders.append(element)
    tcPr.append(tcBorders)

# Usage:
set_cell_border(cell,
    top={'val': 'single', 'sz': '4', 'color': 'CCCCCC'},
    bottom={'val': 'single', 'sz': '4', 'color': 'CCCCCC'},
    start={'val': 'nil'},  # No left border
    end={'val': 'nil'},    # No right border
)
```

## Remove All Borders (Invisible Table — Useful for Layouts)

```python
def remove_table_borders(table):
    """Remove all borders from a table (invisible layout table)."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else tbl.makeelement(qn('w:tblPr'), {})
    borders = tblPr.makeelement(qn('w:tblBorders'), {})
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = borders.makeelement(qn(f'w:{border_name}'), {
            qn('w:val'): 'nil',
        })
        borders.append(border)
    tblPr.append(borders)
```

## Common Table Patterns

### Data Table (with totals)
```python
headers = ['Item', 'Quantity', 'Unit Price', 'Total']
data = [
    ['Widget A', '10', '$25.00', '$250.00'],
    ['Widget B', '5', '$40.00', '$200.00'],
    ['Widget C', '20', '$15.00', '$300.00'],
]
total = '$750.00'

table = doc.add_table(rows=1 + len(data) + 1, cols=4)
table.style = 'Table Grid'

# Header
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h

style_header_row(table)

# Data
for r, row_data in enumerate(data, 1):
    for c, val in enumerate(row_data):
        table.rows[r].cells[c].text = val
        if c >= 1:  # Right-align numbers
            table.rows[r].cells[c].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

# Totals row
totals_row = table.rows[-1]
totals_row.cells[0].merge(totals_row.cells[2])
totals_row.cells[0].text = 'Total'
totals_row.cells[0].paragraphs[0].runs[0].bold = True if totals_row.cells[0].paragraphs[0].runs else None
totals_row.cells[-1].text = total
```

### Key-Value Layout (No Visible Table)
```python
# Use invisible table for aligned key-value pairs
table = doc.add_table(rows=4, cols=2)
remove_table_borders(table)
pairs = [('Invoice #:', 'INV-2024-001'), ('Date:', 'March 3, 2026'),
         ('Due Date:', 'April 2, 2026'), ('Status:', 'Pending')]
for i, (key, val) in enumerate(pairs):
    k_run = table.rows[i].cells[0].paragraphs[0].add_run(key)
    k_run.bold = True
    table.rows[i].cells[1].text = val
```
