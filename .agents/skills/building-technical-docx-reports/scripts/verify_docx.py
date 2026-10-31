#!/usr/bin/env python3
"""Verify a built .docx against its config: structure, geometry, and no silent loss.

Checks that catch the failures that actually happen in this pipeline:
  * an image dropped, reordered, or stretched (aspect ratio / width)
  * a table wider than the text column, or a cell whose longest word cannot fit
  * a row that splits across pages, or a header row that does not repeat
  * a missing cover line, TOC field, header/footer, or code block
  * markdown leftovers and unescaped entities leaking into the text

Usage:
    python3 verify_docx.py report.docx config.json

Exit code 0 = all checks passed, 1 = at least one failed.
"""
import hashlib
import os
import re
import subprocess
import sys

from docx import Document
from docx.oxml.ns import qn
from PIL import Image, ImageFont

WS = re.compile(r"\s+")
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_VALIDATE = os.path.normpath(os.path.join(SKILL, "..", "docx", "scripts", "office", "validate.py"))
VALIDATE = _LOCAL_VALIDATE if os.path.exists(_LOCAL_VALIDATE) else "/opt/computersetup/abacusai_computer/tools/docx_editing_tools/validate.py"

res = []


def chk(name, ok, info=""):
    res.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (("  " + str(info)) if info else ""))


def font_pair():
    for d in (os.path.join(SKILL, "assets", "fonts"), os.path.expanduser("~/.fonts")):
        reg, bold = os.path.join(d, "Carlito-Regular.ttf"), os.path.join(d, "Carlito-Bold.ttf")
        if os.path.exists(reg) and os.path.exists(bold):
            return (ImageFont.truetype(reg, 90), ImageFont.truetype(bold, 90))
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: verify_docx.py report.docx [config.json]")
    out = os.path.abspath(sys.argv[1])
    cfg = {}
    if len(sys.argv) > 2:
        import json
        cfg = json.load(open(sys.argv[2], encoding="utf-8"))
        cfg["_dir"] = os.path.dirname(os.path.abspath(sys.argv[2]))
    base = cfg.get("base_dir") or cfg.get("_dir", os.path.dirname(out))
    if not os.path.isabs(base):
        base = os.path.join(cfg.get("_dir", os.path.dirname(out)), base)
    exp = cfg.get("expect", {})
    text_w = cfg.get("page", {}).get("width_cm", 21.0) - 2 * cfg.get("page", {}).get("margin_cm", 2.2)

    chk("zip magic", open(out, "rb").read(4) == b"PK\x03\x04")
    d = Document(out)
    chk("reopen with python-docx", True)
    body = d.element.body

    # ---- cover -------------------------------------------------------------
    cover_txt = []
    for el in body.iterchildren():
        if el.tag == qn("w:p"):
            sty = el.find(".//" + qn("w:pStyle"))
            if sty is not None and sty.get(qn("w:val")) in ("TOCTitle", "TOC Title"):
                break
        cover_txt.append("".join(t.text or "" for t in el.iter(qn("w:t"))))
    cover = "\n".join(cover_txt)
    for s in exp.get("cover_strings", []):
        chk("cover: " + s[:48], s in cover)
    first_tbl = body.find(qn("w:tbl"))
    if first_tbl is not None:
        chk("cover band is a filled table", "w:fill=" in first_tbl.xml)

    # ---- images ------------------------------------------------------------
    expected = exp.get("images")
    blips = body.findall(".//" + qn("a:blip"))
    rels = d.part.rels
    order = []
    for b in blips:
        blob = rels[b.get(qn("r:embed"))].target_part.blob
        order.append(hashlib.sha1(blob).hexdigest())
    if expected:
        src = {}
        for e in expected:
            p = e if os.path.isabs(e) else os.path.join(base, e)
            src[hashlib.sha1(open(p, "rb").read()).hexdigest()] = os.path.basename(e)
        names = [src.get(h, "?") for h in order]
        chk("%d embedded images" % len(expected), len(blips) == len(expected), len(blips))
        chk("image order matches the HTML", names == [os.path.basename(e) for e in expected], names)
    else:
        chk("images embedded", len(blips) > 0, len(blips))

    # aspect ratio + width, matched back to source files by hash
    bad = []
    if expected:
        for ext, h in zip(body.findall(".//" + qn("wp:extent")), order):
            nm = src.get(h)
            if not nm:
                continue
            p = os.path.join(base, "assets", nm)
            if not os.path.exists(p):
                p = next((os.path.join(base, e) for e in expected
                          if os.path.basename(e) == nm), None)
            if not p or not os.path.exists(p):
                continue
            w, hh = Image.open(p).size
            cx, cy = int(ext.get("cx")), int(ext.get("cy"))
            if abs(cx / cy - w / hh) > 0.01:
                bad.append(nm + " aspect")
            if cx / 360000 > text_w + 0.05:
                bad.append(nm + " too wide")
        chk("image aspect ratio and width", not bad, bad)

    caps = [p.text for p in d.paragraphs if p.style.name == "Caption"]
    caps += [p.text for t in d.tables for c in t._cells for p in c.paragraphs
             if p.style.name == "Caption"]
    nfig = len(set(c for c in caps if c.strip()))
    if exp.get("figures"):
        chk("%d figure captions" % exp["figures"], nfig == exp["figures"], nfig)
    else:
        chk("figure captions present", nfig > 0, nfig)

    # ---- tables ------------------------------------------------------------
    data = [t for t in body.iter(qn("w:tbl")) if t.find(".//" + qn("w:tblHeader")) is not None]
    if exp.get("data_tables"):
        chk("%d data tables with repeating header" % exp["data_tables"],
            len(data) == exp["data_tables"], len(data))
    else:
        chk("data tables with repeating header", len(data) > 0, len(data))
    all_rows = [tr for t in body.iter(qn("w:tbl")) for tr in t.findall(qn("w:tr"))]
    chk("every row cantSplit", all(tr.find(".//" + qn("w:cantSplit")) is not None
                                   for tr in all_rows))
    wide = []
    for t in body.iter(qn("w:tbl")):
        g = t.find(qn("w:tblGrid"))
        if g is None:
            continue
        w = sum(int(x.get(qn("w:w"))) for x in g.findall(qn("w:gridCol"))) / 1440 * 2.54
        if w > text_w + 0.05:
            wide.append(round(w, 2))
    chk("no table wider than the text column", not wide, wide)

    fp = font_pair()
    if fp:
        fR, fB = fp

        def wcm(text, bold, mono, pt):
            if mono:
                return len(text) * 0.55 * pt / 72 * 2.54
            return (fB if bold else fR).getlength(text) / 90 * pt / 72 * 2.54

        over = []
        for ti, t in enumerate(data):
            g = t.find(qn("w:tblGrid"))
            if g is None:
                continue
            grid = [int(x.get(qn("w:w"))) / 1440 * 2.54 for x in g.findall(qn("w:gridCol"))]
            for tr in t.findall(qn("w:tr")):
                for ci, tc in enumerate(tr.findall(qn("w:tc"))):
                    if ci >= len(grid):
                        continue
                    avail = grid[ci] - 2 * 100 / 1440 * 2.54
                    for r in tc.iter(qn("w:r")):
                        txt = "".join(x.text or "" for x in r.findall(qn("w:t")))
                        rs = r.find(".//" + qn("w:rStyle"))
                        mono = rs is not None and "Code" in rs.get(qn("w:val"))
                        bold = (r.find(".//" + qn("w:b")) is not None
                                or tr.find(".//" + qn("w:tblHeader")) is not None)
                        for tok in txt.split():
                            ww = wcm(tok, bold, mono, 8 if mono else 9)
                            if ww > avail:
                                over.append((ti + 1, tok, round(ww, 2), round(avail, 2)))
        chk("no unbreakable token overflows its cell", not over, over[:10])
    else:
        print("SKIP token-width check (Carlito not found — install it or bundle assets/fonts)")

    # ---- headings, TOC, text ----------------------------------------------
    h1 = [p.text for p in d.paragraphs if p.style.name == "Heading 1"]
    if exp.get("h1"):
        chk("%d Heading 1 chapters" % exp["h1"], len(h1) == exp["h1"], len(h1))
    else:
        chk("Heading 1 chapters present", len(h1) > 0, len(h1))
    if exp.get("h2"):
        n2 = sum(p.style.name == "Heading 2" for p in d.paragraphs)
        chk("%d Heading 2 sections" % exp["h2"], n2 == exp["h2"], n2)
    xml = body.xml
    chk("TOC field present", 'TOC \\o' in xml)
    toc_entries = [p for p in d.paragraphs if p.style.name in ("TOC 1", "TOC 2")]
    chk("TOC entries rendered as static text", len(toc_entries) > 0, len(toc_entries))
    if toc_entries:
        numbered = [p for p in toc_entries if p.runs and p.runs[-1].text.strip().isdigit()]
        chk("TOC page numbers filled", len(numbered) == len(toc_entries),
            "%d/%d" % (len(numbered), len(toc_entries)))
    chk("no &#x entities in text", not any("&#x" in p.text for p in d.paragraphs))
    chk("no markdown leftovers", not any(re.search(r"\*\*|^#+ ", p.text) for p in d.paragraphs))
    if exp.get("code_blocks"):
        n = sum(p.style.name == "Code Block" for p in d.paragraphs)
        chk("%d code blocks" % exp["code_blocks"], n == exp["code_blocks"], n)

    s = d.sections[0]
    chk("distinct first-page header/footer",
        s.different_first_page_header_footer and not s.first_page_header.paragraphs[0].text.strip())
    chk("running header + PAGE footer",
        bool(s.header.paragraphs[0].text.strip()) and "PAGE" in s.footer._element.xml)

    if os.path.exists(VALIDATE):
        v = subprocess.run([sys.executable, VALIDATE, out], capture_output=True, text=True)
        txt = v.stdout + v.stderr
        ok = "All validations PASSED" in txt and not re.search(r"new error\(s\)", txt)
        detail = [ln.strip() for ln in txt.splitlines()
                  if "error" in ln.lower() and "new error" not in ln.lower()][:2]
        chk("OOXML schema validation", ok, detail or txt.strip().splitlines()[-1:])
    else:
        print("SKIP schema validation (validate.py not installed)")

    print("ALL PASS" if all(res) else "SOME FAIL (%d/%d)" % (sum(res), len(res)))
    sys.exit(0 if all(res) else 1)


if __name__ == "__main__":
    main()
