# Declarative Nix Deep-Research & Office Document Workspace

This repository provides a **100% declarative Nix environment** for AI agents (Antigravity, Claude Code, and MCP-compatible agents) to perform multi-source deep research and generate verified Office & PDF documents (`.docx`, `.pptx`, `.xlsx`, `.pdf`) with zero external non-Nix dependencies.

---

## 1. Nix Execution & Workspace Directory Rules (CRITICAL)

- **Use `work/` for all agent activity**: Place all generated deliverables (`.docx`, `.pptx`, `.xlsx`, `.pdf`), temporary generator scripts (`.py`, `.js`), unpacked OOXML folders, visual QA page renders (`*.jpg`, `*.png`), and research scratchpads (`work/.scratchpad/`) inside the [`work/`](./work) directory (or a task-specific subdirectory like `work/<task-name>/`). Everything inside `work/` (except `work/.gitkeep`) is gitignored so the Nix Flake Git tree stays clean.
- **Never run `pip install`, `npm install`, `uv run`, or `apt-get`**. Every Python library, Node.js library, system binary, font, and MCP server is declaratively built and pinned in [`flake.nix`](./flake.nix).
- If your shell is not already inside `nix develop` (check if `command -v scratchpad-cli` or `$NODE_PATH` is set), prefix shell commands with `./bin/nix-exec <command>` or `nix develop -c <command>`:
  ```bash
  ./bin/nix-exec python3 script.py
  ./bin/nix-exec node generate_deck.js
  ```
- **Adding Packages On the Fly (100% Declarative)**:
  - **Ephemeral (per-command)**: Pass `--pkgs` (for Nixpkgs binaries) or `--py` (for `python3Packages`) to `./bin/nix-exec`:
    ```bash
    ./bin/nix-exec --pkgs "graphviz imagemagick" --py "matplotlib scipy" -- python3 work/plot.py
    ```
  - **Persistent (repo-wide)**: Use `./bin/nix-add-pkg` (which validates the package in `nixpkgs` and records it in [`nix/extra-packages.nix`](./nix/extra-packages.nix) or [`nix/node/package.json`](./nix/node/package.json)):
    ```bash
    ./bin/nix-add-pkg --system graphviz
    ./bin/nix-add-pkg --python matplotlib
    ./bin/nix-add-pkg --oss protobuf
    ./bin/nix-add-pkg --node chart.js
    ```
- Inside `nix develop` (or via `./bin/nix-exec`), `NODE_PATH` is pre-populated with:
  - `docx` (Word `.docx` generation)
  - `pptxgenjs` (PowerPoint `.pptx` generation)
  - `pdf-lib` & `pdfjs-dist` (PDF creation & inspection)
  - `react`, `react-dom`, `react-icons`, `sharp` (SVG icon rendering to PNG for presentations/reports)
- Inside `nix develop` (or via `./bin/nix-exec`), `python3` has pre-installed:
  - `openpyxl`, `pandas`, `numpy`, `defusedxml`, `lxml`, `Pillow`, `pypdf`, `pdfplumber`, `reportlab`, `pdf2image`, `pytesseract`, `pypdfium2`, `markitdown`, `python-pptx`, `python-docx`, `fastmcp`, `mcp`, `scrapling`, `rival_search_mcp`.

---

## 2. Installed Skills (`.agents/skills/`)

Always read the corresponding `SKILL.md` before starting a research or document task:

| Skill | Path | Purpose |
| :--- | :--- | :--- |
| **`deep-research-deliverables`** | [`.agents/skills/deep-research-deliverables/SKILL.md`](./.agents/skills/deep-research-deliverables/SKILL.md) | End-to-end orchestration from RivalSearchMCP → Scratchpad → Office deliverables |
| **`oss-build-test`** | [`.agents/skills/oss-build-test/SKILL.md`](./.agents/skills/oss-build-test/SKILL.md) | Clone, build, test & benchmark OSS repos in `work/repos/` via `./bin/nix-oss-sandbox` |
| **`research-scratchpad`** | [`.agents/skills/research-scratchpad/SKILL.md`](./.agents/skills/research-scratchpad/SKILL.md) | Structured evidence ledger, table staging, and claim verification in `.scratchpad/` |
| **`rival-search-mcp`** | [`.agents/skills/rival-search-mcp/SKILL.md`](./.agents/skills/rival-search-mcp/SKILL.md) | 9 keyless research tools across web, academic, social, news, GitHub, and PDFs |
| **`docx`** | [`.agents/skills/docx/SKILL.md`](./.agents/skills/docx/SKILL.md) | Official Anthropic Word (`.docx` / `.dotx`) creation, redlining, comments & QA |
| **`pptx`** | [`.agents/skills/pptx/SKILL.md`](./.agents/skills/pptx/SKILL.md) | Official Anthropic PowerPoint (`.pptx` / `.potx`) creation, templates, design & QA |
| **`xlsx`** | [`.agents/skills/xlsx/SKILL.md`](./.agents/skills/xlsx/SKILL.md) | Official Anthropic Excel (`.xlsx` / `.xlsm`) financial modeling & LibreOffice `recalc.py` |
| **`pdf`** | [`.agents/skills/pdf/SKILL.md`](./.agents/skills/pdf/SKILL.md) | Official Anthropic PDF creation, table extraction, OCR, form filling & inspection |
| **`doc-coauthoring`** | [`.agents/skills/doc-coauthoring/SKILL.md`](./.agents/skills/doc-coauthoring/SKILL.md) | Official Anthropic structured collaborative document co-authoring workflow |

---

## 3. Configured MCP Servers

Configured in [`.agents/plugins/research-office-suite/mcp_config.json`](./.agents/plugins/research-office-suite/mcp_config.json) and [`.mcp.json`](./.mcp.json):

- **`rivalsearch`**: Remote Streamable HTTP endpoint (`https://RivalSearchMCP.fastmcp.app/mcp`) providing `web_search`, `social_search`, `news_aggregation`, `github_search`, `scientific_research`, `map_website`, `content_operations`, `research_topic`, and `document_analysis`.
- **`rivalsearch-local`**: Local pure-Nix stdio server (`nix run .#rivalsearch-mcp`) running `RivalSearchMCP` locally without any external cloud dependency.
- **`scratchpad`**: Local pure-Nix stdio server (`nix run .#scratchpad-mcp`) managing `.scratchpad/<session_id>/` (sources, claims, quantitative tables, notes, and Markdown dossiers).
- **`sequential-thinking`**: Nixpkgs `mcp-server-sequential-thinking` for structured multi-step decomposition.
- **`memory`**: Nixpkgs `mcp-server-memory` for persistent knowledge graph tracking.
- **`markitdown`**: Nixpkgs `markitdown-mcp` for converting arbitrary office/PDF files to Markdown.
- **`fetch`**: Nixpkgs `mcp-server-fetch` for direct URL fetching.
- **`nixos`**: Nixpkgs `mcp-nixos` for searching 130,000+ Nixpkgs packages & options when building/testing external OSS repositories.

---

## 4. Mandatory Quality Assurance Gates for Deliverables

Never deliver an Office or PDF document without running its verification pipeline:

1. **`.docx` files**:
   - Validate schema: `./bin/nix-exec python3 .agents/skills/docx/scripts/office/validate.py <file.docx>`
   - Visual QA: `./bin/nix-exec python3 .agents/skills/docx/scripts/office/soffice.py --headless --convert-to pdf <file.docx>` followed by `./bin/nix-exec pdftoppm -jpeg -r 100 <file.pdf> page`
2. **`.pptx` files**:
   - Validate schema & charts: `./bin/nix-exec python3 .agents/skills/pptx/scripts/office/validate.py <file.pptx>`
   - Visual QA: `./bin/nix-exec python3 .agents/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf <file.pptx>` followed by `./bin/nix-exec pdftoppm -jpeg -r 150 <file.pdf> slide`
3. **`.xlsx` files**:
   - Recalculate all formulas via LibreOffice: `./bin/nix-exec python3 .agents/skills/xlsx/scripts/recalc.py <file.xlsx>`
   - Confirm JSON output reports `"status": "success"` and `"total_errors": 0`.
4. **`.pdf` files**:
   - Render pages via `./bin/nix-exec pdftoppm -png -r 150 <file.pdf> page` and visually inspect for layout/font issues.
