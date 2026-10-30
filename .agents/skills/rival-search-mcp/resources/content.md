# Content Analysis Tools

## content_operations

Consolidated content operations: retrieve, stream, analyze, and extract from URLs.

```bash
uv run --with fastmcp python scripts/cli.py call-tool content_operations --operation <value> --url <value> --content <value> --extraction-method <value> --analysis-type <value>
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--operation` | string | yes | — | Operation: "retrieve", "stream", "analyze", "extract" |
| `--url` | string | no | null | URL for retrieve/stream/extract operations |
| `--content` | string | no | null | Content string for analyze operation |
| `--extraction-method` | string | no | auto | For retrieve: "auto", "html", "text", "markdown" |
| `--analysis-type` | string | no | general | For analyze: "general", "sentiment", "technical", "business" |
| `--max-links` | integer | no | 100 | For extract: maximum links to extract |
| `--link-type` | string | no | all | For extract: "all", "internal", "external", "images", "documents" |
| `--extract-key-points` | boolean | no | true | For analyze: extract key points |
| `--summarize` | boolean | no | true | For analyze: create summary |
| `--include-metadata` | boolean | no | true | Include metadata in response |

### Operations

**retrieve** — Fetch and extract content from a URL:
```bash
python scripts/cli.py call-tool content_operations --operation retrieve --url "https://example.com/article" --extraction-method markdown
```

**analyze** — Analyze content with sentiment/technical/business analysis:
```bash
python scripts/cli.py call-tool content_operations --operation analyze --content "Your text here" --analysis-type sentiment --extract-key-points
```

**extract** — Extract links and resources from a page:
```bash
python scripts/cli.py call-tool content_operations --operation extract --url "https://example.com" --link-type external --max-links 50
```

**stream** — Stream content from a URL:
```bash
python scripts/cli.py call-tool content_operations --operation stream --url "https://example.com/large-page"
```

---

## document_analysis

Download and analyze documents with OCR support. Supports PDF, Word (.docx), Text (.txt, .md), and Images (.jpg, .png). No authentication required. OCR auto-downloads models on first use (~100MB).

```bash
uv run --with fastmcp python scripts/cli.py call-tool document_analysis --url <value> --max-pages <value> --extract-metadata --summary-length <value>
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--url` | string | yes | — | URL of the document (PDF, Word, Text, Image) |
| `--max-pages` | integer | no | 10 | Maximum pages to extract (PDFs) |
| `--extract-metadata` | boolean | no | true | Extract document metadata |
| `--summary-length` | integer | no | 500 | Length of text preview in output |

**Examples:**

Extract text from a PDF:
```bash
python scripts/cli.py call-tool document_analysis --url "https://arxiv.org/pdf/2301.00001" --max-pages 5
```

OCR an image:
```bash
python scripts/cli.py call-tool document_analysis --url "https://example.com/screenshot.png"
```

Analyze a Word document:
```bash
python scripts/cli.py call-tool document_analysis --url "https://example.com/report.docx" --extract-metadata --summary-length 1000
```
