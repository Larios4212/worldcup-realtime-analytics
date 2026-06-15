from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.api.v1.schemas import MatchResponse, MatchListResponse, TimelineResponse
from app.services.match_service import MatchService
from app.api.v1.dependencies import get_match_service

router = APIRouter()


@router.get("/", response_model=MatchListResponse)
async def list_matches(
    stage: Optional[str] = Query(None, description="Filter by stage (e.g. 'Group Stage', 'Round of 16')"),
    live_only: bool = Query(False, description="Return only live matches"),
    service: MatchService = Depends(get_match_service),
):
    """List all World Cup matches, optionally filtered."""
    if live_only:
        matches = await service.list_live_matches()
    else:
        matches = await service.list_matches(stage=stage)
    return MatchListResponse(matches=matches, total=len(matches))


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    service: MatchService = Depends(get_match_service),
):
    """Get a specific match with live stats."""
    match = await service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    return match


@router.get("/{match_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    match_id: str,
    service: MatchService = Depends(get_match_service),
):
    """Get the full event timeline for a match."""
    match = await service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")
    events = await service.get_timeline(match_id)
    return TimelineResponse(match_id=match_id, events=events)
