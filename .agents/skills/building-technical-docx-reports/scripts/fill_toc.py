#!/usr/bin/env python3
"""Fill the page numbers of a static TOC result region by measuring the rendered PDF.

The builder emits the TOC as a real Word field whose *result* is a list of
`TOC 1` / `TOC 2` paragraphs ending in a tab and a placeholder number. Word shows
that result immediately (no "update field" prompt) and can still refresh it with F9.
This script renders the .docx to PDF, finds the page where each heading actually
lands, and rewrites the placeholder numbers.

Usage:
    python3 fill_toc.py report.docx [--pdf existing.pdf] [--keep-pdf out.pdf]

Requires: libreoffice (soffice), pymupdf, python-docx.
"""
import os
import re
import subprocess
import sys
import tempfile

import pymupdf
from docx import Document
from docx.oxml.ns import qn

WS = re.compile(r"\s+")


def norm(s):
    return WS.sub(" ", s.replace("\u00ad", "")).strip().lower()


def to_pdf(docx_path, workdir):
    from pathlib import Path
    profile_uri = Path(workdir).resolve().as_uri()
    subprocess.run(["soffice", f"-env:UserInstallation={profile_uri}", "--headless", "--convert-to", "pdf", "--outdir", workdir, docx_path],
                   check=True, capture_output=True, timeout=600)
    pdf = os.path.join(workdir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf):
        sys.exit("fill_toc.py: LibreOffice produced no PDF")
    return pdf


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: fill_toc.py report.docx [--pdf file.pdf] [--keep-pdf out.pdf]")
    docx_path = os.path.abspath(sys.argv[1])
    keep = sys.argv[sys.argv.index("--keep-pdf") + 1] if "--keep-pdf" in sys.argv else None

    doc = Document(docx_path)
    entries = [p for p in doc.paragraphs if p.style.name in ("TOC 1", "TOC 2")]
    if not entries:
        sys.exit("fill_toc.py: no TOC 1 / TOC 2 paragraphs found — nothing to fill")
    title = next((p.text.strip() for p in doc.paragraphs if p.style.name == "TOC Title"), "")

    if "--pdf" in sys.argv:
        pdf = sys.argv[sys.argv.index("--pdf") + 1]
        tmp = None
    else:
        tmp = tempfile.mkdtemp(prefix="filltoc_")
        pdf = to_pdf(docx_path, tmp)
    if keep:
        subprocess.run(["cp", pdf, keep], check=True)

    pages = [norm(pg.get_text()) for pg in pymupdf.open(pdf)]
    # The TOC pages are the ones carrying dot leaders; skip them (and the cover) so a
    # heading is never "found" inside the index itself.
    dot_pages = [i for i, t in enumerate(pages[:12]) if re.search(r"\.{20,}", t)]
    start = max(dot_pages) + 1 if dot_pages else 0
    if not dot_pages and title:
        hits = [i for i, t in enumerate(pages) if norm(title) in t]
        if hits:
            start = hits[0] + 1

    filled, missing = 0, []
    for e in entries:
        label = norm(e.text.split("\t")[0])  # drop the tab + placeholder page number
        key = label[:45]
        found = None
        for i in range(start, len(pages)):
            if key and key in pages[i]:
                found = i
                break
        if found is None:
            missing.append(e.text[:60])
            continue
        start = found
        runs = e.runs
        if not runs:
            continue
        runs[-1].text = str(found + 1)
        filled += 1

    doc.save(docx_path)
    print("fill_toc.py: %d/%d entries numbered, %d pages" % (filled, len(entries), len(pages)))
    if missing:
        print("  not located (kept placeholder): " + " | ".join(missing[:8]))
    if tmp and not keep:
        subprocess.run(["rm", "-rf", tmp])


if __name__ == "__main__":
    main()
