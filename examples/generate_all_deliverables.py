#!/usr/bin/env python3
"""End-to-End Demo: Research Scratchpad -> Verified .docx, .pptx, .xlsx, and .pdf Deliverables.

Run via:
  ./bin/nix-exec python3 examples/generate_all_deliverables.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "nix" / "mcp"))

import scratchpad_server as sp  # noqa: E402


def main() -> None:
    out_dir = REPO_ROOT / "work" / "example-deliverables"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("1. Initializing Research Scratchpad session...")
    session_id = "declarative-ai-agents-2026"
    sp.scratchpad_init_session(
        session_id=session_id,
        topic="Declarative Nix AI Agent Workflows (2026)",
        goal="Synthesize benchmark data and produce executive .docx, .pptx, .xlsx, and .pdf deliverables.",
        deliverables=["docx", "pptx", "xlsx", "pdf"],
        sub_questions=[
            "How does Nix reproducibility impact agent tool reliability?",
            "What are the verification metrics across Office deliverable formats?",
        ],
    )
    sp.scratchpad_add_source(
        session_id=session_id,
        url="https://nixos.org",
        title="Nix & Declarative Reproducible Builds",
        source_type="web",
        quality_score=0.96,
        confidence="high",
        summary="Cryptographic hashes guarantee identical dependencies across Linux and macOS.",
    )
    sp.scratchpad_verify_claim(
        session_id=session_id,
        claim="Declarative Nix environments eliminate runtime pip/npm version drift across agent executions.",
        status="verified",
        confidence="high",
        supporting_urls=["https://nixos.org"],
    )
    rows = [
        ["2024", 140, 210, 85],
        ["2025", 320, 480, 94],
        ["2026", 690, 950, 99],
    ]
    sp.scratchpad_record_table(
        session_id=session_id,
        table_name="Agent_Deliverable_Benchmarks",
        columns=["Year", "Research_Sessions", "Deliverables_Generated", "QA_Pass_Rate_Pct"],
        rows=rows,
        units="Count / Percentage",
        source_citation="Internal Benchmark Suite (2024-2026)",
    )
    dossier = sp.scratchpad_export_dossier(
        session_id=session_id,
        output_path=str(out_dir / "research_dossier.md"),
    )
    print(f"   -> Exported research dossier: {dossier['output_path']}")

    # 2. Generate & Validate .xlsx
    print("2. Generating and recalculating .xlsx financial/benchmark model...")
    xlsx_path = out_dir / "executive_benchmarks.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Benchmarks"
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E2761", end_color="1E2761", fill_type="solid")
    input_font = Font(name="Arial", size=10, color="0000FF")
    formula_font = Font(name="Arial", size=10, bold=True, color="000000")

    headers = ["Year", "Research Sessions", "Deliverables Generated", "Deliverables per Session"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for r_idx, r in enumerate(rows, start=2):
        c_year = ws.cell(row=r_idx, column=1, value=str(r[0]))
        c_sess = ws.cell(row=r_idx, column=2, value=r[1])
        c_deliv = ws.cell(row=r_idx, column=3, value=r[2])
        c_ratio = ws.cell(row=r_idx, column=4, value=f"=IF(B{r_idx}>0, C{r_idx}/B{r_idx}, 0)")
        c_year.font = Font(name="Arial", size=10)
        c_sess.font = input_font
        c_deliv.font = input_font
        c_ratio.font = formula_font
        c_ratio.number_format = "0.00"

    ws.cell(row=5, column=1, value="Total").font = formula_font
    ws.cell(row=5, column=2, value="=SUM(B2:B4)").font = formula_font
    ws.cell(row=5, column=3, value="=SUM(C2:C4)").font = formula_font
    ws.cell(row=5, column=4, value="=IF(B5>0, C5/B5, 0)").font = formula_font
    ws.cell(row=5, column=4).number_format = "0.00"
    wb.save(xlsx_path)

    recalc_out = subprocess.check_output(
        [sys.executable, str(REPO_ROOT / ".agents/skills/xlsx/scripts/recalc.py"), str(xlsx_path)],
        text=True,
    )
    recalc_data = json.loads(recalc_out)
    assert recalc_data.get("status") == "success" and recalc_data.get("total_errors") == 0, recalc_out
    print(f"   -> Verified .xlsx ({recalc_data['total_formulas']} formulas, 0 errors): {xlsx_path}")

    # 3. Generate & Validate .docx
    print("3. Generating and validating .docx executive report...")
    docx_path = out_dir / "executive_report.docx"
    docx_js = f"""
      const fs = require('fs');
      const {{ Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType }} = require('docx');
      const doc = new Document({{
        sections: [{{
          properties: {{ page: {{ size: {{ width: 12240, height: 15840 }} }} }},
          children: [
            new Paragraph({{ text: 'Declarative Nix AI Agent Workflows (2026)', heading: HeadingLevel.HEADING_1 }}),
            new Paragraph({{ children: [new TextRun({{ text: 'Executive Summary: ', bold: true }}), new TextRun('All research tools, MCP servers, and Office document pipelines run reproducibly via Nix.')] }}),
            new Table({{
              columnWidths: [3000, 3000, 3000],
              rows: [
                new TableRow({{
                  children: ['Year', 'Sessions', 'Deliverables'].map(label => new TableCell({{
                    width: {{ size: 3000, type: WidthType.DXA }},
                    shading: {{ type: ShadingType.CLEAR, fill: '1E2761' }},
                    children: [new Paragraph({{ children: [new TextRun({{ text: label, bold: true, color: 'FFFFFF' }})] }})]
                  }}))
                }}),
                ...{json.dumps([[str(r[0]), str(r[1]), str(r[2])] for r in rows])}.map(row => new TableRow({{
                  children: row.map(val => new TableCell({{
                    width: {{ size: 3000, type: WidthType.DXA }},
                    children: [new Paragraph(val)]
                  }}))
                }}))
              ]
            }})
          ]
        }}]
      }});
      Packer.toBuffer(doc).then(buf => fs.writeFileSync({json.dumps(str(docx_path))}, buf));
    """
    subprocess.run(["node", "-e", docx_js], check=True)
    subprocess.run(
        [sys.executable, str(REPO_ROOT / ".agents/skills/docx/scripts/office/validate.py"), str(docx_path)],
        check=True,
    )
    print(f"   -> Verified .docx: {docx_path}")

    # 4. Generate & Validate .pptx
    print("4. Generating and validating .pptx executive slide deck...")
    pptx_path = out_dir / "executive_deck.pptx"
    pptx_js = f"""
      const pptxgen = require('pptxgenjs');
      const pres = new pptxgen();
      pres.layout = 'LAYOUT_16x9';

      const slide1 = pres.addSlide();
      slide1.background = {{ color: '1E2761' }};
      slide1.addText('Declarative Nix AI Research Suite', {{
        x: 0.8, y: 1.8, w: 8.4, h: 1.2, fontSize: 38, fontFace: 'Cambria', bold: true, color: 'FFFFFF', margin: 0
      }});
      slide1.addText('RivalSearchMCP + Research Scratchpad + Anthropic Office Skills', {{
        x: 0.8, y: 3.1, w: 8.4, h: 0.8, fontSize: 18, fontFace: 'Calibri', color: 'CADCFC', margin: 0
      }});

      const slide2 = pres.addSlide();
      slide2.addText('Deliverable Growth (2024–2026)', {{
        x: 0.6, y: 0.4, w: 8.8, h: 0.7, fontSize: 28, fontFace: 'Cambria', bold: true, color: '1E2761', margin: 0
      }});
      slide2.addChart(pres.ChartType.bar, [{{
        name: 'Deliverables Generated',
        labels: ['2024', '2025', '2026'],
        values: [210, 480, 950]
      }}], {{
        x: 0.8, y: 1.3, w: 8.4, h: 3.8,
        showTitle: true, title: 'Verified Office Deliverables per Year',
        showValue: true, dataLabelPosition: 'outEnd',
        chartColors: ['028090'],
        catGridLine: {{ style: 'none' }},
        showLegend: false
      }});

      pres.writeFile({{ fileName: {json.dumps(str(pptx_path))} }});
    """
    subprocess.run(["node", "-e", pptx_js], check=True)
    subprocess.run(
        [sys.executable, str(REPO_ROOT / ".agents/skills/pptx/scripts/office/validate.py"), str(pptx_path)],
        check=True,
    )
    print(f"   -> Verified .pptx: {pptx_path}")

    # 5. Generate .pdf
    print("5. Generating .pdf executive brief...")
    pdf_path = out_dir / "executive_brief.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    story = [
        Paragraph("Declarative Nix AI Agent Research Brief", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            "Generated with ReportLab inside a 100% declarative Nix flake environment.",
            styles["Normal"],
        ),
        Spacer(1, 16),
    ]
    tbl_data = [["Year", "Research Sessions", "Deliverables", "QA Pass Rate (%)"]] + [
        [str(c) for c in r] for r in rows
    ]
    tbl = Table(tbl_data, colWidths=[100, 130, 130, 120])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E2761")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(tbl)
    doc.build(story)
    print(f"   -> Generated .pdf: {pdf_path}")
    print("\nAll 4 Office/PDF deliverables + Markdown dossier generated and verified in work/example-deliverables/!")


if __name__ == "__main__":
    main()
