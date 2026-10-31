# Images in DOCX — Complete Guide

## Adding Images

```python
from docx.shared import Inches, Cm, Emu

# Basic — full width with auto height
doc.add_picture('/path/to/image.png', width=Inches(6))

# Specific dimensions
doc.add_picture('/path/to/image.png', width=Inches(4), height=Inches(3))

# From URL (download first)
import urllib.request
urllib.request.urlretrieve('https://example.com/image.png', '/tmp/img.png')
doc.add_picture('/tmp/img.png', width=Inches(5))

# From bytes (BytesIO)
from io import BytesIO
image_stream = BytesIO(image_bytes)
doc.add_picture(image_stream, width=Inches(5))
```

## Centering Images

```python
doc.add_picture('/path/to/image.png', width=Inches(4))
last_paragraph = doc.paragraphs[-1]
last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## Image with Caption

```python
# Add image
doc.add_picture('/path/to/chart.png', width=Inches(5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

# Add caption
caption = doc.add_paragraph('Figure 1: Quarterly Revenue Growth', style='Caption')
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.runs[0].font.size = Pt(9)
caption.runs[0].font.italic = True
caption.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8b)
```

## Inline Images (Within a Paragraph)

```python
paragraph = doc.add_paragraph('Here is the logo: ')
run = paragraph.add_run()
run.add_picture('/path/to/logo.png', width=Inches(0.5))
paragraph.add_run(' followed by text.')
```

## Image in Table Cell

```python
cell = table.cell(0, 0)
cell_paragraph = cell.paragraphs[0]
run = cell_paragraph.add_run()
run.add_picture('/path/to/image.png', width=Inches(1.5))
cell_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## Image Border

```python
from lxml import etree

def add_image_border(paragraph, color='000000', width_pt=1):
    """Add a border around the last inline image in the paragraph."""
    # Find the drawing element
    for run in paragraph.runs:
        drawings = run._r.findall(qn('w:drawing'))
        for drawing in drawings:
            inline = drawing.find(qn('wp:inline'))
            if inline is not None:
                # Add effect extent
                extent = inline.find(qn('wp:effectExtent'))
                if extent is None:
                    extent = inline.makeelement(qn('wp:effectExtent'), {
                        'l': '0', 't': '0', 'r': '0', 'b': '0'
                    })
```

## Generating Charts as Images

Use matplotlib to generate chart images, then embed:

```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Create chart
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(['Q1', 'Q2', 'Q3', 'Q4'], [120, 150, 180, 210])
ax.set_title('Quarterly Revenue ($K)')
fig.savefig('/tmp/chart.png', dpi=150, bbox_inches='tight', transparent=False)
plt.close()

# Embed in document
doc.add_picture('/tmp/chart.png', width=Inches(6))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## Image Size Guidelines

| Context | Recommended Width | Notes |
|---|---|---|
| Full-page image | 6.0-6.5 inches | Depends on margins |
| Half-page | 3.0-3.5 inches | |
| Inline logo | 0.3-0.8 inches | In headers/footers |
| Chart/graph | 5.0-6.0 inches | Readable labels |
| Thumbnail | 1.0-1.5 inches | In tables |
| Signature | 1.5-2.0 inches | Scanned signature |

## DPI Considerations

- Screen viewing: 96-150 DPI is fine
- Print: use 300 DPI source images
- For matplotlib charts: `fig.savefig(..., dpi=150)` is a good balance
- python-docx embeds the image at its native resolution and scales display size via width/height
