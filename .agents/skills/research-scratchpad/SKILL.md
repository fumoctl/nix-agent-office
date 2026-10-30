---
name: research-scratchpad
description: "Structured, auditable research scratchpad and evidence ledger (.scratchpad/<session_id>/) for multi-step deep research, source quality tracking, claim verification, conflict resolution, and quantitative table staging before generating Office deliverables (.docx, .pptx, .xlsx, .pdf). Activate whenever conducting multi-source research, synthesizing findings, or preparing structured data for documents."
---

# Research Scratchpad Skill

When conducting deep research or preparing deliverables (`.docx`, `.pptx`, `.xlsx`, `.pdf`), never rely solely on ephemeral conversation context. Maintain an auditable, persistent research ledger in `.scratchpad/<session_id>/` using either the **`scratchpad` MCP server** tools or the **`scratchpad-cli`** utility.

## Available Interfaces

### 1. MCP Tools (`scratchpad` MCP Server)
- `scratchpad_init_session(session_id, topic, goal, deliverables, sub_questions)`
- `scratchpad_write_note(session_id, section, content, tags)`
- `scratchpad_add_source(session_id, url, title, summary, source_type, quality_score, confidence, published_date, key_quotes)`
- `scratchpad_verify_claim(session_id, claim, status, confidence, supporting_urls, conflicting_urls, resolution_notes)`
- `scratchpad_record_table(session_id, table_name, columns, rows, units, source_citation, notes)`
- `scratchpad_read(session_id, view="full|summary|sources|claims|tables|notes")`
- `scratchpad_list_sessions()`
- `scratchpad_export_dossier(session_id, output_path)`

### 2. CLI Utility (`scratchpad-cli` or `scripts/scratchpad_cli.py`)
```bash
# Initialize a research session
python3 .agents/skills/research-scratchpad/scripts/scratchpad_cli.py init market-2026 \
  --topic "AI Agent Infrastructure 2026" \
  --goal "Produce executive report (.docx), board deck (.pptx), and financial model (.xlsx)" \
  --deliverables docx pptx xlsx pdf \
  --questions "What is the TAM growth rate?" "Who are the top 5 vendors?"

# Log a verified source from RivalSearchMCP
python3 .agents/skills/research-scratchpad/scripts/scratchpad_cli.py add-source market-2026 \
  --url "https://arxiv.org/abs/2501.00001" \
  --title "Enterprise Agent Benchmarks" \
  --type academic \
  --quality 0.92 \
  --confidence high \
  --summary "Benchmarks 14 agent architectures across 500 enterprise workflows."

# Record a quantitative dataset for .xlsx and .pptx charts
python3 .agents/skills/research-scratchpad/scripts/scratchpad_cli.py record-table market-2026 \
  --name "Market_Size_Projection" \
  --columns-json '["Year", "Enterprise_Spend_USD_M", "YoY_Growth"]' \
  --rows-json '[["2024", 4200, 0.45], ["2025", 6800, 0.619], ["2026", 11200, 0.647]]' \
  --units "USD Millions" \
  --source "Gartner / OpenAlex Synthesis (2026)"

# Log claim verification after running RivalSearchMCP find_conflicts
python3 .agents/skills/research-scratchpad/scripts/scratchpad_cli.py verify-claim market-2026 \
  --claim "Enterprise adoption grew >60% YoY in 2025-2026" \
  --status verified \
  --confidence high \
  --supporting "https://arxiv.org/abs/2501.00001"

# Export full Markdown dossier
python3 .agents/skills/research-scratchpad/scripts/scratchpad_cli.py export market-2026
```

## Standard Deep-Research Workflow

1. **Decompose & Initialize**: Call `scratchpad_init_session` with 4–8 concrete sub-questions and the target deliverables (`docx`, `pptx`, `xlsx`, `pdf`).
2. **Multi-Source Fan-Out (`rivalsearch`)**:
   - Run `web_search`, `scientific_research`, `news_aggregation`, `social_search`, `github_search`, or `research_topic`.
   - Weight findings by RivalSearchMCP's per-item `quality` block and aggregate `confidence` signal.
3. **Retrieve & Cross-Check**:
   - Fetch full text of top sources via `content_operations(operation="retrieve")` or `document_analysis` for PDFs.
   - When numbers or dates disagree across sources, run `content_operations(operation="find_conflicts")` and record the resolution via `scratchpad_verify_claim`.
4. **Stage Quantitative Data**:
   - Every table destined for an `.xlsx` sheet, `.pptx` native chart, or `.docx` table should be saved with `scratchpad_record_table` including exact units and source citations.
5. **Synthesize & Export Dossier**:
   - Call `scratchpad_export_dossier` to produce `.scratchpad/<session_id>/dossier.md`, then pass the structured JSON/Markdown directly into your `.docx`, `.pptx`, `.xlsx`, and `.pdf` generator scripts.
