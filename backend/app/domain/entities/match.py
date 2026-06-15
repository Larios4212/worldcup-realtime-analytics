from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    HALFTIME = "HALFTIME"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"


class EventType(str, Enum):
    GOAL = "GOAL"
    OWN_GOAL = "OWN_GOAL"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    SUBSTITUTION = "SUBSTITUTION"
    PENALTY = "PENALTY"
    VAR = "VAR"
    KICK_OFF = "KICK_OFF"
    HALF_TIME = "HALF_TIME"
    FULL_TIME = "FULL_TIME"


@dataclass
class Team:
    id: str
    name: str
    short_name: str
    crest_url: Optional[str] = None
    group: Optional[str] = None


@dataclass
class Score:
    home: int = 0
    away: int = 0
    home_ht: Optional[int] = None
    away_ht: Optional[int] = None


@dataclass
class MatchStats:
    possession_home: float = 50.0
    possession_away: float = 50.0
    shots_home: int = 0
    shots_away: int = 0
    shots_on_target_home: int = 0
    shots_on_target_away: int = 0
    xg_home: float = 0.0
    xg_away: float = 0.0
    passes_home: int = 0
    passes_away: int = 0
    pass_accuracy_home: float = 0.0
    pass_accuracy_away: float = 0.0
    fouls_home: int = 0
    fouls_away: int = 0
    corners_home: int = 0
    corners_away: int = 0
    offsides_home: int = 0
    offsides_away: int = 0


@dataclass
class MatchEvent:
    id: str
    match_id: str
    event_type: EventType
    minute: int
    team_id: str
    player_name: Optional[str] = None
    player_in_name: Optional[str] = None  # For substitutions
    description: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Match:
    id: str
    home_team: Team
    away_team: Team
    status: MatchStatus
    kickoff_utc: datetime
    score: Score = field(default_factory=Score)
    stats: MatchStats = field(default_factory=MatchStats)
    minute: Optional[int] = None
    stage: str = "Group Stage"
    group: Optional[str] = None
    venue: Optional[str] = None
    events: list[MatchEvent] = field(default_factory=list)
