import os
from dotenv import load_dotenv
from fastmcp import FastMCP

from cfbd_client import (
    get_team_info,
    get_game_results,
    get_team_season_stats,
    get_player_season_stats,
    get_rankings,
    get_advanced_team_stats,
)

load_dotenv()

mcp = FastMCP("CFB Stats")


@mcp.tool()
def team_info(team: str, year: int) -> dict:
    """Get season record (wins/losses) and conference info for a college football team."""
    return get_team_info(team, year)


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
