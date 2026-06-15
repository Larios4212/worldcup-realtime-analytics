from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.match import Match, MatchEvent


class IMatchRepository(ABC):
    """Interface for match persistence."""

    @abstractmethod
    async def get_by_id(self, match_id: str) -> Optional[Match]:
        ...

    @abstractmethod
    async def get_live_matches(self) -> list[Match]:
        ...

    @abstractmethod
    async def get_all(self, stage: Optional[str] = None) -> list[Match]:
        ...

    @abstractmethod
    async def save(self, match: Match) -> Match:
        ...

    @abstractmethod
    async def save_event(self, event: MatchEvent) -> MatchEvent:
        ...

    @abstractmethod
    async def get_events(self, match_id: str) -> list[MatchEvent]:
        ...


class IMatchEventPublisher(ABC):
    """Interface for publishing real-time match events."""

    @abstractmethod
    async def publish(self, match_id: str, event: dict) -> None:
        ...

    @abstractmethod
    async def subscribe(self, match_id: str):
        ...
