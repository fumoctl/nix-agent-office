# Research & Office Suite Plugin Rules

- Use the `rivalsearch` (or `rivalsearch-local`) MCP server for multi-engine web, academic, social, news, and GitHub research.
- Record all sources, quality scores, claim verifications, and quantitative tables in the `scratchpad` MCP server (`scratchpad_init_session`, `scratchpad_add_source`, `scratchpad_record_table`, `scratchpad_verify_claim`, `scratchpad_export_dossier`) or `scratchpad-cli`.
- Read `.agents/skills/{docx,pptx,xlsx,pdf}/SKILL.md` before generating `.docx`, `.pptx`, `.xlsx`, or `.pdf` files, and always run their validation/QA scripts via `./bin/nix-exec` or inside `nix develop`.
