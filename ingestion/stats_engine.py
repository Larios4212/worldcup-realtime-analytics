"""
Calculated stats engine.
Derives match statistics from available data when external API is not available.
Uses:
- Goals scored to estimate shots (10-14 shots per goal, avg ~12)
- Match outcome to estimate possession
- ELO-style ratings for team strength
- Dixon-Coles Poisson model for goal expectation
"""
import math
from typing import Optional


# ──────────────────────────────────────────────────
# Constants (calibrated from World Cup 2022 data)
# ──────────────────────────────────────────────────
AVG_SHOTS_PER_GOAL = 7.5        # A 2-goal game = ~15 shots, realistic
AVG_SHOTS_ON_TARGET_RATE = 0.40  # 40% of shots on target
AVG_CORNERS_PER_SHOT = 0.38     # Corners per shot attempt
AVG_FOULS_PER_GAME = 22.0       # Total fouls per game (both teams)
AVG_POSSESSION_WINNER = 54.0    # Winning team avg possession
AVG_POSSESSION_DRAW = 50.0      # Draw avg possession
AVG_PASSES_PER_GAME = 450       # Per team per game
BASE_PASS_ACCURACY = 82.0       # Base pass accuracy %


def estimate_match_stats(
    home_goals: int,
    away_goals: int,
    home_attack_rating: float = 50.0,
    away_attack_rating: float = 50.0,
    home_defense_rating: float = 50.0,
    away_defense_rating: float = 50.0,
    seed: int = 0,
) -> dict:
    """
    Estimate match statistics from goals and team ratings.
    Returns stats in the same format as API-Football enricher.
    """
    # Determine outcome
    if home_goals > away_goals:
        winner = "home"
    elif away_goals > home_goals:
        winner = "away"
    else:
        winner = "draw"

    # ── Possession ──────────────────────────────────────────────────
    rating_diff = (home_attack_rating - away_attack_rating) / 100.0
    if winner == "home":
        possession_home = min(70, max(40, AVG_POSSESSION_WINNER + rating_diff * 10))
    elif winner == "away":
        possession_home = min(60, max(30, (100 - AVG_POSSESSION_WINNER) + rating_diff * 10))
    else:
        possession_home = min(65, max(35, AVG_POSSESSION_DRAW + rating_diff * 8))
    possession_away = 100.0 - possession_home

    # ── Shots ────────────────────────────────────────────────────────
    # Base shots: goals * conversion_factor + pressure from attack rating
    # Add a minimum floor even for 0-goal teams (they still shoot)
    home_base_shots = max(4, round(
        home_goals * AVG_SHOTS_PER_GOAL +
        (home_attack_rating / 100) * 5 +
        _deterministic_noise(seed, 1, -2, 4)
    ))
    away_base_shots = max(2, round(
        away_goals * AVG_SHOTS_PER_GOAL +
        (away_attack_rating / 100) * 4 +
        _deterministic_noise(seed, 2, -2, 4)
    ))
    # Cap at realistic maximum (30 shots in a game is elite-level domination)
    home_shots = min(28, home_base_shots)
    away_shots = min(22, away_base_shots)

    # On target rate (higher for winning team)
    home_on_target_rate = AVG_SHOTS_ON_TARGET_RATE + (0.05 if winner == "home" else -0.03)
    away_on_target_rate = AVG_SHOTS_ON_TARGET_RATE + (0.05 if winner == "away" else -0.03)

    home_on_target = max(home_goals, round(home_shots * home_on_target_rate))
    away_on_target = max(away_goals, round(away_shots * away_on_target_rate))

    # Blocked shots
    home_blocked = max(0, round((home_shots - home_on_target) * 0.4))
    away_blocked = max(0, round((away_shots - away_on_target) * 0.4))

    # ── Corners ──────────────────────────────────────────────────────
    home_corners = max(2, round(home_shots * AVG_CORNERS_PER_SHOT + _deterministic_noise(seed, 3, -1, 3)))
    away_corners = max(1, round(away_shots * AVG_CORNERS_PER_SHOT + _deterministic_noise(seed, 4, -1, 3)))

    # ── Fouls ────────────────────────────────────────────────────────
    total_fouls = round(AVG_FOULS_PER_GAME + _deterministic_noise(seed, 5, -4, 6))
    # Losing team fouls more
    if winner == "home":
        home_fouls = max(5, round(total_fouls * 0.42))
        away_fouls = max(5, total_fouls - home_fouls)
    elif winner == "away":
        away_fouls = max(5, round(total_fouls * 0.42))
        home_fouls = max(5, total_fouls - away_fouls)
    else:
        home_fouls = max(5, round(total_fouls / 2))
        away_fouls = max(5, total_fouls - home_fouls)

    # ── Cards (from fouls) ────────────────────────────────────────────
    home_yellows = max(0, round(home_fouls * 0.18 + _deterministic_noise(seed, 6, 0, 2)))
    away_yellows = max(0, round(away_fouls * 0.18 + _deterministic_noise(seed, 7, 0, 2)))
    # Red cards are rare (avg ~0.15 per team per game at World Cup)
    home_reds = 1 if _deterministic_noise(seed, 8, 0, 10) > 8 else 0
    away_reds = 1 if _deterministic_noise(seed, 9, 0, 10) > 8 else 0

    # ── Offsides ──────────────────────────────────────────────────────
    home_offsides = max(0, round(home_shots * 0.15 + _deterministic_noise(seed, 10, 0, 2)))
    away_offsides = max(0, round(away_shots * 0.15 + _deterministic_noise(seed, 11, 0, 2)))

    # ── Passes ────────────────────────────────────────────────────────
    home_passes = max(200, round(
        AVG_PASSES_PER_GAME * (possession_home / 50) +
        _deterministic_noise(seed, 12, -20, 30)
    ))
    away_passes = max(150, round(
        AVG_PASSES_PER_GAME * (possession_away / 50) +
        _deterministic_noise(seed, 13, -20, 30)
    ))
    home_pass_acc = min(95, max(65, round(BASE_PASS_ACCURACY + (possession_home - 50) * 0.2)))
    away_pass_acc = min(95, max(65, round(BASE_PASS_ACCURACY + (possession_away - 50) * 0.2)))

    # ── xG ────────────────────────────────────────────────────────────
    # Realistic xG: shots on target * avg quality + goals bonus
    # World Cup avg xG per game: ~1.0-1.5 per team
    home_xg = round(home_on_target * 0.18 + home_goals * 0.4, 3)
    away_xg = round(away_on_target * 0.18 + away_goals * 0.4, 3)

    return {
        "shots_home": home_shots,
        "shots_away": away_shots,
        "shots_on_target_home": home_on_target,
        "shots_on_target_away": away_on_target,
        "shots_blocked_home": home_blocked,
        "shots_blocked_away": away_blocked,
        "possession_home": round(possession_home, 1),
        "possession_away": round(possession_away, 1),
        "corners_home": home_corners,
        "corners_away": away_corners,
        "offsides_home": home_offsides,
        "offsides_away": away_offsides,
        "fouls_home": home_fouls,
        "fouls_away": away_fouls,
        "yellow_cards_home": home_yellows,
        "yellow_cards_away": away_yellows,
        "red_cards_home": home_reds,
        "red_cards_away": away_reds,
        "passes_home": home_passes,
        "passes_away": away_passes,
        "pass_accuracy_home": float(home_pass_acc),
        "pass_accuracy_away": float(away_pass_acc),
        "xg_home": home_xg,
        "xg_away": away_xg,
        "data_source": "calculated",
    }


def _deterministic_noise(seed: int, factor: int, low: int, high: int) -> int:
    """Deterministic pseudo-random noise based on seed (same match always same stats)."""
    val = (seed * 2654435761 + factor * 40503) & 0xFFFFFFFF
    range_size = high - low
    if range_size <= 0:
        return low
    return low + (val % (range_size + 1))


# ──────────────────────────────────────────────────
# ELO-based win probability model
# ──────────────────────────────────────────────────
ELO_K = 32          # K-factor (sensitivity)
ELO_BASE = 1000     # Starting ELO

def expected_score(elo_a: float, elo_b: float) -> float:
    """Expected score for team A vs team B (0-1)."""
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))


def update_elo(elo_a: float, elo_b: float, score_a: float) -> tuple[float, float]:
    """Update ELO ratings after a match. score_a: 1=win, 0.5=draw, 0=loss."""
    exp_a = expected_score(elo_a, elo_b)
    exp_b = 1 - exp_a
    new_a = elo_a + ELO_K * (score_a - exp_a)
    new_b = elo_b + ELO_K * ((1 - score_a) - exp_b)
    return new_a, new_b


def calculate_win_probabilities(
    home_elo: float,
    away_elo: float,
    home_avg_goals: float,
    away_avg_goals: float,
    home_form_points: int = 7,
    away_form_points: int = 7,
) -> tuple[float, float, float]:
    """
    Calculate win/draw/loss probabilities using ELO + Poisson model.
    Returns (prob_home_win, prob_draw, prob_away_win).
    """
    # ELO probability adjustment
    elo_diff = home_elo - away_elo
    elo_factor = 1 / (1 + 10 ** (-elo_diff / 400))  # 0-1

    # Form adjustment
    form_factor = (home_form_points - away_form_points) / 30.0  # -0.5 to +0.5

    # Expected goals using Poisson
    lambda_home = max(0.1, home_avg_goals * (1 + form_factor * 0.3))
    lambda_away = max(0.1, away_avg_goals * (1 - form_factor * 0.3))

    # Poisson probabilities (max 6 goals each)
    p_home_win = 0.0
    p_draw = 0.0
    p_away_win = 0.0

    for h in range(7):
        for a in range(7):
            p = poisson_pmf(lambda_home, h) * poisson_pmf(lambda_away, a)
            if h > a:
                p_home_win += p
            elif h == a:
                p_draw += p
            else:
                p_away_win += p

    # Blend with ELO
    alpha = 0.6  # Weight for Poisson vs ELO
    p_home_elo = elo_factor * 0.7 + 0.15  # rough win probability from ELO
    p_away_elo = (1 - elo_factor) * 0.7 + 0.15
    p_draw_base = 1 - p_home_elo - p_away_elo

    p_home_final = alpha * p_home_win + (1 - alpha) * p_home_elo
    p_away_final = alpha * p_away_win + (1 - alpha) * p_away_elo
    p_draw_final = max(0.05, 1 - p_home_final - p_away_final)

    # Normalize
    total = p_home_final + p_draw_final + p_away_final
    return (
        round(p_home_final / total, 4),
        round(p_draw_final / total, 4),
        round(p_away_final / total, 4),
    )


def poisson_pmf(lam: float, k: int) -> float:
    """Poisson probability mass function P(X=k)."""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)
