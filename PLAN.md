# CFB MCP Server — Project Plan

## What we're building

A Model Context Protocol (MCP) server that exposes college football data from
CollegeFootballData.com as tools that Claude Desktop can call. The goal is a
portfolio project + blog post demonstrating real MCP server development in Python.

When working, you should be able to open Claude Desktop and ask things like:
- "How did Missouri do in 2024?"
- "Who led the SEC in passing EPA last season?"
- "Compare Alabama's offensive efficiency from 2021 to 2024"

---

## Project location

```
~/Code/cfb-mcp-server/
```

---

## Current file state

### Files that exist

**`.env`** — contains the CFBD API key. Do not commit this.
```
CFBD_API_KEY=<key is already set>
```

**`cfbd_client.py`** — rewritten to use direct CFBD REST calls with `httpx`, Bearer auth, and caching.

**`test_client.py`** — basic sanity check file. It now exercises `get_team_info` and `get_game_results`.

**`cache.py`** — added. Contains a simple in-memory TTL cache to avoid repeated API calls.

**`.gitignore`** — exists, correctly ignores `.env`, `.venv/`, `__pycache__/`

### Files that do NOT exist yet

- `claude_desktop_config.json` entry — not yet added to user's config (Step 4)

---

## The current blocker

### Problem 1: Wrong Python version

`uv` is defaulting to Python 3.10 (system Python) instead of Python 3.12
(installed via deadsnakes PPA). Every `uv add` or `uv venv` command recreates
the venv with 3.10.

Python 3.12 is installed and works:
```bash
python3.12 --version  # confirms 3.12 is available
```

The fix is to force uv to use 3.12. Try:
```bash
uv venv --python $(which python3.12) .venv
```

Or pin it in `pyproject.toml`:
```toml
[project]
requires-python = ">=3.12"
```

Then re-add dependencies.

### Problem 2: cfbd library dropped due to pydantic conflict

The `cfbd` PyPI package (v5.x) requires `pydantic<2`, but `fastmcp` requires
`pydantic>=2`. They are incompatible and cannot be installed together.

**Resolution: do NOT use the cfbd library.** Call the CFBD REST API directly
using `httpx` instead. This is cleaner anyway.

---

## Dependencies (correct set, no cfbd)

```bash
uv add fastmcp python-dotenv httpx
```

Verify with:
```bash
uv pip show fastmcp  # location should show python3.12
```

---

## Step 1: Rewrite cfbd_client.py

Call the CFBD API directly with `httpx`. Base URL is
`https://api.collegefootballdata.com`. Authentication is a Bearer token.

The client should be a simple class or set of functions. Example pattern:

```python
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.collegefootballdata.com"

def get_headers():
    return {"Authorization": f"Bearer {os.environ['CFBD_API_KEY']}"}

def get_game_results(team: str, year: int) -> list[dict]:
    response = httpx.get(
        f"{BASE_URL}/games",
        headers=get_headers(),
        params={"year": year, "team": team, "classification": "fbs"}
    )
    response.raise_for_status()
    return response.json()
```

### Functions needed in cfbd_client.py

| Function | CFBD endpoint | Key params |
|---|---|---|
| `get_game_results(team, year)` | `GET /games` | year, team, classification="fbs" |
| `get_team_season_stats(team, year)` | `GET /stats/season` | year, team |
| `get_player_season_stats(team, year, category)` | `GET /stats/player/season` | year, team, category |
| `get_rankings(year, week, season_type)` | `GET /rankings` | year, week, seasonType |
| `get_advanced_team_stats(team, year)` | `GET /stats/season/advanced` | year, team |
| `get_team_info(team, year)` | `GET /teams` + `GET /games` | team, year |

Full API docs: https://apinext.collegefootballdata.com

### Test it works

```bash
uv run --no-project python test_client.py
```

Expected output: Missouri's 2024 game results printed as dicts.

---

## Step 2: Add simple caching (cache.py)

The free tier is 1,000 API calls/month. Add a simple in-memory cache so
repeated identical queries don't burn calls during development and demos.

```python
# cache.py
import time

_cache: dict = {}
TTL = 3600  # 1 hour

def get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < TTL:
        return entry["value"]
    return None

def set(key: str, value):
    _cache[key] = {"value": value, "ts": time.time()}
```

Then wrap each function in `cfbd_client.py`:
```python
from cache import get as cache_get, set as cache_set

def get_game_results(team: str, year: int):
    key = f"games:{team}:{year}"
    cached = cache_get(key)
    if cached:
        return cached
    # ... httpx call ...
    cache_set(key, result)
    return result
```

---

## Step 3: Build server.py (the MCP server)

This is the main deliverable. Use FastMCP — it turns decorated Python functions
into MCP tools automatically.

```python
from mcp.server.fastmcp import FastMCP
from cfbd_client import (
    get_game_results,
    get_team_season_stats,
    get_player_season_stats,
    get_rankings,
    get_advanced_team_stats,
)

mcp = FastMCP("CFB Stats")

@mcp.tool()
def team_game_results(team: str, year: int) -> list[dict]:
    """Get the full schedule and results for a college football team in a given year."""
    return get_game_results(team, year)

@mcp.tool()
def team_season_stats(team: str, year: int) -> list[dict]:
    """Get aggregated season statistics for a college football team."""
    return get_team_season_stats(team, year)

@mcp.tool()
def player_stats(team: str, year: int, category: str) -> list[dict]:
    """
    Get player season stats for a team by category.
    Category options: passing, rushing, receiving, defensive, kicking, punting
    """
    return get_player_season_stats(team, year, category)

@mcp.tool()
def ap_rankings(year: int, week: int, season_type: str = "regular") -> list[dict]:
    """Get AP Top 25 college football rankings for a specific week and year."""
    return get_rankings(year, week, season_type)

@mcp.tool()
def advanced_team_stats(team: str, year: int) -> dict:
    """
    Get advanced stats for a team: EPA per play, success rate, explosiveness,
    rushing EPA, passing EPA for both offense and defense.
    """
    return get_advanced_team_stats(team, year)

if __name__ == "__main__":
    mcp.run()
```

**Important:** The docstrings on each tool are what Claude reads to decide
when to call them. Write them clearly — they are essentially the tool's API contract.

### Run and test the server

```bash
uv run python server.py
```

Also test with MCP Inspector:
```bash
uv run fastmcp dev server.py
```

---

## Step 4: Connect to Claude Desktop

Add to `~/.config/Claude/claude_desktop_config.json` (Linux path):

```json
{
  "mcpServers": {
    "cfb-stats": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/<your-username>/Code/cfb-mcp-server",
        "python",
        "server.py"
      ],
      "env": {
        "CFBD_API_KEY": "<your key here>"
      }
    }
  }
}
```

Restart Claude Desktop. You should see a hammer icon (🔨) in the chat input
indicating tools are available.

---

## Final project structure

```
cfb-mcp-server/
├── server.py          # MCP server — tool definitions (main deliverable)
├── cfbd_client.py     # CFBD API wrapper using httpx
├── cache.py           # Simple in-memory TTL cache
├── test_client.py     # Sanity check script (can delete after)
├── .env               # CFBD_API_KEY (never commit)
├── .gitignore
├── pyproject.toml     # uv project file
└── README.md          # Blog post scaffold
```

---

## CFBD API reference

- Docs: https://apinext.collegefootballdata.com
- Auth: `Authorization: Bearer <your_key>`
- Free tier: 1,000 calls/month
- Check remaining calls: response header `X-CallLimit-Remaining`

---

## Context for the blog post

This project is a portfolio piece for an AI Automation/Acceleration engineer
targeting Forward Deployed Engineer and Solutions Engineer roles at AI companies.
The blog post angle is: "I built an MCP server from scratch to learn the protocol
— here's what MCP actually is, how tools work, and what I learned."

Key talking points:
- MCP is a standardization layer (the USB analogy: write once, any client can use it)
- FastMCP reduces boilerplate — a decorated Python function becomes a tool
- Tool docstrings are the API contract Claude reads to decide when to call a tool
- Caching is important when your data source has rate limits
- The `cfbd` library was dropped due to a pydantic version conflict with fastmcp —
  calling the REST API directly with httpx is simpler and more educational anyway
