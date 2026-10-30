# Research & Scientific Tools

## research_topic

End-to-end research workflow for a topic. Combines search, content retrieval, and analysis into a single operation.

```bash
uv run --with fastmcp python scripts/cli.py call-tool research_topic --topic <value> --sources <value> --max-sources <value> --include-analysis
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--topic` | string | yes | — | Research topic |
| `--sources` | JSON string | no | null | List of specific sources to use |
| `--max-sources` | integer | no | 5 | Maximum number of sources to research |
| `--include-analysis` | boolean | no | true | Include content analysis |

**Example:**
```bash
python scripts/cli.py call-tool research_topic --topic "LLM agent frameworks comparison" --max-sources 10
```

---

## scientific_research

Academic paper and dataset discovery across multiple sources. No authentication required.

```bash
uv run --with fastmcp python scripts/cli.py call-tool scientific_research --operation <value> --query <value> --max-results <value> --sources <value> --categories <value>
```

| Flag | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `--operation` | string | yes | — | "academic_search" or "dataset_discovery" |
| `--query` | string | yes | — | Search query |
| `--max-results` | integer | no | 10 | Maximum results to return |
| `--sources` | JSON string | no | null | Specific sources to search |
| `--categories` | JSON string | no | null | Categories for dataset discovery |

### Operations

**academic_search** — Search papers across OpenAlex, CrossRef, arXiv, PubMed, Europe PMC:
```bash
python scripts/cli.py call-tool scientific_research --operation academic_search --query "transformer attention mechanisms" --sources '["openalex", "arxiv"]'
```

**dataset_discovery** — Find datasets on Kaggle, HuggingFace:
```bash
python scripts/cli.py call-tool scientific_research --operation dataset_discovery --query "sentiment analysis" --sources '["huggingface", "kaggle"]'
```

---
