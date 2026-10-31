#!/usr/bin/env python3
"""Accept all tracked changes in a DOCX file (pure Python — no LibreOffice).

Operates directly on the OOXML zip via lxml. Handles:
  - <w:ins>, <w:moveTo>      — unwrap (inserted/moved-in content stays)
  - <w:del>, <w:moveFrom>    — remove (deleted/moved-out content goes away)
  - <w:delText>, <w:delInstrText> — convert back to <w:t> / <w:instrText>
  - Paragraph mark deletion  — merge paragraph with the following paragraph
  - <w:pPrChange>, <w:rPrChange>, <w:sectPrChange>, <w:tblPrChange>,
    <w:trPrChange>, <w:tcPrChange>, <w:numberingChange>,
    <w:cellIns>, <w:cellDel>, <w:cellMerge>  — strip the change markers,
    keep the current property values

Processes every XML part of the docx that may contain tracked changes:
document.xml, footnotes.xml, endnotes.xml, comments.xml, header*.xml, footer*.xml.

Usage:
    python accept_changes.py input.docx output.docx
"""

import argparse
import re
import sys
import zipfile

from lxml import etree


W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

UNWRAP_TAGS = (f'{W}ins', f'{W}moveTo')
REMOVE_TAGS = (f'{W}del', f'{W}moveFrom')
CHANGE_TRACKING_TAGS = (
    f'{W}pPrChange', f'{W}rPrChange', f'{W}sectPrChange', f'{W}tblPrChange',
    f'{W}trPrChange', f'{W}tcPrChange', f'{W}numberingChange',
    f'{W}cellIns', f'{W}cellDel', f'{W}cellMerge',
)


def _is_paragraph_mark_deletion(del_elem) -> bool:
    """A <w:del/> inside <w:pPr><w:rPr>...</w:rPr></w:pPr> marks the paragraph mark itself as deleted."""
    parent = del_elem.getparent()
    if parent is None or parent.tag != f'{W}rPr':
        return False
    grandparent = parent.getparent()
    return grandparent is not None and grandparent.tag == f'{W}pPr'


def _unwrap(elem) -> None:
    """Replace elem with its children, preserving order."""
    parent = elem.getparent()
    if parent is None:
        return
    idx = parent.index(elem)
    for child in list(elem):
        parent.insert(idx, child)
        idx += 1
    parent.remove(elem)


def _accept_in_xml(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml_bytes, parser)

    # 1) Find paragraphs whose paragraph mark is marked-deleted; remove the marker
    #    and queue the paragraph for merging with the next paragraph.
    paragraphs_to_merge = []
    for del_elem in list(root.iter(f'{W}del')):
        if _is_paragraph_mark_deletion(del_elem):
            p = del_elem
            while p is not None and p.tag != f'{W}p':
                p = p.getparent()
            if p is not None:
                paragraphs_to_merge.append(p)
            del_elem.getparent().remove(del_elem)

    # 2) Merge each marked paragraph into its next paragraph sibling.
    #    Word's behavior: the merged paragraph keeps the *next* paragraph's pPr.
    for p in paragraphs_to_merge:
        parent = p.getparent()
        if parent is None:
            continue
        siblings = list(parent)
        try:
            idx = siblings.index(p)
        except ValueError:
            continue
        next_p = next((s for s in siblings[idx + 1:] if s.tag == f'{W}p'), None)
        if next_p is None:
            continue
        next_pPr = next_p.find(f'{W}pPr')
        insert_at = list(next_p).index(next_pPr) + 1 if next_pPr is not None else 0
        for child in list(p):
            if child.tag == f'{W}pPr':
                continue
            next_p.insert(insert_at, child)
            insert_at += 1
        parent.remove(p)

    # 3) Unwrap insertions and move-tos (kept content).
    for tag in UNWRAP_TAGS:
        for elem in list(root.iter(tag)):
            _unwrap(elem)

    # 4) Remove deletions and move-froms (discarded content).
    for tag in REMOVE_TAGS:
        for elem in list(root.iter(tag)):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    # 5) Defensive: any surviving delText/delInstrText elements (shouldn't happen
    #    after step 4, but normalize them in case) become regular t/instrText.
    for elem in root.iter(f'{W}delText'):
        elem.tag = f'{W}t'
    for elem in root.iter(f'{W}delInstrText'):
        elem.tag = f'{W}instrText'

    # 6) Strip property-change tracking elements. The current properties stay;
    #    only the record of "what they used to be" is removed.
    for tag in CHANGE_TRACKING_TAGS:
        for elem in list(root.iter(tag)):
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)


_HEADER_RE = re.compile(r'^word/header\d*\.xml$')
_FOOTER_RE = re.compile(r'^word/footer\d*\.xml$')
_ALWAYS_PROCESS = {'word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml', 'word/comments.xml'}


def _should_process(name: str) -> bool:
    return name in _ALWAYS_PROCESS or bool(_HEADER_RE.match(name)) or bool(_FOOTER_RE.match(name))


def accept_changes(input_path: str, output_path: str) -> None:
    with zipfile.ZipFile(input_path, 'r') as zin, zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if _should_process(item.filename):
                try:
                    data = _accept_in_xml(data)
                except Exception as e:
                    sys.stderr.write(f'Warning: failed to process {item.filename}: {e}\n')
            zout.writestr(item, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Accept all tracked changes in a DOCX file.')
    parser.add_argument('input_file', help='Input DOCX file with tracked changes')
    parser.add_argument('output_file', help='Output DOCX file (clean, no tracked changes)')
    args = parser.parse_args()
    accept_changes(args.input_file, args.output_file)
    print(f'Successfully accepted all tracked changes: {args.input_file} -> {args.output_file}')
