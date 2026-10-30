# Search & Discovery Tools

## web_search

Search across Yahoo and DuckDuckGo engines with automatic fallback support.

```bash
uv run --with fastmcp python scripts/cli.py call-tool web_search --query <value> --num-results <value> --extract-content --follow-links --max-depth <value> --use-fallback
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--query` | string | yes | — | Search query string |
| `--num-results` | integer | no | 10 | Number of results per engine |
| `--extract-content` | boolean | no | true | Extract full page content |
| `--follow-links` | boolean | no | true | Follow internal links |
| `--max-depth` | integer | no | 2 | Maximum depth for link following |
| `--use-fallback` | boolean | no | true | Use fallback strategy if engine fails |

**Example:**
```bash
python scripts/cli.py call-tool web_search --query "best MCP servers 2026" --num-results 5
```

---

## social_search

Search Reddit, Hacker News, Dev.to, Product Hunt, and Medium without authentication.

```bash
uv run --with fastmcp python scripts/cli.py call-tool social_search --query <value> --platforms <value> --max-results-per-platform <value> --reddit-subreddit <value> --time-filter <value>
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--query` | string | yes | — | Search query |
| `--platforms` | array[string] | no | reddit, hackernews, devto | Platforms to search |
| `--max-results-per-platform` | integer | no | 10 | Max results per platform |
| `--max-results` | integer | no | 0 | Global max results (0 = unlimited) |
| `--reddit-subreddit` | string | no | all | Subreddit to search |
| `--time-filter` | string | no | all | Time filter: all, day, week, month, year |

**Platforms:** `reddit`, `hackernews`, `devto`, `producthunt`, `medium`

**Example:**
```bash
python scripts/cli.py call-tool social_search --query "AI agents" --platforms reddit --platforms hackernews --time-filter week
```

---

## news_aggregation

Aggregate news from Google News RSS feed without authentication.

```bash
uv run --with fastmcp python scripts/cli.py call-tool news_aggregation --query <value> --max-results <value> --language <value> --country <value> --time-range <value>
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--query` | string | yes | — | News search query |
| `--max-results` | integer | no | 10 | Maximum results to return |
| `--language` | string | no | en | Language code |
| `--country` | string | no | US | Country code |
| `--time-range` | string | no | anytime | Time range: anytime, day, week, month |

**Example:**
```bash
python scripts/cli.py call-tool news_aggregation --query "artificial intelligence startups" --time-range week --max-results 20
```

---

## github_search

Search public GitHub repositories using the public API. No authentication required. Rate limited to 60 requests/hour.

```bash
uv run --with fastmcp python scripts/cli.py call-tool github_search --query <value> --language <value> --sort <value> --max-results <value> --include-readme
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--query` | string | yes | — | Search query (e.g., "web framework") |
| `--language` | string | no | null | Filter by language (e.g., "Python", "TypeScript") |
| `--sort` | string | no | stars | Sort by: stars, forks, updated |
| `--max-results` | integer | no | 10 | Maximum results to return |
| `--include-readme` | boolean | no | false | Fetch README content (slower) |

**Example:**
```bash
python scripts/cli.py call-tool github_search --query "MCP server" --language Python --sort stars --include-readme
```

---

## map_website

Map and explore websites with different traversal modes.

```bash
uv run --with fastmcp python scripts/cli.py call-tool map_website --url <value> --mode <value> --max-pages <value> --max-depth <value> --generate-llms-txt
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--url` | string | yes | — | Website URL to traverse |
| `--mode` | string | no | research | Mode: "research" (general), "docs" (documentation), "map" (structure) |
| `--max-pages` | integer | no | 5 | Maximum pages to traverse |
| `--max-depth` | integer | no | 2 | Maximum depth for mapping |
| `--generate-llms-txt` | boolean | no | false | Generate llms.txt output |

**Example:**
```bash
python scripts/cli.py call-tool map_website --url "https://docs.example.com" --mode docs --max-pages 20
```
