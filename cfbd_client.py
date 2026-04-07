import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

from cache import get as cache_get, set as cache_set

load_dotenv()

BASE_URL = "https://api.collegefootballdata.com"
CACHE_TTL_SECONDS = 3600
TIMEOUT_SECONDS = 30.0


def _get_api_key() -> str:
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError("CFBD_API_KEY is not set in the environment")
    return api_key


def _get_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_get_api_key()}"}


def _fetch_json(path: str, params: dict | None = None) -> list[dict] | dict:
    url = f"{BASE_URL}{path}"
    response = httpx.get(url, headers=_get_headers(), params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _cached_fetch(key: str, path: str, params: dict | None = None):
    cached = cache_get(key)
    if cached is not None:
        return cached

    result = _fetch_json(path, params=params)
    cache_set(key, result)
    return result


def _normalize_team(team: str) -> str:
    return team.strip()


def get_game_results(team: str, year: int) -> list[dict]:
    team = _normalize_team(team)
    key = f"games:{team}:{year}"
    games = _cached_fetch(
        key,
        "/games",
        params={"year": year, "team": team, "classification": "fbs"},
    )

    results = []
    for game in games:
        home_points = game.get("homePoints")
        away_points = game.get("awayPoints")
        home_team = game.get("homeTeam")
        away_team = game.get("awayTeam")
        start_date = game.get("startDate")

        if home_points is None or away_points is None:
            result = "scheduled"
        elif home_team == team:
            result = "W" if home_points > away_points else "L"
        else:
            result = "W" if away_points > home_points else "L"

        results.append(
            {
                "date": start_date[:10] if isinstance(start_date, str) else "TBD",
                "home_team": home_team,
                "away_team": away_team,
                "home_points": home_points,
                "away_points": away_points,
                "result": result,
            }
        )

    return sorted(results, key=lambda item: item["date"])


def get_team_season_stats(team: str, year: int) -> list[dict]:
    team = _normalize_team(team)
    key = f"team_stats:{team}:{year}"
    stats = _cached_fetch(
        key,
        "/stats/season",
        params={"year": year, "team": team},
    )
    return stats if isinstance(stats, list) else []


def get_player_season_stats(team: str, year: int, category: str) -> list[dict]:
    team = _normalize_team(team)
    key = f"player_stats:{team}:{year}:{category}"
    stats = _cached_fetch(
        key,
        "/stats/player/season",
        params={"year": year, "team": team, "category": category},
    )
    return stats if isinstance(stats, list) else []


def get_rankings(year: int, week: int, season_type: str = "regular") -> list[dict]:
    key = f"rankings:{year}:{week}:{season_type}"
    ranking_data = _cached_fetch(
        key,
        "/rankings",
        params={"year": year, "week": week, "seasonType": season_type},
    )

    if not isinstance(ranking_data, list):
        return []

    for poll_week in ranking_data:
        polls = poll_week.get("polls") or []
        for poll in polls:
            if poll.get("poll") == "AP Top 25":
                return [
                    {
                        "rank": rank.get("rank"),
                        "team": rank.get("school"),
                        "points": rank.get("points"),
                    }
                    for rank in poll.get("ranks", [])
                ]

    return []


def get_advanced_team_stats(team: str, year: int) -> dict:
    team = _normalize_team(team)
    key = f"advanced_stats:{team}:{year}"
    stats = _cached_fetch(
        key,
        "/stats/season/advanced",
        params={"year": year, "team": team},
    )

    if not isinstance(stats, list) or not stats:
        return {}

    season_stats = stats[0]
    offense = season_stats.get("offense", {}) or {}
    defense = season_stats.get("defense", {}) or {}
    return {
        "team": season_stats.get("team", team),
        "year": year,
        "offense": {
            "epa_per_play": offense.get("epaPerPlay"),
            "success_rate": offense.get("successRate"),
            "explosiveness": offense.get("explosiveness"),
            "rushing_epa": offense.get("rushingEpaPerPlay"),
            "passing_epa": offense.get("passingEpaPerPlay"),
        },
        "defense": {
            "epa_per_play": defense.get("epaPerPlay"),
            "success_rate": defense.get("successRate"),
            "explosiveness": defense.get("explosiveness"),
        },
    }


def get_team_info(team: str, year: int) -> dict:
    team = _normalize_team(team)
    key = f"team_info:{team}:{year}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    teams = _fetch_json("/teams", params={"year": year})
    team_record = next(
        (item for item in teams if item.get("school") == team or item.get("school") == team.title()),
        None,
    )

    games = get_game_results(team, year)
    wins = sum(1 for game in games if game["result"] == "W")
    losses = sum(1 for game in games if game["result"] == "L")
    ties = sum(1 for game in games if game["result"] not in {"W", "L", "scheduled"})

    result = {
        "team": team,
        "year": year,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "games_played": len(games),
        "conference": team_record.get("conference") if team_record else None,
        "division": team_record.get("division") if team_record else None,
    }

    cache_set(key, result)
    return result
