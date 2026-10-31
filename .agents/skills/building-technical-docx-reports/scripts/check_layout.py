#!/usr/bin/env python3
"""Render a .docx to PDF and report layout problems that only show up on the page.

Catches: near-empty pages (an orphaned bullet or a stray caption pushed a page),
text or images running past the margins, images clipped by the page edge, and the
overall page count. Run it after every build; a page with fewer than --min-lines
lines of text is almost always a spacing bug, not a design choice.

Usage:
    python3 check_layout.py report.docx [--min-lines 8] [--keep-pdf out.pdf] [--margin-cm 2.2]
"""
import os
import subprocess
import sys
import tempfile

import pymupdf

PT_CM = 72 / 2.54


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: check_layout.py report.docx [--min-lines 8] [--keep-pdf out.pdf]")
    docx_path = os.path.abspath(sys.argv[1])
    min_lines = int(sys.argv[sys.argv.index("--min-lines") + 1]) if "--min-lines" in sys.argv else 8
    keep = sys.argv[sys.argv.index("--keep-pdf") + 1] if "--keep-pdf" in sys.argv else None
    margin = float(sys.argv[sys.argv.index("--margin-cm") + 1]) if "--margin-cm" in sys.argv else 2.2

    tmp = tempfile.mkdtemp(prefix="checklayout_")
    from pathlib import Path
    profile_uri = Path(tmp).resolve().as_uri()
    subprocess.run(["soffice", f"-env:UserInstallation={profile_uri}", "--headless", "--convert-to", "pdf", "--outdir", tmp, docx_path],
                   check=True, capture_output=True, timeout=900)
    pdf = os.path.join(tmp, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit("check_layout.py: LibreOffice produced no PDF")
    if keep:
        subprocess.run(["cp", pdf, keep], check=True)

    doc = pymupdf.open(pdf)
    sparse, overflow, clipped = [], [], []
    print("pages: %d" % doc.page_count)
    for i, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        lines = [ln for blk in page.get_text("blocks") for ln in blk[4].splitlines() if ln.strip()]
        imgs = page.get_image_info()  # images actually drawn on this page
        if len(lines) < min_lines and not imgs:
            sparse.append((i, len(lines)))
        for blk in page.get_text("blocks"):
            if blk[2] > W - margin * PT_CM + 6:
                overflow.append((i, round(blk[2] / PT_CM, 2)))
                break
        for info in page.get_image_info():
            x0, y0, x1, y1 = info["bbox"]
            if y1 > H - 4 or x1 > W - 4 or x0 < 4:
                clipped.append((i, [round(v / PT_CM, 2) for v in info["bbox"]]))
        print("  p%-3d lines %-3d images %d" % (i, len(lines), len(imgs)))

    print()
    if sparse:
        print("SPARSE PAGES (fewer than %d text lines): %s" % (min_lines, sparse))
    if overflow:
        print("TEXT PAST THE RIGHT MARGIN: %s" % overflow[:10])
    if clipped:
        print("IMAGE TOUCHING/OVERFLOWING THE PAGE EDGE: %s" % clipped[:10])
    if not (sparse or overflow or clipped):
        print("LAYOUT OK")
    if not keep:
        subprocess.run(["rm", "-rf", tmp])


if __name__ == "__main__":
    main()
