"""
Internal endpoints — only called by the ingestion service, not exposed publicly.
These are not authenticated because they run inside the Docker network.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from app.infra.db.session import AsyncSessionLocal
from app.infra.db.models import TeamModel, MatchModel
from app.infra.cache.redis import get_redis
import json

router = APIRouter()


class UpsertMatchPayload(BaseModel):
    id: str
    status: str
    minute: Optional[int] = None
    home_team: dict
    away_team: dict
    score: dict
    stage: str = "Group Stage"
    group: Optional[str] = None
    kickoff_utc: Optional[str] = None
    venue: Optional[str] = None


@router.post("/matches/upsert", status_code=200)
async def upsert_match(payload: UpsertMatchPayload):
    """Called by the ingestion service to persist / update a match."""
    try:
        async with AsyncSessionLocal() as db:
            home_id = payload.home_team.get("id", "").strip()
            away_id = payload.away_team.get("id", "").strip()

            # Skip matches without team assignments (playoff slots not yet determined)
            if not home_id or not away_id:
                return {"ok": True, "id": payload.id, "skipped": "no_teams"}

            # 1. Upsert home team
            await _upsert_team_raw(db, payload.home_team)
            # 2. Upsert away team
            await _upsert_team_raw(db, payload.away_team)

            # 3. Parse kickoff (store as naive UTC)
            kickoff = datetime.utcnow()
            if payload.kickoff_utc:
                try:
                    dt = datetime.fromisoformat(
                        payload.kickoff_utc.replace("Z", "+00:00")
                    )
                    # Strip tzinfo — column is TIMESTAMP WITHOUT TIME ZONE
                    kickoff = dt.replace(tzinfo=None)
                except ValueError:
                    pass

            # 4. Upsert match
            result = await db.execute(
                select(MatchModel).where(MatchModel.id == payload.id)
            )
            row = result.scalar_one_or_none()

            if row is None:
                row = MatchModel(
                    id=payload.id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    kickoff_utc=kickoff,
                    stage=payload.stage,
                    group=payload.group,
                    venue=payload.venue,
                    status=payload.status,
                    score_home=payload.score.get("home", 0),
                    score_away=payload.score.get("away", 0),
                    score_home_ht=payload.score.get("home_ht"),
                    score_away_ht=payload.score.get("away_ht"),
                    minute=payload.minute,
                )
                db.add(row)
            else:
                row.status = payload.status
                row.minute = payload.minute
                row.score_home = payload.score.get("home", 0)
                row.score_away = payload.score.get("away", 0)
                row.score_home_ht = payload.score.get("home_ht")
                row.score_away_ht = payload.score.get("away_ht")
                row.kickoff_utc = kickoff
                row.stage = payload.stage
                row.group = payload.group
                row.venue = payload.venue

            await db.commit()

        # 5. Broadcast to Redis (best-effort)
        try:
            redis = await get_redis()
            event = {
                "type": "STATS_UPDATE",
                "match_id": payload.id,
                "score": {"home": payload.score.get("home", 0), "away": payload.score.get("away", 0)},
                "status": payload.status,
            }
            await redis.publish(f"match:{payload.id}:events", json.dumps(event))
        except Exception:
            pass

        return {"ok": True, "id": payload.id}

    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        )


async def _upsert_team_raw(db, team_data: dict) -> None:
    team_id = team_data.get("id", "")
    if not team_id:
        return
    result = await db.execute(select(TeamModel).where(TeamModel.id == team_id))
    row = result.scalar_one_or_none()
    if row is None:
        db.add(TeamModel(
            id=team_id,
            name=team_data.get("name", ""),
            short_name=team_data.get("short_name", team_data.get("name", "")[:3].upper()),
            crest_url=team_data.get("crest_url"),
        ))
    else:
        if team_data.get("crest_url") and not row.crest_url:
            row.crest_url = team_data["crest_url"]
