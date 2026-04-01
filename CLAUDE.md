# BuzzOps — Claude Code Guide

## What this project is

BuzzOps is an MCP server that translates enterprise software marketing buzzwords into plain English. It exposes four tools to Claude Desktop (or any MCP-compatible client) via the `mcp` library.

## Project layout

```
buzzops/
  server.py       # All four MCP tools + shared helpers
  __init__.py     # Empty
test_buzzops.py   # Standalone test script (not pytest — run directly)
pyproject.toml    # Build config; entry point: buzzops.server:main
```

## Running the test program

```bash
python test_buzzops.py
```

Uses Python 3.10 (`/opt/homebrew/opt/python@3.10/bin/python3.10`). The system `python3` points to 3.13, which lacks the installed dependencies — always use 3.10 explicitly or activate a venv.

## Installing dependencies

```bash
pip install -e .          # runtime only
pip install -e ".[dev]"   # includes pytest
```

Dependencies: `mcp[cli]`, `httpx`, `beautifulsoup4`, `ddgs`.

## The four MCP tools (all in `buzzops/server.py`)

| Tool | What it does |
|------|-------------|
| `debuzz(content)` | Counts buzzwords in pasted text or a fetched URL; returns density stats + translations |
| `retro_halo(company_name)` | Compares current vs. 2022-2023 messaging via DDG search |
| `countdown_to_zombie(company_name)` | Searches funding, hiring, and distress signals to estimate startup health |
| `investor_combustion(company_name)` | Compares marketing vs. real-user buzzword density; measures VC-to-adjective conversion |

## Key internals

- `BUZZWORDS` — list of ~70 buzzwords used for density counting (`_count_buzzwords`)
- `BUZZWORD_TRANSLATIONS` — canonical field guide dict used by `_match_translations`; keys are lowercase, sorted longest-first to prevent partial matches
- `_ddg_search(query, max_results)` — wraps `ddgs.DDGS().text()`; returns `[{title, href, body}]`
- `_fetch_url(url)` — fetches and BeautifulSoup-parses a page, strips nav/footer/script, caps at 8000 chars
- All tools return `json.dumps(...)` strings with an `"instruction"` field that guides the LLM's response format

## Connecting to Claude Desktop

Copy `claude_desktop_config.example.json` to `~/Library/Application Support/Claude/claude_desktop_config.json` and replace the path placeholder with your actual venv path:

```json
{
  "mcpServers": {
    "buzzops": {
      "command": "/absolute/path/to/BuzzOps/.venv/bin/buzzops",
      "args": []
    }
  }
}
```

`claude_desktop_config.json` is gitignored — only the `.example` template is committed.

## Notes

- The `test_buzzops.py` script makes live network calls (DDG searches + one HTTP fetch). Expect ~15-45 seconds to run and occasional search engine 403s — those are non-fatal.
- `pyproject.toml` has a GitLab private index configured upstream in pip config; 401 warnings on install are expected and harmless — packages fall through to PyPI.
- No linter, formatter, or CI configuration is present in this repo.
