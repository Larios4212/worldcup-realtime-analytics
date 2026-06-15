from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class PredictionResponse(BaseModel):
    match_id: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_goals_home: float
    predicted_goals_away: float
    model_version: str
    confidence: float


@router.get("/{match_id}", response_model=PredictionResponse)
async def get_predictions(match_id: str):
    """
    Get ML-powered predictions for a match.
    
    Returns win/draw/loss probabilities and expected goals
    based on historical data and current match form.
    """
    # TODO: wire to ML service
    return PredictionResponse(
        match_id=match_id,
        home_win_prob=0.45,
        draw_prob=0.28,
        away_win_prob=0.27,
        predicted_goals_home=1.4,
        predicted_goals_away=1.1,
        model_version="v1.0.0",
        confidence=0.72,
    )
