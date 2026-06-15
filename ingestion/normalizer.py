from typing import Any


def normalize_football_data_match(raw: dict[str, Any]) -> dict:
    """
    Normalize a match object from football-data.org API v4
    into our internal schema.
    """
    score = raw.get("score", {})
    full_time = score.get("fullTime", {})
    half_time = score.get("halfTime", {})

    return {
        "type": "STATS_UPDATE",
        "id": str(raw["id"]),
        "status": _map_status(raw.get("status", "")),
        "minute": raw.get("minute"),
        "home_team": {
            "id": str(raw["homeTeam"]["id"]),
            "name": raw["homeTeam"]["name"],
            "short_name": raw["homeTeam"].get("shortName", raw["homeTeam"]["name"][:3].upper()),
            "crest_url": raw["homeTeam"].get("crest"),
        },
        "away_team": {
            "id": str(raw["awayTeam"]["id"]),
            "name": raw["awayTeam"]["name"],
            "short_name": raw["awayTeam"].get("shortName", raw["awayTeam"]["name"][:3].upper()),
            "crest_url": raw["awayTeam"].get("crest"),
        },
        "score": {
            "home": full_time.get("home") or 0,
            "away": full_time.get("away") or 0,
            "home_ht": half_time.get("home"),
            "away_ht": half_time.get("away"),
        },
        "stage": raw.get("stage", "GROUP_STAGE"),
        "group": raw.get("group"),
        "kickoff_utc": raw.get("utcDate"),
    }


def _map_status(status: str) -> str:
    mapping = {
        "SCHEDULED": "SCHEDULED",
        "LIVE": "LIVE",
        "IN_PLAY": "LIVE",
        "PAUSED": "HALFTIME",
        "FINISHED": "FINISHED",
        "POSTPONED": "POSTPONED",
    }
    return mapping.get(status, "SCHEDULED")
