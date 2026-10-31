# Professional Styles & Formatting Reference

## Complete Professional Style Set

Use this as the base style definition for any professional document. Copy this into your script.

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn


def setup_professional_styles(doc: Document, scheme: str = 'corporate'):
    """Apply professional styles to the document.
    Schemes: 'corporate', 'modern', 'traditional', 'creative'
    """
    SCHEMES = {
        'corporate': {
            'primary': RGBColor(0x1a, 0x36, 0x5d),      # Navy
            'secondary': RGBColor(0x2c, 0x5f, 0x8a),     # Steel blue
            'accent': RGBColor(0x3b, 0x82, 0xf6),        # Blue
            'text': RGBColor(0x1f, 0x2a, 0x37),          # Dark gray
            'muted': RGBColor(0x64, 0x74, 0x8b),         # Slate
            'heading_font': 'Calibri',
            'body_font': 'Calibri',
        },
        'modern': {
            'primary': RGBColor(0x0f, 0x17, 0x2a),       # Near black
            'secondary': RGBColor(0x33, 0x41, 0x55),      # Gray
            'accent': RGBColor(0x6366, 0xf1 >> 8, 0xf1 & 0xFF),  # fallback below
            'text': RGBColor(0x1e, 0x29, 0x3b),
            'muted': RGBColor(0x94, 0xa3, 0xb8),
            'heading_font': 'Arial',
            'body_font': 'Arial',
        },
        'traditional': {
            'primary': RGBColor(0x5c, 0x21, 0x18),       # Maroon
            'secondary': RGBColor(0x78, 0x35, 0x0f),      # Brown
            'accent': RGBColor(0xb4, 0x5a, 0x09),        # Gold
            'text': RGBColor(0x27, 0x27, 0x27),
            'muted': RGBColor(0x73, 0x73, 0x73),
            'heading_font': 'Georgia',
            'body_font': 'Georgia',
        },
        'creative': {
            'primary': RGBColor(0x7c, 0x3a, 0xed),       # Purple
            'secondary': RGBColor(0xec, 0x48, 0x99),      # Pink
            'accent': RGBColor(0xf5, 0x93, 0x0e),        # Amber
            'text': RGBColor(0x18, 0x18, 0x1b),
            'muted': RGBColor(0x71, 0x71, 0x7a),
            'heading_font': 'Arial',
            'body_font': 'Arial',
        },
    }
    # Fix modern accent
    SCHEMES['modern']['accent'] = RGBColor(0x63, 0x66, 0xf1)

    s = SCHEMES.get(scheme, SCHEMES['corporate'])

    # Normal style
    normal = doc.styles['Normal']
    normal.font.name = s['body_font']
    normal.font.size = Pt(11)
    normal.font.color.rgb = s['text']
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)

    # Heading styles
    for level, size, spacing_before in [(1, 22, 36), (2, 16, 24), (3, 13, 18)]:
        style_name = f'Heading {level}'
        h = doc.styles[style_name]
        h.font.name = s['heading_font']
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = s['primary']
        h.paragraph_format.space_before = Pt(spacing_before)
        h.paragraph_format.space_after = Pt(8)
        h.paragraph_format.keep_with_next = True

    # Title style
    title = doc.styles['Title']
    title.font.name = s['heading_font']
    title.font.size = Pt(28)
    title.font.bold = True
    title.font.color.rgb = s['primary']
    title.paragraph_format.space_after = Pt(4)

    # Subtitle
    subtitle = doc.styles['Subtitle']
    subtitle.font.name = s['body_font']
    subtitle.font.size = Pt(14)
    subtitle.font.color.rgb = s['muted']
    subtitle.paragraph_format.space_after = Pt(24)

    return s  # Return scheme for use in custom elements
```

## Run-Level Formatting

```python
run = paragraph.add_run('text')

# Font properties
run.font.name = 'Calibri'
run.font.size = Pt(11)
run.font.bold = True
run.font.italic = True
run.font.underline = True
run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
run.font.all_caps = True
run.font.small_caps = True
run.font.strike = True          # Strikethrough
run.font.superscript = True
run.font.subscript = True
run.font.highlight_color = 7    # Yellow highlight (WD_COLOR_INDEX.YELLOW)
```

## Paragraph-Level Formatting

```python
pf = paragraph.paragraph_format

# Alignment
pf.alignment = WD_ALIGN_PARAGRAPH.LEFT      # LEFT, CENTER, RIGHT, JUSTIFY

# Spacing
pf.space_before = Pt(12)
pf.space_after = Pt(6)
pf.line_spacing = 1.5           # Multiple
pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
pf.line_spacing = Pt(14)        # Exact points

# Indentation
pf.left_indent = Inches(0.5)
pf.right_indent = Inches(0.5)
pf.first_line_indent = Inches(0.25)

# Pagination
pf.keep_together = True         # Don't split paragraph across pages
pf.keep_with_next = True        # Keep with next paragraph (for headings)
pf.page_break_before = True     # Start on new page
pf.widow_control = True         # Avoid orphan/widow lines
```

## Bullet Lists and Numbered Lists

```python
# Bullet list
doc.add_paragraph('First item', style='List Bullet')
doc.add_paragraph('Second item', style='List Bullet')
doc.add_paragraph('Sub-item', style='List Bullet 2')

# Numbered list
doc.add_paragraph('Step one', style='List Number')
doc.add_paragraph('Step two', style='List Number')
doc.add_paragraph('Sub-step', style='List Number 2')
```

## Hyperlinks

python-docx doesn't have a native hyperlink API. Use XML:

```python
def add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    hyperlink = paragraph._p.makeelement(qn('w:hyperlink'), {qn('r:id'): r_id})
    new_run = paragraph._p.makeelement(qn('w:r'), {})
    rPr = paragraph._p.makeelement(qn('w:rPr'), {})
    c = paragraph._p.makeelement(qn('w:color'), {qn('w:val'): '0563C1'})
    u = paragraph._p.makeelement(qn('w:u'), {qn('w:val'): 'single'})
    rPr.append(c)
    rPr.append(u)
    new_run.append(rPr)
    new_run.text = text
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
```

## Borders and Shading

### Paragraph Border (Bottom Line — Useful for Section Dividers)
```python
def add_bottom_border(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.makeelement(qn('w:pBdr'), {})
    bottom = pBdr.makeelement(qn('w:bottom'), {
        qn('w:val'): 'single',
        qn('w:sz'): '4',
        qn('w:space'): '1',
        qn('w:color'): 'CCCCCC',
    })
    pBdr.append(bottom)
    pPr.append(pBdr)
```

### Cell Shading
```python
def shade_cell(cell, color_hex: str):
    """Shade a table cell. color_hex without #, e.g. 'E8F0FE'."""
    shading = cell._tc.get_or_add_tcPr().makeelement(qn('w:shd'), {
        qn('w:val'): 'clear',
        qn('w:color'): 'auto',
        qn('w:fill'): color_hex,
    })
    cell._tc.get_or_add_tcPr().append(shading)
```

## Column Layout (Two-Column Sections)
```python
from docx.oxml.ns import qn

section = doc.sections[-1]
sectPr = section._sectPr
cols = sectPr.makeelement(qn('w:cols'), {
    qn('w:num'): '2',
    qn('w:space'): '720',  # Space between columns in twips (720 = 0.5 inch)
})
sectPr.append(cols)
```

## Watermark Text
```python
def add_watermark(section, text='DRAFT'):
    """Add a diagonal watermark to the document."""
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()

    # VML shape for watermark
    from lxml import etree
    nsmap = {'v': 'urn:schemas-microsoft-com:vml', 'o': 'urn:schemas-microsoft-com:office:office'}
    shape = etree.SubElement(p._p, qn('w:r'))
    pict = etree.SubElement(shape, qn('w:pict'))

    vml = f'''<v:shape xmlns:v="urn:schemas-microsoft-com:vml"
        style="position:absolute;margin-left:0;margin-top:0;width:500pt;height:200pt;rotation:315;z-index:-251658752"
        fillcolor="silver" stroked="f">
        <v:textpath style="font-family:Calibri;font-size:72pt" string="{text}"/>
    </v:shape>'''

    elem = etree.fromstring(vml)
    pict.append(elem)
```

## docxtpl — Template-Driven Generation

`docxtpl` (python-docx-template) uses Jinja2 inside `.docx` files. The template is a real Word document you design normally, then embed tags.

### Template tags
```
{{ variable }}                    simple value substitution
{{ item.price | round(2) }}       Jinja2 filters work
{% for row in rows %}...{% endfor %}  loops inside table rows
{% if is_vip %}...{% endif %}     conditionals
{{ image_obj }}                   embed an InlineImage
```

### Inline images via docxtpl
```python
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Inches

tpl = DocxTemplate('template.docx')
context = {
    'logo': InlineImage(tpl, '/path/to/logo.png', width=Inches(2)),
    'chart': InlineImage(tpl, '/path/to/chart.png', width=Inches(5)),
}
tpl.render(context)
tpl.save('output.docx')
```

### Tables with dynamic rows
In the Word template, create a table with a header row and one data row. In the data row, use:
```
{% for item in items %}
| {{ item.description }} | {{ item.quantity }} | ${{ item.price }} |
{% endfor %}
```
docxtpl expands the loop row automatically, preserving all cell styles.

### Rich text (pre-formatted HTML-like content)
```python
from docxtpl import DocxTemplate, RichText

tpl = DocxTemplate('template.docx')
rt = RichText()
rt.add('Important:', bold=True, color='FF0000')
rt.add(' this term applies to all parties.')
context = {'notice': rt}
tpl.render(context)
```
