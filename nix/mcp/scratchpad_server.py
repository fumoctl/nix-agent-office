#!/usr/bin/env python3
"""Declarative Research Scratchpad MCP Server & CLI for AI Agents.

Provides structured, persistent, auditable research scratchpads in `.scratchpad/<session_id>/`
for tracking multi-source evidence from RivalSearchMCP, verifying claims/conflicts, storing
quantitative tables, and exporting structured data for Office document generation (.docx, .pptx, .xlsx, .pdf).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP(
    "ResearchScratchpadMCP",
    instructions=(
        "Structured research scratchpad and evidence ledger for deep research and Office document "
        "generation (.docx, .pptx, .xlsx, .pdf). Use these tools to initialize a research session, "
        "record sources with quality/confidence scores from RivalSearchMCP, log structured data tables "
        "for Excel/PowerPoint charts, verify or resolve conflicting claims, and export research dossiers."
    ),
)


def _scratchpad_root() -> Path:
    root = os.environ.get("SCRATCHPAD_DIR", os.path.join(os.getcwd(), ".scratchpad"))
    path = Path(root).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_id(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw.strip().lower()).strip("-")
    return cleaned or "default-session"


def _session_dir(session_id: str) -> Path:
    sdir = _scratchpad_root() / _sanitize_id(session_id)
    sdir.mkdir(parents=True, exist_ok=True)
    return sdir


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@mcp.tool()
def scratchpad_init_session(
    session_id: str,
    topic: str,
    goal: str = "",
    deliverables: list[str] | None = None,
    sub_questions: list[str] | None = None,
) -> dict[str, Any]:
    """Initialize or update a structured research scratchpad session."""
    sdir = _session_dir(session_id)
    meta_path = sdir / "metadata.json"
    existing = _load_json(meta_path, {})
    meta = {
        "session_id": _sanitize_id(session_id),
        "topic": topic,
        "goal": goal or existing.get("goal", ""),
        "deliverables": deliverables if deliverables is not None else existing.get("deliverables", ["docx", "pptx", "xlsx", "pdf"]),
        "sub_questions": sub_questions if sub_questions is not None else existing.get("sub_questions", []),
        "created_at": existing.get("created_at", _now_iso()),
        "updated_at": _now_iso(),
    }
    _save_json(meta_path, meta)

    for fname, default in [
        ("sources.json", []),
        ("claims.json", []),
        ("tables.json", {}),
    ]:
        fpath = sdir / fname
        if not fpath.exists():
            _save_json(fpath, default)

    notes_path = sdir / "notes.md"
    if not notes_path.exists():
        header = [
            f"# Research Scratchpad: {topic}",
            "",
            f"- **Session ID**: `{meta['session_id']}`",
            f"- **Goal**: {meta['goal'] or 'Comprehensive multi-source research & synthesis'}",
            f"- **Target Deliverables**: {', '.join(meta['deliverables'])}",
            f"- **Initialized**: {meta['created_at']}",
            "",
        ]
        if meta["sub_questions"]:
            header.append("## Research Sub-Questions")
            for idx, q in enumerate(meta["sub_questions"], 1):
                header.append(f"{idx}. [ ] {q}")
            header.append("")
        header.append("## Research Notes")
        header.append("")
        notes_path.write_text("\n".join(header), encoding="utf-8")

    return {
        "status": "initialized",
        "session_id": meta["session_id"],
        "path": str(sdir),
        "metadata": meta,
    }


@mcp.tool()
def scratchpad_write_note(
    session_id: str,
    section: str,
    content: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Append a structured research note under a section in the session's scratchpad."""
    sdir = _session_dir(session_id)
    notes_path = sdir / "notes.md"
    if not notes_path.exists():
        scratchpad_init_session(session_id=session_id, topic=session_id)

    tag_str = f" `[{', '.join(tags)}]`" if tags else ""
    entry = f"\n### {section}{tag_str} ({_now_iso()})\n\n{content.strip()}\n"
    with notes_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    return {
        "status": "recorded",
        "session_id": _sanitize_id(session_id),
        "section": section,
        "notes_path": str(notes_path),
    }


@mcp.tool()
def scratchpad_add_source(
    session_id: str,
    url: str,
    title: str,
    summary: str = "",
    source_type: str = "web",
    quality_score: float | None = None,
    confidence: str = "medium",
    published_date: str = "",
    key_quotes: list[str] | None = None,
) -> dict[str, Any]:
    """Log a verified source (from RivalSearchMCP web/academic/news/social search) into the evidence ledger."""
    sdir = _session_dir(session_id)
    sources_path = sdir / "sources.json"
    sources: list[dict[str, Any]] = _load_json(sources_path, [])

    # Deduplicate by URL
    existing_idx = next((i for i, s in enumerate(sources) if s.get("url") == url), None)
    record = {
        "id": f"S{existing_idx + 1}" if existing_idx is not None else f"S{len(sources) + 1}",
        "url": url,
        "title": title,
        "summary": summary,
        "source_type": source_type,
        "quality_score": quality_score,
        "confidence": confidence,
        "published_date": published_date,
        "key_quotes": key_quotes or [],
        "recorded_at": _now_iso(),
    }
    if existing_idx is not None:
        sources[existing_idx] = record
    else:
        sources.append(record)

    _save_json(sources_path, sources)
    return {
        "status": "saved",
        "source_id": record["id"],
        "total_sources": len(sources),
        "source": record,
    }


@mcp.tool()
def scratchpad_verify_claim(
    session_id: str,
    claim: str,
    status: str = "verified",
    confidence: str = "high",
    supporting_urls: list[str] | None = None,
    conflicting_urls: list[str] | None = None,
    resolution_notes: str = "",
) -> dict[str, Any]:
    """Record a factual claim, its verification status (verified, contested, unverified), and supporting/conflicting URLs."""
    sdir = _session_dir(session_id)
    claims_path = sdir / "claims.json"
    claims: list[dict[str, Any]] = _load_json(claims_path, [])
    record = {
        "id": f"C{len(claims) + 1}",
        "claim": claim,
        "status": status,
        "confidence": confidence,
        "supporting_urls": supporting_urls or [],
        "conflicting_urls": conflicting_urls or [],
        "resolution_notes": resolution_notes,
        "recorded_at": _now_iso(),
    }
    claims.append(record)
    _save_json(claims_path, claims)
    return {
        "status": "saved",
        "claim_id": record["id"],
        "total_claims": len(claims),
        "claim": record,
    }


@mcp.tool()
def scratchpad_record_table(
    session_id: str,
    table_name: str,
    columns: list[str],
    rows: list[list[Any]],
    units: str = "",
    source_citation: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Store a structured quantitative dataset/table in the scratchpad for direct use in .xlsx models, .pptx charts, and .docx tables."""
    sdir = _session_dir(session_id)
    tables_path = sdir / "tables.json"
    tables: dict[str, Any] = _load_json(tables_path, {})
    tables[table_name] = {
        "table_name": table_name,
        "columns": columns,
        "rows": rows,
        "units": units,
        "source_citation": source_citation,
        "notes": notes,
        "updated_at": _now_iso(),
    }
    _save_json(tables_path, tables)
    return {
        "status": "saved",
        "table_name": table_name,
        "row_count": len(rows),
        "column_count": len(columns),
    }


@mcp.tool()
def scratchpad_read(
    session_id: str,
    view: str = "full",
) -> dict[str, Any]:
    """Read back the current state of a research scratchpad session.

    `view` can be one of: "full", "summary", "sources", "claims", "tables", "notes".
    """
    sdir = _session_dir(session_id)
    meta = _load_json(sdir / "metadata.json", {"session_id": _sanitize_id(session_id)})
    sources = _load_json(sdir / "sources.json", [])
    claims = _load_json(sdir / "claims.json", [])
    tables = _load_json(sdir / "tables.json", {})
    notes = (sdir / "notes.md").read_text(encoding="utf-8") if (sdir / "notes.md").exists() else ""

    if view == "sources":
        return {"session_id": meta.get("session_id"), "sources": sources}
    if view == "claims":
        return {"session_id": meta.get("session_id"), "claims": claims}
    if view == "tables":
        return {"session_id": meta.get("session_id"), "tables": tables}
    if view == "notes":
        return {"session_id": meta.get("session_id"), "notes": notes}
    if view == "summary":
        return {
            "session_id": meta.get("session_id"),
            "metadata": meta,
            "counts": {
                "sources": len(sources),
                "claims": len(claims),
                "tables": len(tables),
                "notes_chars": len(notes),
            },
        }
    return {
        "session_id": meta.get("session_id"),
        "metadata": meta,
        "sources": sources,
        "claims": claims,
        "tables": tables,
        "notes": notes,
    }


@mcp.tool()
def scratchpad_list_sessions() -> dict[str, Any]:
    """List all research scratchpad sessions in `.scratchpad/`."""
    root = _scratchpad_root()
    sessions = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            meta = _load_json(child / "metadata.json", {"session_id": child.name})
            sources = _load_json(child / "sources.json", [])
            claims = _load_json(child / "claims.json", [])
            tables = _load_json(child / "tables.json", {})
            sessions.append(
                {
                    "session_id": child.name,
                    "topic": meta.get("topic", child.name),
                    "updated_at": meta.get("updated_at", ""),
                    "sources_count": len(sources),
                    "claims_count": len(claims),
                    "tables_count": len(tables),
                }
            )
    return {"scratchpad_root": str(root), "sessions": sessions}


@mcp.tool()
def scratchpad_export_dossier(
    session_id: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Export the entire scratchpad session (notes, verified claims, structured tables, and bibliography) to a Markdown dossier."""
    data = scratchpad_read(session_id=session_id, view="full")
    sdir = _session_dir(session_id)
    meta = data.get("metadata", {})
    lines = [
        f"# Research Dossier: {meta.get('topic', session_id)}",
        "",
        f"- **Session ID**: `{meta.get('session_id', session_id)}`",
        f"- **Goal**: {meta.get('goal', '')}",
        f"- **Exported At**: {_now_iso()}",
        "",
    ]

    if data.get("claims"):
        lines.extend(["## Verified Claims & Fact-Check Ledger", ""])
        for c in data["claims"]:
            lines.append(
                f"- **[{c['id']}] ({c['status'].upper()} | Confidence: {c['confidence']})**: {c['claim']}"
            )
            if c.get("supporting_urls"):
                lines.append(f"  - Supporting: {', '.join(c['supporting_urls'])}")
            if c.get("conflicting_urls"):
                lines.append(f"  - Conflicting: {', '.join(c['conflicting_urls'])}")
            if c.get("resolution_notes"):
                lines.append(f"  - Resolution: {c['resolution_notes']}")
        lines.append("")

    if data.get("tables"):
        lines.extend(["## Structured Quantitative Tables", ""])
        for tname, t in data["tables"].items():
            lines.append(f"### {tname}" + (f" ({t['units']})" if t.get("units") else ""))
            cols = t.get("columns", [])
            if cols:
                lines.append("| " + " | ".join(str(c) for c in cols) + " |")
                lines.append("| " + " | ".join("---" for _ in cols) + " |")
                for row in t.get("rows", []):
                    lines.append("| " + " | ".join(str(v) for v in row) + " |")
            if t.get("source_citation"):
                lines.append(f"\n*Source: {t['source_citation']}*")
            lines.append("")

    if data.get("notes"):
        lines.extend(["## Detailed Notes", "", data["notes"].strip(), ""])

    if data.get("sources"):
        lines.extend(["## Source Bibliography", ""])
        for s in data["sources"]:
            q = f", Quality: {s['quality_score']}" if s.get("quality_score") is not None else ""
            lines.append(
                f"- **[{s['id']}]** [{s['title']}]({s['url']}) — *{s['source_type']}* (Confidence: {s['confidence']}{q})"
            )
            if s.get("summary"):
                lines.append(f"  - {s['summary']}")
        lines.append("")

    dossier_md = "\n".join(lines)
    target = Path(output_path).resolve() if output_path else (sdir / "dossier.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dossier_md, encoding="utf-8")

    return {
        "status": "exported",
        "session_id": _sanitize_id(session_id),
        "output_path": str(target),
        "bytes": len(dossier_md.encode("utf-8")),
    }


def main_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="scratchpad-cli",
        description="CLI interface to the Research Scratchpad ledger (.scratchpad/)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a research scratchpad session")
    p_init.add_argument("session_id")
    p_init.add_argument("--topic", required=True)
    p_init.add_argument("--goal", default="")
    p_init.add_argument("--deliverables", nargs="*", default=["docx", "pptx", "xlsx", "pdf"])
    p_init.add_argument("--questions", nargs="*", default=[])

    p_note = sub.add_parser("note", help="Append a research note")
    p_note.add_argument("session_id")
    p_note.add_argument("--section", required=True)
    p_note.add_argument("--content", required=True)
    p_note.add_argument("--tags", nargs="*", default=[])

    p_src = sub.add_parser("add-source", help="Add a verified source")
    p_src.add_argument("session_id")
    p_src.add_argument("--url", required=True)
    p_src.add_argument("--title", required=True)
    p_src.add_argument("--summary", default="")
    p_src.add_argument("--type", default="web")
    p_src.add_argument("--quality", type=float, default=None)
    p_src.add_argument("--confidence", default="medium")
    p_src.add_argument("--date", default="")

    p_claim = sub.add_parser("verify-claim", help="Log a verified/contested claim")
    p_claim.add_argument("session_id")
    p_claim.add_argument("--claim", required=True)
    p_claim.add_argument("--status", default="verified")
    p_claim.add_argument("--confidence", default="high")
    p_claim.add_argument("--supporting", nargs="*", default=[])
    p_claim.add_argument("--conflicting", nargs="*", default=[])
    p_claim.add_argument("--notes", default="")

    p_table = sub.add_parser("record-table", help="Record a quantitative table from JSON")
    p_table.add_argument("session_id")
    p_table.add_argument("--name", required=True)
    p_table.add_argument("--columns-json", required=True, help="JSON array of column names")
    p_table.add_argument("--rows-json", required=True, help="JSON array of row arrays")
    p_table.add_argument("--units", default="")
    p_table.add_argument("--source", default="")

    p_read = sub.add_parser("read", help="Read session state")
    p_read.add_argument("session_id")
    p_read.add_argument("--view", default="full", choices=["full", "summary", "sources", "claims", "tables", "notes"])

    sub.add_parser("list", help="List all scratchpad sessions")

    p_export = sub.add_parser("export", help="Export session dossier to Markdown")
    p_export.add_argument("session_id")
    p_export.add_argument("--output", default=None)

    args = parser.parse_args()
    if args.cmd == "init":
        res = scratchpad_init_session(
            session_id=args.session_id,
            topic=args.topic,
            goal=args.goal,
            deliverables=args.deliverables,
            sub_questions=args.questions,
        )
    elif args.cmd == "note":
        res = scratchpad_write_note(
            session_id=args.session_id,
            section=args.section,
            content=args.content,
            tags=args.tags,
        )
    elif args.cmd == "add-source":
        res = scratchpad_add_source(
            session_id=args.session_id,
            url=args.url,
            title=args.title,
            summary=args.summary,
            source_type=args.type,
            quality_score=args.quality,
            confidence=args.confidence,
            published_date=args.date,
        )
    elif args.cmd == "verify-claim":
        res = scratchpad_verify_claim(
            session_id=args.session_id,
            claim=args.claim,
            status=args.status,
            confidence=args.confidence,
            supporting_urls=args.supporting,
            conflicting_urls=args.conflicting,
            resolution_notes=args.notes,
        )
    elif args.cmd == "record-table":
        res = scratchpad_record_table(
            session_id=args.session_id,
            table_name=args.name,
            columns=json.loads(args.columns_json),
            rows=json.loads(args.rows_json),
            units=args.units,
            source_citation=args.source,
        )
    elif args.cmd == "read":
        res = scratchpad_read(session_id=args.session_id, view=args.view)
    elif args.cmd == "list":
        res = scratchpad_list_sessions()
    elif args.cmd == "export":
        res = scratchpad_export_dossier(session_id=args.session_id, output_path=args.output)
    else:
        parser.error(f"Unknown command: {args.cmd}")
        return

    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "mcp":
        main_cli()
    else:
        mcp.run()
