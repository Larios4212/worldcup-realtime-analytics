from typing import Any


def normalize_football_data_match(raw: dict[str, Any]) -> dict:
    """
    Normalize a match object from football-data.org API v4
    into our internal schema.
    """
    score = raw.get("score", {})
    full_time = score.get("fullTime", {}) or {}
    half_time = score.get("halfTime", {}) or {}

    home = raw.get("homeTeam") or {}
    away = raw.get("awayTeam") or {}

    return {
        "type": "STATS_UPDATE",
        "id": str(raw["id"]),
        "status": _map_status(raw.get("status", "")),
        "minute": raw.get("minute"),
        "home_team": {
            "id": str(home.get("id", "") or ""),
            "name": home.get("name") or "TBD",
            "short_name": home.get("shortName") or home.get("tla") or (home.get("name") or "TBD")[:3].upper(),
            "crest_url": home.get("crest"),
        },
        "away_team": {
            "id": str(away.get("id", "") or ""),
            "name": away.get("name") or "TBD",
            "short_name": away.get("shortName") or away.get("tla") or (away.get("name") or "TBD")[:3].upper(),
            "crest_url": away.get("crest"),
        },
        "score": {
            "home": full_time.get("home") or 0,
            "away": full_time.get("away") or 0,
            "home_ht": half_time.get("home"),
            "away_ht": half_time.get("away"),
        },
        "stage": _map_stage(raw.get("stage", "GROUP_STAGE")),
        "group": raw.get("group"),
        "kickoff_utc": raw.get("utcDate"),
        "venue": raw.get("venue"),
    }


def normalize_all_matches(raw_list: list[dict]) -> list[dict]:
    return [normalize_football_data_match(r) for r in raw_list]


def _map_status(status: str) -> str:
    return {
        "SCHEDULED": "SCHEDULED",
        "TIMED": "SCHEDULED",
        "LIVE": "LIVE",
        "IN_PLAY": "LIVE",
        "PAUSED": "HALFTIME",
        "FINISHED": "FINISHED",
        "POSTPONED": "POSTPONED",
        "CANCELLED": "POSTPONED",
    }.get(status, "SCHEDULED")


def _map_stage(stage: str) -> str:
    return {
        "GROUP_STAGE": "Group Stage",
        "LAST_16": "Round of 16",
        "QUARTER_FINALS": "Quarter-Final",
        "SEMI_FINALS": "Semi-Final",
        "THIRD_PLACE": "Third Place",
        "FINAL": "Final",
    }.get(stage, stage.replace("_", " ").title())
