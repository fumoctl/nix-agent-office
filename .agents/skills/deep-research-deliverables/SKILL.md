---
name: deep-research-deliverables
description: "End-to-end workflow for conducting multi-source deep research with RivalSearchMCP, staging verified evidence and tables in the Research Scratchpad, and generating verified executive Office deliverables (.docx Word reports, .pptx PowerPoint slide decks, .xlsx Excel financial/data models, and .pdf documents) in a 100% declarative Nix environment."
---

# Deep Research to Office Deliverables Workflow

Use this skill whenever the user asks you to research a topic and produce one or more Office or PDF deliverables (`.docx`, `.pptx`, `.xlsx`, `.pdf`).

## Architecture Overview

```text
[1. RivalSearchMCP]  ──(web / academic / news / social / GitHub / PDF OCR)──►
[2. Research Scratchpad (.scratchpad/<session>)]  ──(verified claims, sources, tables)──►
[3. Anthropic Office & PDF Skills]
    ├── .docx (Node `docx` + LibreOffice/Poppler visual QA + XSD validate.py)
    ├── .pptx (Node `pptxgenjs` + `validate.py` + LibreOffice/Poppler slide QA)
    ├── .xlsx (Python `openpyxl` + live formulas + LibreOffice `recalc.py`)
    └── .pdf  (Python `reportlab`/`pypdf`/`pdfplumber` + `pdftoppm` visual QA)
```

## Step-by-Step Procedure

### Phase 1: Plan & Initialize Scratchpad
1. Activate the **`research-scratchpad`** skill and initialize a session (`scratchpad_init_session` or `scratchpad-cli init <session_id>`).
2. If you have access to the `sequential-thinking` MCP server, use it to break down complex analytical dimensions before searching.

### Phase 2: Deep Research via `rivalsearch`
1. **Broad Discovery**: Use `research_topic(mode="topic" | "entity")` or fan out across `web_search`, `scientific_research`, `news_aggregation`, `social_search`, and `github_search`.
2. **Deep Reading**: Retrieve primary sources with `content_operations(operation="retrieve")` and analyze linked PDFs/DOCXs with `document_analysis`.
3. **Trust & Conflict Calibration**:
   - Check source trustworthiness with `content_operations(operation="score", urls=[...])`.
   - Resolve numeric or factual discrepancies across sources with `content_operations(operation="find_conflicts", urls=[...])`.
4. **Ledger Recording**:
   - Record every cited source via `scratchpad_add_source`.
   - Record every quantitative dataset via `scratchpad_record_table`.
   - Record verified claims via `scratchpad_verify_claim`.

### Phase 3: Deliverable Generation & Mandatory QA Gates

Read the corresponding official Anthropic skill (`docx`, `pptx`, `xlsx`, `pdf`) before generating each file, and run its required verification pipeline:

1. **Word Documents (`.docx`) — read [`.agents/skills/docx/SKILL.md`](../docx/SKILL.md)**:
   - Generate via Node.js `require('docx')` (preinstalled in `NODE_PATH` by Nix).
   - Validate XML schema: `python3 .agents/skills/docx/scripts/office/validate.py output.docx`
   - Visual QA:
     ```bash
     python3 .agents/skills/docx/scripts/office/soffice.py --headless --convert-to pdf output.docx
     pdftoppm -jpeg -r 100 output.pdf docx-page
     ```

2. **PowerPoint Presentations (`.pptx`) — read [`.agents/skills/pptx/SKILL.md`](../pptx/SKILL.md)**:
   - Generate via Node.js `require('pptxgenjs')` (with `react-icons` + `sharp` for crisp icon graphics, preinstalled in `NODE_PATH` by Nix).
   - Validate OOXML & chart integrity: `python3 .agents/skills/pptx/scripts/office/validate.py output.pptx`
   - Content & Visual QA:
     ```bash
     markitdown output.pptx
     python3 .agents/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf output.pptx
     pdftoppm -jpeg -r 150 output.pdf slide
     ```

3. **Excel Spreadsheets (`.xlsx`) — read [`.agents/skills/xlsx/SKILL.md`](../xlsx/SKILL.md)**:
   - Generate via Python `openpyxl` using dynamic Excel formulas (`=SUM(...)`, `=INDEX(...)`, etc.), never hardcoded calculated outputs, and cite sources from `.scratchpad/<session_id>/sources.json`.
   - **Mandatory Recalculation & Error Check**:
     ```bash
     python3 .agents/skills/xlsx/scripts/recalc.py output.xlsx
     ```
     Verify `"status": "success"` and `"total_errors": 0`.

4. **PDF Reports & Forms (`.pdf`) — read [`.agents/skills/pdf/SKILL.md`](../pdf/SKILL.md)**:
   - Generate via Python `reportlab` or `pypdf` / Node `pdf-lib`.
   - Render pages with `pdftoppm -png -r 150 output.pdf pdf-page` and inspect visually for layout or glyph issues.
