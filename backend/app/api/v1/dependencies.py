from fastapi import Depends
from app.services.match_service import MatchService
from app.infra.db.match_repository import PostgresMatchRepository
from app.infra.cache.redis_publisher import RedisMatchEventPublisher
from app.infra.db.session import get_db_session
from app.infra.cache.redis import get_redis


async def get_match_service(
    db=Depends(get_db_session),
    redis=Depends(get_redis),
) -> MatchService:
    repo = PostgresMatchRepository(db)
    publisher = RedisMatchEventPublisher(redis)
    return MatchService(repository=repo, publisher=publisher)
