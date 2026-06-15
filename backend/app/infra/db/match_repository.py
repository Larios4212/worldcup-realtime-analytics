from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.domain.entities.match import Match, MatchEvent, MatchStatus, Team, Score, MatchStats, EventType
from app.domain.interfaces.match_repository import IMatchRepository
from app.infra.db.models import MatchModel, MatchEventModel, TeamModel
import uuid


class PostgresMatchRepository(IMatchRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, match_id: str) -> Optional[Match]:
        result = await self._session.execute(
            select(MatchModel)
            .options(selectinload(MatchModel.home_team), selectinload(MatchModel.away_team))
            .where(MatchModel.id == match_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def get_live_matches(self) -> list[Match]:
        result = await self._session.execute(
            select(MatchModel)
            .options(selectinload(MatchModel.home_team), selectinload(MatchModel.away_team))
            .where(MatchModel.status.in_([MatchStatus.LIVE.value, MatchStatus.HALFTIME.value]))
        )
        return [self._to_entity(r) for r in result.scalars().all()]

    async def get_all(self, stage: Optional[str] = None) -> list[Match]:
        query = select(MatchModel).options(
            selectinload(MatchModel.home_team),
            selectinload(MatchModel.away_team),
        )
        if stage:
            query = query.where(MatchModel.stage == stage)
        result = await self._session.execute(query.order_by(MatchModel.kickoff_utc))
        return [self._to_entity(r) for r in result.scalars().all()]

    async def save(self, match: Match) -> Match:
        result = await self._session.execute(
            select(MatchModel).where(MatchModel.id == match.id)
        )
        row = result.scalar_one_or_none()

        if row is None:
            row = MatchModel(
                id=match.id,
                home_team_id=match.home_team.id,
                away_team_id=match.away_team.id,
                kickoff_utc=match.kickoff_utc,
                stage=match.stage,
                group=match.group,
                venue=match.venue,
            )
            self._session.add(row)
        else:
            # Update mutable fields
            row.kickoff_utc = match.kickoff_utc
            row.stage = match.stage
            row.group = match.group
            row.venue = match.venue

        row.status = match.status.value if hasattr(match.status, 'value') else match.status
        row.minute = match.minute
        row.score_home = match.score.home
        row.score_away = match.score.away
        row.score_home_ht = match.score.home_ht
        row.score_away_ht = match.score.away_ht
        row.possession_home = match.stats.possession_home
        row.possession_away = match.stats.possession_away
        row.shots_home = match.stats.shots_home
        row.shots_away = match.stats.shots_away
        row.xg_home = match.stats.xg_home
        row.xg_away = match.stats.xg_away

        await self._session.commit()
        return match

    async def save_event(self, event: MatchEvent) -> MatchEvent:
        row = MatchEventModel(
            id=event.id or str(uuid.uuid4()),
            match_id=event.match_id,
            event_type=event.event_type,
            minute=event.minute,
            team_id=event.team_id,
            player_name=event.player_name,
            player_in_name=event.player_in_name,
            description=event.description,
            timestamp=event.timestamp,
        )
        self._session.add(row)
        await self._session.commit()
        return event

    async def get_events(self, match_id: str) -> list[MatchEvent]:
        result = await self._session.execute(
            select(MatchEventModel)
            .where(MatchEventModel.match_id == match_id)
            .order_by(MatchEventModel.minute)
        )
        return [self._event_to_entity(r) for r in result.scalars().all()]

    def _to_entity(self, row: MatchModel) -> Match:
        try:
            status = MatchStatus(row.status)
        except ValueError:
            status = MatchStatus.SCHEDULED
        return Match(
            id=row.id,
            home_team=Team(id=row.home_team_id, name=row.home_team.name if row.home_team else "", short_name=row.home_team.short_name if row.home_team else ""),
            away_team=Team(id=row.away_team_id, name=row.away_team.name if row.away_team else "", short_name=row.away_team.short_name if row.away_team else ""),
            status=status,
            kickoff_utc=row.kickoff_utc,
            score=Score(home=row.score_home, away=row.score_away, home_ht=row.score_home_ht, away_ht=row.score_away_ht),
            stats=MatchStats(
                possession_home=row.possession_home,
                possession_away=row.possession_away,
                shots_home=row.shots_home,
                shots_away=row.shots_away,
                shots_on_target_home=row.shots_on_target_home,
                shots_on_target_away=row.shots_on_target_away,
                xg_home=row.xg_home,
                xg_away=row.xg_away,
                passes_home=row.passes_home,
                passes_away=row.passes_away,
                fouls_home=row.fouls_home,
                fouls_away=row.fouls_away,
                corners_home=row.corners_home,
                corners_away=row.corners_away,
            ),
            minute=row.minute,
            stage=row.stage,
            group=row.group,
            venue=row.venue,
        )

    def _event_to_entity(self, row: MatchEventModel) -> MatchEvent:
        return MatchEvent(
            id=row.id,
            match_id=row.match_id,
            event_type=row.event_type,
            minute=row.minute,
            team_id=row.team_id,
            player_name=row.player_name,
            player_in_name=row.player_in_name,
            description=row.description,
            timestamp=row.timestamp,
        )
