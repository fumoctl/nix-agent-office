---
name: rival-search-mcp
description: "Deterministic deep research via RivalSearchMCP. 9 tools: 5-engine web search (DuckDuckGo/Bing/Yahoo/Mojeek/Wikipedia), 9-platform social search (Reddit/HN/StackOverflow/Dev.to/Medium/ProductHunt/Bluesky/Lobste.rs/Lemmy), 5-source news (Google/Bing/Guardian/GDELT/DDG), 5 academic DBs (OpenAlex/CrossRef/arXiv/PubMed/EuropePMC), GitHub search, website mapping, content extraction with OCR, and research topic synthesis. No API keys required. Use when the user needs web research, competitive analysis, content discovery, or academic paper search."
---

# RivalSearchMCP

You have access to 9 deterministic research tools via:
1. **Native MCP Server (`rivalsearch` / `rivalsearch-local`)**: Call the MCP tools directly (`web_search`, `social_search`, `news_aggregation`, `github_search`, `map_website`, `content_operations`, `document_analysis`, `research_topic`, `scientific_research`).
2. **Nix CLI (`rival-search` or `python3 scripts/cli.py`)**: Provided declaratively by the Nix environment (`nix develop` or `nix run .#rival-search --`). No `uv` or runtime `pip` installs are needed.

Every tool returns deterministic, auditable output annotated with per-item `quality` scores and an aggregate `confidence` signal (`high` / `medium` / `low`). There is no in-server LLM — you perform the synthesis.

## How to invoke tools via CLI (when not calling MCP tools directly)

```bash
# Inside nix develop:
rival-search call-tool <tool_name> --flag value
# Or via python3 directly:
python3 .agents/skills/rival-search-mcp/scripts/cli.py call-tool <tool_name> --flag value
# Or from anywhere with Nix installed:
nix run .#rival-search -- call-tool <tool_name> --flag value
```

## Available tools

- `web_search` — concurrent search across DuckDuckGo, Bing, Yahoo, Mojeek, Wikipedia. Use for general web queries.
- `social_search` — Reddit, Hacker News, Stack Overflow, Dev.to, Medium, Product Hunt, Bluesky, Lobste.rs, Lemmy. Use for community discussions.
- `news_aggregation` — Google News, Bing News, The Guardian, GDELT, DuckDuckGo News. Use for current events. Accepts `--time-range day|week|month|anytime`.
- `github_search` — search public GitHub repos. Use for code, libraries, projects.
- `map_website` — crawl a site in `research` / `docs` / `map` mode. Use to explore site structure or documentation.
- `content_operations` — one tool, six ops (`retrieve`, `stream`, `analyze`, `extract`, `score`, `find_conflicts`). Use to get full page content, rate source quality, or surface disagreements between sources.
- `document_analysis` — extract text from PDFs, Word docs, images. Use for document processing.
- `research_topic` — end-to-end research workflow (`mode="topic"` or `mode="entity"`), combining search, content retrieval, and cross-source synthesis.
- `scientific_research` — OpenAlex, CrossRef, arXiv, PubMed, Europe PMC (papers) + Kaggle, HuggingFace, Dataverse, Zenodo (datasets).

## When to chain tools

- Found a URL from search? → `content_operations --operation retrieve --url <url>`
- Want to assess source trust before using results? → `content_operations --operation score --urls '[…]'`
- Two sources seem to disagree? → `content_operations --operation find_conflicts --urls '[…]'`
- Found a PDF link? → `document_analysis --url <url>`
- Need to explore a website? → `map_website --url <url> --mode docs`
- Need a unified entity profile in one shot? → `research_topic --mode entity --topic "OpenAI"`

## Tool reference

For full flags, types, and defaults for each tool, read:

- [resources/search.md](resources/search.md) — web_search, social_search, news_aggregation, github_search, map_website
- [resources/content.md](resources/content.md) — content_operations, document_analysis
- [resources/research.md](resources/research.md) — research_topic, scientific_research

## Output

All tools return structured text to stdout. Errors go to stderr. Exit codes: 0 success, 1 tool error, 2 connection failed.
