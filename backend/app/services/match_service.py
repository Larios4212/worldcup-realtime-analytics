from typing import Optional
from app.domain.entities.match import Match, MatchEvent, MatchStatus
from app.domain.interfaces.match_repository import IMatchRepository, IMatchEventPublisher
from app.core.logging import logger


class MatchService:
    """Core business logic for match operations."""

    def __init__(
        self,
        repository: IMatchRepository,
        publisher: IMatchEventPublisher,
    ):
        self._repo = repository
        self._publisher = publisher

    async def get_match(self, match_id: str) -> Optional[Match]:
        return await self._repo.get_by_id(match_id)

    async def list_matches(self, stage: Optional[str] = None) -> list[Match]:
        return await self._repo.get_all(stage=stage)

    async def list_live_matches(self) -> list[Match]:
        return await self._repo.get_live_matches()

    async def get_timeline(self, match_id: str) -> list[MatchEvent]:
        return await self._repo.get_events(match_id)

    async def process_event(self, event: MatchEvent) -> None:
        """Persist a match event and broadcast it to subscribers."""
        await self._repo.save_event(event)

        payload = {
            "type": event.event_type.value,
            "match_id": event.match_id,
            "minute": event.minute,
            "team_id": event.team_id,
            "player": event.player_name,
            "description": event.description,
            "timestamp": event.timestamp.isoformat(),
        }

        await self._publisher.publish(event.match_id, payload)
        logger.info("match_event_processed", match_id=event.match_id, event_type=event.event_type)

    async def update_match(self, match: Match) -> Match:
        """Update match state and broadcast updated stats."""
        saved = await self._repo.save(match)

        stats_payload = {
            "type": "STATS_UPDATE",
            "match_id": match.id,
            "score": {"home": match.score.home, "away": match.score.away},
            "stats": {
                "possession_home": match.stats.possession_home,
                "possession_away": match.stats.possession_away,
                "shots_home": match.stats.shots_home,
                "shots_away": match.stats.shots_away,
                "xg_home": match.stats.xg_home,
                "xg_away": match.stats.xg_away,
            },
            "minute": match.minute,
            "status": match.status.value,
        }

        await self._publisher.publish(match.id, stats_payload)
        return saved
