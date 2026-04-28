# CFB MCP Server

An MCP server that exposes college football data from [CollegeFootballData.com](https://collegefootballdata.com/) as callable tools.

The server is built with `FastMCP`, fetches live data with `httpx`, and uses a small in-memory TTL cache to avoid burning through API quota during repeated queries.

## What It Does

This project turns common college football lookups into MCP tools that an MCP client can call over stdio.

Current tools:

- `team_info(team, year)`
- `team_game_results(team, year)`
- `team_season_stats(team, year)`
- `player_stats(team, year, category)`
- `ap_rankings(year, week, season_type="regular")`
- `advanced_team_stats(team, year)`

Typical questions this server can answer:

- "How did Missouri do in 2024?"
- "Show me Alabama's advanced team stats for 2023."
- "What were the AP rankings in week 8 of 2025?"
- "Give me Texas receiving stats for 2024."

## Example Prompts

These are good prompt shapes to test with an MCP client such as Claude Desktop:

- "Summarize Missouri's 2024 season record and conference."
- "List Oregon's 2024 game results in chronological order."
- "Show me Georgia's 2023 advanced offensive and defensive stats."
- "Get Ohio State passing stats for 2024."
- "Who was ranked in the AP Top 25 in week 10 of the 2025 regular season?"
- "Compare Alabama's and Texas's advanced team stats for 2024."

For best results, mention the team, year, and stat category directly in the prompt.

## Stack

- Python 3.12+
- `fastmcp`
- `httpx`
- `python-dotenv`

## Requirements

You need a CollegeFootballData API key.

1. Create an account at [CollegeFootballData.com](https://collegefootballdata.com/).
2. Generate an API key.
3. Put it in a local `.env` file:

```env
CFBD_API_KEY=your_api_key_here
```

The server reads `CFBD_API_KEY` from the environment and will raise an error if it is missing.

## Setup

This repository is configured as a Python project with `uv`.

```bash
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

If you do not use `uv`, install the listed dependencies into a Python 3.12 environment manually.

## Run The Server

Start the MCP server locally:

```bash
uv run python server.py
```

For local MCP inspection during development:

```bash
uv run fastmcp dev server.py
```

You can also launch the same server through the project entrypoint:

```bash
uv run python main.py
```

## MCP Tools

### `team_info(team, year)`

Returns a summary for a team season, including wins, losses, ties, games played, conference, and division.

Example:

```json
{
	"team": "Missouri",
	"year": 2024,
	"wins": 10,
	"losses": 2,
	"ties": 0,
	"games_played": 12,
	"conference": "SEC",
	"division": null
}
```

### `team_game_results(team, year)`

Returns the full schedule and results for a team in a given season.

Each game includes:

- `date`
- `home_team`
- `away_team`
- `home_points`
- `away_points`
- `result`

### `team_season_stats(team, year)`

Returns aggregated season statistics from the CFBD season stats endpoint.

### `player_stats(team, year, category)`

Returns player season stats for a team and stat category.

Supported categories depend on the upstream CFBD API. Common categories include:

- `passing`
- `rushing`
- `receiving`
- `defensive`
- `kicking`
- `punting`

### `ap_rankings(year, week, season_type="regular")`

Returns AP Top 25 rankings for a specific week.

### `advanced_team_stats(team, year)`

Returns offensive and defensive advanced metrics, including:

- EPA per play
- success rate
- explosiveness
- rushing EPA
- passing EPA

## Development Notes

### Quick client sanity check

There is a small script for manually checking the API client:

```bash
uv run python test_client.py
```

### Caching

Responses are cached in memory for 1 hour.

- Cache implementation: `cache.py`
- Default TTL: `3600` seconds
- Scope: process-local only

This cache reduces repeated identical requests during demos and development, but it is not persistent across server restarts.

## Project Structure

```text
.
├── cache.py          # Simple in-memory TTL cache
├── cfbd_client.py    # Direct CFBD REST client functions
├── main.py           # Project entrypoint that launches the MCP server
├── server.py         # FastMCP server and tool definitions
├── test_client.py    # Manual API sanity-check script
├── pyproject.toml    # Project metadata and dependencies
└── README.md
```

## Claude Desktop Example

If you want to wire this into an MCP client such as Claude Desktop, configure it to launch the server with your project environment.

Example shape:

```json
{
	"mcpServers": {
		"cfb-stats": {
			"command": "uv",
			"args": ["run", "python", "server.py"],
			"cwd": "/absolute/path/to/cfb-mcp-server",
			"env": {
				"CFBD_API_KEY": "your_api_key_here"
			}
		}
	}
}
```

Adjust the path and environment values for your machine.

## Limitations

- The cache is in-memory only.
- API availability and response shape depend on CollegeFootballData.
- This server currently focuses on a small set of team, player, ranking, and advanced-stat lookups.

## License

Add a license section if you plan to publish or distribute the project.
