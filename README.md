# Declarative Nix AI Research & Office Suite

A **100% declarative Nix Flake repository** that equips AI coding & research agents (Antigravity, Claude Code, and MCP clients) with:

1. **Deep Multi-Source Research (`RivalSearchMCP`)**:
   - Both the remote Streamable HTTP endpoint (`https://RivalSearchMCP.fastmcp.app/mcp`) and a **100% local Nix-packaged stdio server (`nix run .#rivalsearch-mcp`)** + CLI (`rival-search`).
   - 9 keyless tools spanning 5-engine web search (DuckDuckGo, Bing, Yahoo, Mojeek, Wikipedia), 9-platform social search (Reddit, Hacker News, Stack Overflow, Dev.to, Medium, Product Hunt, Bluesky, Lobste.rs, Lemmy), 5-source news aggregation, 5 academic paper & dataset databases (OpenAlex, CrossRef, arXiv, PubMed, Europe PMC, Kaggle, HuggingFace, Zenodo, Dataverse), GitHub repo search, site mapping, content conflict detection, and PDF/DOCX analysis.
2. **Official Anthropic Office & PDF Skills (`.docx`, `.pptx`, `.xlsx`, `.pdf`, `doc-coauthoring`)**:
   - Pinned from [`anthropics/skills`](https://github.com/anthropics/skills) (`ca45fc496a3436251f191354091d557da31c15b5`) with every single runtime dependency pre-built by Nix:
     - **Node.js (`NODE_PATH`)**: `docx`, `pptxgenjs`, `pdf-lib`, `pdfjs-dist`, `react`, `react-dom`, `react-icons`, `sharp` (with `autoPatchelfHook` native library patching on Linux).
     - **Python 3**: `openpyxl`, `pandas`, `numpy`, `defusedxml`, `lxml`, `Pillow`, `pypdf`, `pdfplumber`, `reportlab`, `pdf2image`, `pytesseract`, `pypdfium2`, `markitdown`, `python-pptx`, `python-docx`.
     - **System & Verification Tools**: Headless `libreoffice` (`soffice`), `pandoc`, `poppler-utils` (`pdftoppm`, `pdftotext`, `pdfimages`), `qpdf`, `pdftk`, `tesseract`, plus metric-compatible Office fonts (`Liberation`, `Carlito`, `Caladea`, `DejaVu`) wired via `FONTCONFIG_FILE`.
3. **Structured Research Scratchpad & Reasoning MCP Servers**:
   - **`scratchpad-mcp` (`nix run .#scratchpad-mcp` & `scratchpad-cli`)**: Custom FastMCP server and CLI that maintains an auditable evidence ledger in `.scratchpad/<session_id>/` (verified sources with quality/confidence scores, fact-checked claims, structured quantitative tables, and Markdown research dossiers).
   - **Bundled Nixpkgs MCP Servers**: `mcp-server-sequential-thinking`, `mcp-server-memory`, `markitdown-mcp`, and `mcp-server-fetch`.

---

## Quick Start (Works Anywhere Nix is Installed)

### 1. Run the Full Self-Test & Deliverable Verification Suite
```bash
nix run .#verify-env
```
This single command builds the declarative environment and verifies:
- All CLI binaries, Python libraries, and Node.js packages (`docx`, `pptxgenjs`, `pdf-lib`, `sharp`, `react-icons`).
- The Research Scratchpad engine (`scratchpad-cli`).
- End-to-end generation and validation of `.docx` (XSD validation), `.pptx` (OOXML validation), `.xlsx` (LibreOffice headless formula recalculation via `recalc.py`), and `.pdf` (ReportLab + Poppler `pdftoppm`).

### 2. Enter the Declarative Development Shell
```bash
nix develop
```
Or execute any single command inside the declarative environment from outside `nix develop`:
```bash
./bin/nix-exec python3 examples/generate_all_deliverables.py
```

### 3. Run Individual Nix Flake Apps
| Command | Description |
| :--- | :--- |
| `nix run .#verify-env` | Run end-to-end verification of all tools, MCP servers, and `.docx`/`.pptx`/`.xlsx`/`.pdf` pipelines |
| `nix run .#rivalsearch-mcp` | Start the local pure-Nix `RivalSearchMCP` server over stdio |
| `nix run .#rival-search -- --help` | Run the `RivalSearchMCP` CLI (`call-tool web_search`, `research_topic`, etc.) |
| `nix run .#scratchpad-mcp` | Start the `ResearchScratchpadMCP` server over stdio |
| `nix run .#scratchpad-cli -- --help` | Manage `.scratchpad/<session_id>/` research sessions from the terminal |
| `nix run .#sequential-thinking-mcp` | Start `mcp-server-sequential-thinking` |
| `nix run .#memory-mcp` | Start `mcp-server-memory` |
| `nix run .#markitdown-mcp` | Start `markitdown-mcp` |
| `nix run .#nixos-mcp` | Start `mcp-nixos` to search 130,000+ Nixpkgs packages for OSS builds |
| `nix run .#oss-fhs` | Enter a Linux FHS sandbox (`buildFHSEnv`) for building/testing external OSS repos |
| `nix develop .#oss-polyglot` | Enter the polyglot OSS build/test shell (Rust, Go, Python, Node/pnpm/yarn, C/C++) |
| `./bin/nix-oss-sandbox --help` | Run OSS repo builds & test suites in `work/repos/` with caches isolated in `work/.cache/` |

---

## Repository Structure

```text
.
├── flake.nix                                      # 100% declarative Nix Flake (packages, apps, devShells)
├── flake.lock                                     # Pinned Nix flake lockfile
├── AGENTS.md / GEMINI.md                          # Agent instructions & mandatory QA gates
├── .mcp.json                                      # Project-level MCP configuration
├── bin/
│   └── nix-exec                                   # Wrapper to run any command inside the Nix environment
├── nix/
│   ├── mcp/
│   │   └── scratchpad_server.py                   # FastMCP server & CLI for .scratchpad/ research ledgers
│   └── node/
│       ├── package.json                           # Declarative Node dependencies (docx, pptxgenjs, pdf-lib, sharp, react-icons)
│       └── package-lock.json                      # Pinned npm lockfile built via pkgs.importNpmLock
├── examples/
│   └── generate_all_deliverables.py               # End-to-end demo generating verified .docx, .pptx, .xlsx, .pdf in work/
├── work/                                          # Gitignored agent working directory for deliverables, scripts, QA & .scratchpad/
└── .agents/
    ├── skills.json                                # Antigravity skill registry
    ├── plugins.json                               # Antigravity plugin registry
    ├── plugins/
    │   └── research-office-suite/                 # Bundled plugin with mcp_config.json & rules
    └── skills/
        ├── docx/                                  # Official Anthropic Word (.docx) skill + XSD validator
        ├── building-technical-docx-reports/       # HTML -> Styled Technical Report .docx pipeline + real TOC page numbering
        ├── docx-expert/                           # python-docx & docxtpl Jinja2 template workflow + generators
        ├── pptx/                                  # Official Anthropic PowerPoint (.pptx) skill + OOXML validator
        ├── xlsx/                                  # Official Anthropic Excel (.xlsx) skill + LibreOffice recalc.py
        ├── pdf/                                   # Official Anthropic PDF skill + form/table utilities
        ├── doc-coauthoring/                       # Official Anthropic structured doc co-authoring skill
        ├── rival-search-mcp/                      # Official RivalSearchMCP deep research skill & CLI
        ├── research-scratchpad/                   # Structured evidence & quantitative table scratchpad skill
        └── deep-research-deliverables/            # End-to-end research-to-Office orchestration skill
```
