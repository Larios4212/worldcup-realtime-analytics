from fastapi import APIRouter
from app.api.v1.endpoints import matches, websockets, stats, predictions, internal

api_router = APIRouter()

api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(websockets.router, prefix="/ws", tags=["websockets"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
