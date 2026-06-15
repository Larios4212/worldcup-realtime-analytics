from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.infra.db.session import Base
from app.domain.entities.match import MatchStatus, EventType


class TeamModel(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    crest_url = Column(String, nullable=True)
    group = Column(String, nullable=True)


class MatchModel(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True)
    home_team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    status = Column(SAEnum(MatchStatus), nullable=False, default=MatchStatus.SCHEDULED)
    kickoff_utc = Column(DateTime, nullable=False)
    score_home = Column(Integer, default=0)
    score_away = Column(Integer, default=0)
    score_home_ht = Column(Integer, nullable=True)
    score_away_ht = Column(Integer, nullable=True)
    minute = Column(Integer, nullable=True)
    stage = Column(String, default="Group Stage")
    group = Column(String, nullable=True)
    venue = Column(String, nullable=True)

    # Stats
    possession_home = Column(Float, default=50.0)
    possession_away = Column(Float, default=50.0)
    shots_home = Column(Integer, default=0)
    shots_away = Column(Integer, default=0)
    shots_on_target_home = Column(Integer, default=0)
    shots_on_target_away = Column(Integer, default=0)
    xg_home = Column(Float, default=0.0)
    xg_away = Column(Float, default=0.0)
    passes_home = Column(Integer, default=0)
    passes_away = Column(Integer, default=0)
    pass_accuracy_home = Column(Float, default=0.0)
    pass_accuracy_away = Column(Float, default=0.0)
    fouls_home = Column(Integer, default=0)
    fouls_away = Column(Integer, default=0)
    corners_home = Column(Integer, default=0)
    corners_away = Column(Integer, default=0)
    offsides_home = Column(Integer, default=0)
    offsides_away = Column(Integer, default=0)

    home_team = relationship("TeamModel", foreign_keys=[home_team_id])
    away_team = relationship("TeamModel", foreign_keys=[away_team_id])
    events = relationship("MatchEventModel", back_populates="match", order_by="MatchEventModel.minute")


class MatchEventModel(Base):
    __tablename__ = "match_events"

    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.id"), nullable=False)
    event_type = Column(SAEnum(EventType), nullable=False)
    minute = Column(Integer, nullable=False)
    team_id = Column(String, nullable=False)
    player_name = Column(String, nullable=True)
    player_in_name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    match = relationship("MatchModel", back_populates="events")
