from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from app.infra.db.session import AsyncSessionLocal

router = APIRouter()


class PredictionResponse(BaseModel):
    match_id: str
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    predicted_goals_home: float
    predicted_goals_away: float
    home_attack_rating: float
    away_attack_rating: float
    home_form: str
    away_form: str
    model_version: str
    confidence: float


@router.get("/{match_id}", response_model=PredictionResponse)
async def get_predictions(match_id: str):
    """
    ML predictions for a match: win/draw/loss probabilities + expected goals.
    Uses ELO ratings + Dixon-Coles Poisson model.
    """
    async with AsyncSessionLocal() as db:
        # Try prediction features table
        result = await db.execute(
            text("SELECT * FROM prediction_features WHERE match_id = :mid"),
            {"mid": match_id},
        )
        pred = result.mappings().one_or_none()

        # Get match details for team IDs
        m_result = await db.execute(
            text("SELECT home_team_id, away_team_id FROM matches WHERE id = :mid"),
            {"mid": match_id},
        )
        match = m_result.mappings().one_or_none()

        home_form = ""
        away_form = ""
        if match:
            tf_h = await db.execute(
                text("SELECT form_last5 FROM team_form WHERE team_id = :tid"),
                {"tid": match["home_team_id"]},
            )
            tf_a = await db.execute(
                text("SELECT form_last5 FROM team_form WHERE team_id = :tid"),
                {"tid": match["away_team_id"]},
            )
            rh = tf_h.mappings().one_or_none()
            ra = tf_a.mappings().one_or_none()
            home_form = rh["form_last5"] if rh else ""
            away_form = ra["form_last5"] if ra else ""

        if pred:
            p = dict(pred)
            confidence = min(0.95, 0.5 + abs(p["prob_home_win"] - p["prob_away_win"]) * 1.2)
            return PredictionResponse(
                match_id=match_id,
                home_win_prob=p["prob_home_win"],
                draw_prob=p["prob_draw"],
                away_win_prob=p["prob_away_win"],
                predicted_goals_home=p.get("expected_home_goals", 1.2),
                predicted_goals_away=p.get("expected_away_goals", 1.0),
                home_attack_rating=p.get("home_attack_rating", 50.0),
                away_attack_rating=p.get("away_attack_rating", 50.0),
                home_form=home_form,
                away_form=away_form,
                model_version="v1_elo_poisson",
                confidence=round(confidence, 3),
            )

    # Fallback: equal probabilities
    return PredictionResponse(
        match_id=match_id,
        home_win_prob=0.333,
        draw_prob=0.333,
        away_win_prob=0.334,
        predicted_goals_home=1.2,
        predicted_goals_away=1.0,
        home_attack_rating=50.0,
        away_attack_rating=50.0,
        home_form="",
        away_form="",
        model_version="v1_elo_poisson",
        confidence=0.5,
    )

