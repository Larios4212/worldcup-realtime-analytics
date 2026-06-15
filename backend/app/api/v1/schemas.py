from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.domain.entities.match import MatchStatus, EventType


class TeamSchema(BaseModel):
    id: str
    name: str
    short_name: str
    crest_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ScoreSchema(BaseModel):
    home: int
    away: int
    home_ht: Optional[int] = None
    away_ht: Optional[int] = None

    model_config = {"from_attributes": True}


class MatchStatsSchema(BaseModel):
    possession_home: float
    possession_away: float
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int
    xg_home: float
    xg_away: float
    passes_home: int
    passes_away: int
    fouls_home: int
    fouls_away: int
    corners_home: int
    corners_away: int

    model_config = {"from_attributes": True}


class MatchEventSchema(BaseModel):
    id: str
    match_id: str
    event_type: EventType
    minute: int
    team_id: str
    player_name: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    id: str
    home_team: TeamSchema
    away_team: TeamSchema
    status: MatchStatus
    kickoff_utc: datetime
    score: ScoreSchema
    stats: MatchStatsSchema
    minute: Optional[int] = None
    stage: str
    group: Optional[str] = None
    venue: Optional[str] = None

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]
    total: int


class TimelineResponse(BaseModel):
    match_id: str
    events: list[MatchEventSchema]
