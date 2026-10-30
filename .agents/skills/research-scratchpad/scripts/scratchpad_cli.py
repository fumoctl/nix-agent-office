#!/usr/bin/env python3
"""Wrapper entrypoint for the Research Scratchpad CLI."""

from pathlib import Path
import runpy
import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVER_SCRIPT = REPO_ROOT / "nix" / "mcp" / "scratchpad_server.py"

if __name__ == "__main__":
    sys.path.insert(0, str(SERVER_SCRIPT.parent))
    runpy.run_path(str(SERVER_SCRIPT), run_name="__main__")
