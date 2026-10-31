"""Pack a directory into a DOCX, PPTX, or XLSX file.

Validates with auto-repair, condenses XML formatting, and creates the Office file.

Usage:
    python pack.py <input_directory> <output_file> [--original <file>] [--validate true|false]

Examples:
    python pack.py unpacked/ output.docx --original input.docx
    python pack.py unpacked/ output.pptx --validate false
"""

import argparse
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

import re

import defusedxml.minidom

from validators import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator

# OPC namespaces that must use a default (unprefixed) xmlns — ns#-prefixed → Word/LO reject.
_OPC_DEFAULT_NAMESPACES = {
    "http://schemas.openxmlformats.org/package/2006/content-types",
    "http://schemas.openxmlformats.org/package/2006/relationships",
}

# Canonical OOXML prefixes. ElementTree rewrites w:/r:/etc. to ns0: without register_namespace(); restore them.
_OOXML_NAMESPACE_PREFIXES = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main": "w",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships": "r",
    "http://schemas.openxmlformats.org/drawingml/2006/main": "a",
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing": "wp",
    "http://schemas.openxmlformats.org/drawingml/2006/picture": "pic",
    "http://schemas.openxmlformats.org/markup-compatibility/2006": "mc",
    "http://schemas.openxmlformats.org/officeDocument/2006/math": "m",
    "http://schemas.microsoft.com/office/word/2010/wordprocessingShape": "wps",
    "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup": "wpg",
    "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing": "wp14",
    "http://schemas.microsoft.com/office/word/2010/wordml": "w14",
    "urn:schemas-microsoft-com:vml": "v",
    "urn:schemas-microsoft-com:office:office": "o",
    "http://schemas.openxmlformats.org/presentationml/2006/main": "p",  # pptx packed via this tool
}

def pack(
    input_directory: str,
    output_file: str,
    original_file: str | None = None,
    validate: bool = True,
    infer_author_func=None,
) -> tuple[None, str]:
    input_dir = Path(input_directory)
    output_path = Path(output_file)
    suffix = output_path.suffix.lower()

    if not input_dir.is_dir():
        return None, f"Error: {input_dir} is not a directory"

    if suffix not in {".docx", ".pptx", ".xlsx"}:
        return None, f"Error: {output_file} must be a .docx, .pptx, or .xlsx file"

    if validate:
        original_path = None
        if original_file:
            candidate = Path(original_file)
            if candidate.exists():
                original_path = candidate
            else:
                print(f"Warning: --original {original_file} does not exist; running schema validation only (redlining check requires the original file).", file=sys.stderr)
        else:
            print("Note: --original not provided; running schema validation only (redlining check is skipped without an original to diff against).", file=sys.stderr)

        success, output = _run_validation(
            input_dir, original_path, suffix, infer_author_func
        )
        if output:
            print(output)
        if not success:
            return None, f"Error: Validation failed for {input_dir}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        for pattern in ["*.xml", "*.rels"]:
            for xml_file in temp_content_dir.rglob(pattern):
                _condense_xml(xml_file)
                _normalize_opc_namespaces(xml_file)
                _normalize_ooxml_prefixes(xml_file)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_content_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(temp_content_dir))

    return None, f"Successfully packed {input_dir} to {output_file}"


def _normalize_opc_namespaces(xml_file: Path) -> None:
    """Restore default (unprefixed) xmlns on OPC parts that ElementTree mangled to ns#."""
    try:
        text = xml_file.read_text(encoding="utf-8")
    except Exception:
        return
    changed = False
    for ns_uri in _OPC_DEFAULT_NAMESPACES:
        match = re.search(rf'xmlns:(\w+)="{re.escape(ns_uri)}"', text)
        if match:
            prefix = match.group(1)
            text = re.sub(rf'xmlns:{prefix}="{re.escape(ns_uri)}"', f'xmlns="{ns_uri}"', text)
            text = text.replace(f"<{prefix}:", "<").replace(f"</{prefix}:", "</")
            changed = True
    if changed:
        print(f"Normalized OPC namespaces in {xml_file.name}", file=sys.stderr)
        xml_file.write_text(text, encoding="utf-8")


def _normalize_ooxml_prefixes(xml_file: Path) -> None:
    """Restore canonical OOXML prefixes (w:/r:/a:…) that ElementTree mangled to ns#. Touches only ns# prefixes."""
    try:
        text = xml_file.read_text(encoding="utf-8")
    except Exception:
        return
    changed = False
    for ns_uri, canonical_prefix in _OOXML_NAMESPACE_PREFIXES.items():
        match = re.search(rf'xmlns:(\w+)="{re.escape(ns_uri)}"', text)
        if match:
            current_prefix = match.group(1)
            if current_prefix.startswith("ns") and current_prefix != canonical_prefix:
                text = re.sub(
                    rf'xmlns:{current_prefix}="{re.escape(ns_uri)}"',
                    f'xmlns:{canonical_prefix}="{ns_uri}"',
                    text,
                )
                text = text.replace(f"<{current_prefix}:", f"<{canonical_prefix}:")
                text = text.replace(f"</{current_prefix}:", f"</{canonical_prefix}:")
                text = re.sub(rf'\b{current_prefix}:(\w+)=', rf'{canonical_prefix}:\1=', text)
                changed = True
    if changed:
        print(f"Normalized OOXML prefixes in {xml_file.name}", file=sys.stderr)
        xml_file.write_text(text, encoding="utf-8")


def _run_validation(
    unpacked_dir: Path,
    original_file: Path | None,
    suffix: str,
    infer_author_func=None,
) -> tuple[bool, str | None]:
    output_lines = []
    validators = []

    if suffix == ".docx":
        validators = [DOCXSchemaValidator(unpacked_dir, original_file)]
        # RedliningValidator only fires when we have an original to diff against.
        if original_file is not None:
            author = "Abacus AI Agent"
            if infer_author_func:
                try:
                    author = infer_author_func(unpacked_dir, original_file)
                except ValueError as e:
                    print(f"Warning: {e} Using default author 'Abacus AI Agent'.", file=sys.stderr)
            validators.append(RedliningValidator(unpacked_dir, original_file, author=author))
    elif suffix == ".pptx":
        validators = [PPTXSchemaValidator(unpacked_dir, original_file)]

    if not validators:
        return True, None

    total_repairs = sum(v.repair() for v in validators)
    if total_repairs:
        output_lines.append(f"Auto-repaired {total_repairs} issue(s)")

    success = all(v.validate() for v in validators)

    if success:
        output_lines.append("All validations PASSED!")

    return success, "\n".join(output_lines) if output_lines else None


def _condense_xml(xml_file: Path) -> None:
    try:
        with open(xml_file, encoding="utf-8") as f:
            dom = defusedxml.minidom.parse(f)

        for element in dom.getElementsByTagName("*"):
            if element.tagName.endswith(":t"):
                continue

            for child in list(element.childNodes):
                if (
                    child.nodeType == child.TEXT_NODE
                    and child.nodeValue
                    and child.nodeValue.strip() == ""
                ) or child.nodeType == child.COMMENT_NODE:
                    element.removeChild(child)

        xml_file.write_bytes(dom.toxml(encoding="UTF-8"))
    except Exception as e:
        print(f"ERROR: Failed to parse {xml_file.name}: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pack a directory into a DOCX, PPTX, or XLSX file"
    )
    parser.add_argument("input_directory", help="Unpacked Office document directory")
    parser.add_argument("output_file", help="Output Office file (.docx/.pptx/.xlsx)")
    parser.add_argument(
        "--original",
        help="Original file for validation comparison",
    )
    parser.add_argument(
        "--validate",
        type=lambda x: x.lower() == "true",
        default=True,
        metavar="true|false",
        help="Run validation with auto-repair (default: true)",
    )
    parser.add_argument(
        "--infer-author",
        action="store_true",
        help="When validating with --original, infer the redlining author from the diff "
             "(picks the author whose tracked-change count grew between original and modified). "
             "Without this flag, redlining defaults to author='Abacus AI Agent'.",
    )
    args = parser.parse_args()

    infer_author_func = None
    if args.infer_author:
        from helpers.simplify_redlines import infer_author as infer_author_func  # noqa: F401

    _, message = pack(
        args.input_directory,
        args.output_file,
        original_file=args.original,
        validate=args.validate,
        infer_author_func=infer_author_func,
    )
    print(message)

    if "Error" in message:
        sys.exit(1)
