-- Migration 009: Team form stats + prediction features
-- Provides the foundation for the ML predictive model

-- Team performance aggregates (updated after each match)
CREATE TABLE IF NOT EXISTS team_form (
    team_id         TEXT PRIMARY KEY REFERENCES teams(id),
    team_name       TEXT NOT NULL,
    played          INTEGER DEFAULT 0,
    wins            INTEGER DEFAULT 0,
    draws           INTEGER DEFAULT 0,
    losses          INTEGER DEFAULT 0,
    goals_for       INTEGER DEFAULT 0,
    goals_against   INTEGER DEFAULT 0,
    goal_diff       INTEGER GENERATED ALWAYS AS (goals_for - goals_against) STORED,
    points          INTEGER GENERATED ALWAYS AS (wins * 3 + draws) STORED,
    -- Recent form (last 5): W=3, D=1, L=0
    form_last5      TEXT DEFAULT '',        -- e.g. "WWDLW"
    form_points5    INTEGER DEFAULT 0,      -- max 15
    -- Attack/Defense ratings (0-100)
    attack_rating   NUMERIC(5,2) DEFAULT 50.0,
    defense_rating  NUMERIC(5,2) DEFAULT 50.0,
    -- Averages per game
    avg_goals_for   NUMERIC(4,2) DEFAULT 0.0,
    avg_goals_against NUMERIC(4,2) DEFAULT 0.0,
    avg_shots       NUMERIC(5,2) DEFAULT 0.0,
    avg_shots_on_target NUMERIC(5,2) DEFAULT 0.0,
    avg_possession  NUMERIC(5,2) DEFAULT 50.0,
    avg_corners     NUMERIC(4,2) DEFAULT 0.0,
    avg_fouls       NUMERIC(4,2) DEFAULT 0.0,
    clean_sheets    INTEGER DEFAULT 0,
    -- xG model
    xg_scored_avg   NUMERIC(5,3) DEFAULT 0.0,
    xg_conceded_avg NUMERIC(5,3) DEFAULT 0.0,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Per-match stats enrichment (from API-Football or calculated)
CREATE TABLE IF NOT EXISTS match_stats_enriched (
    match_id            TEXT PRIMARY KEY REFERENCES matches(id),
    -- Shots
    shots_home          INTEGER DEFAULT 0,
    shots_away          INTEGER DEFAULT 0,
    shots_on_target_home INTEGER DEFAULT 0,
    shots_on_target_away INTEGER DEFAULT 0,
    shots_blocked_home  INTEGER DEFAULT 0,
    shots_blocked_away  INTEGER DEFAULT 0,
    -- Possession
    possession_home     NUMERIC(5,2) DEFAULT 50.0,
    possession_away     NUMERIC(5,2) DEFAULT 50.0,
    -- Set pieces
    corners_home        INTEGER DEFAULT 0,
    corners_away        INTEGER DEFAULT 0,
    offsides_home       INTEGER DEFAULT 0,
    offsides_away       INTEGER DEFAULT 0,
    -- Fouls & cards
    fouls_home          INTEGER DEFAULT 0,
    fouls_away          INTEGER DEFAULT 0,
    yellow_cards_home   INTEGER DEFAULT 0,
    yellow_cards_away   INTEGER DEFAULT 0,
    red_cards_home      INTEGER DEFAULT 0,
    red_cards_away      INTEGER DEFAULT 0,
    -- Expected Goals
    xg_home             NUMERIC(6,3) DEFAULT 0.0,
    xg_away             NUMERIC(6,3) DEFAULT 0.0,
    -- Passing
    passes_home         INTEGER DEFAULT 0,
    passes_away         INTEGER DEFAULT 0,
    pass_accuracy_home  NUMERIC(5,2) DEFAULT 0.0,
    pass_accuracy_away  NUMERIC(5,2) DEFAULT 0.0,
    -- Source tracking
    data_source         TEXT DEFAULT 'calculated',  -- 'api_football' | 'calculated'
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Prediction features table (pre-computed for ML model)
CREATE TABLE IF NOT EXISTS prediction_features (
    match_id                TEXT PRIMARY KEY REFERENCES matches(id),
    -- Team strengths at time of match
    home_attack_rating      NUMERIC(5,2),
    home_defense_rating     NUMERIC(5,2),
    away_attack_rating      NUMERIC(5,2),
    away_defense_rating     NUMERIC(5,2),
    -- Form
    home_form_points5       INTEGER,
    away_form_points5       INTEGER,
    home_played             INTEGER,
    away_played             INTEGER,
    -- Average goals
    home_avg_goals_for      NUMERIC(4,2),
    home_avg_goals_against  NUMERIC(4,2),
    away_avg_goals_for      NUMERIC(4,2),
    away_avg_goals_against  NUMERIC(4,2),
    -- xG projection
    expected_home_goals     NUMERIC(5,3),
    expected_away_goals     NUMERIC(5,3),
    -- Win probability (0-1)
    prob_home_win           NUMERIC(5,4) DEFAULT 0.333,
    prob_draw               NUMERIC(5,4) DEFAULT 0.333,
    prob_away_win           NUMERIC(5,4) DEFAULT 0.334,
    -- Actual outcome (filled after match)
    actual_home_goals       INTEGER,
    actual_away_goals       INTEGER,
    actual_outcome          TEXT,  -- 'HOME_WIN' | 'DRAW' | 'AWAY_WIN'
    -- Model metadata
    model_version           TEXT DEFAULT 'v1_elo_form',
    computed_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Head-to-head records
CREATE TABLE IF NOT EXISTS head_to_head (
    id              SERIAL PRIMARY KEY,
    home_team_id    TEXT REFERENCES teams(id),
    away_team_id    TEXT REFERENCES teams(id),
    match_id        TEXT REFERENCES matches(id),
    home_goals      INTEGER,
    away_goals      INTEGER,
    outcome         TEXT,  -- 'HOME_WIN' | 'DRAW' | 'AWAY_WIN'
    played_at       TIMESTAMPTZ,
    UNIQUE(home_team_id, away_team_id, match_id)
);

-- Group standings view
CREATE OR REPLACE VIEW group_standings AS
SELECT
    t.id            AS team_id,
    t.name          AS team_name,
    m.group,
    tf.played,
    tf.wins,
    tf.draws,
    tf.losses,
    tf.goals_for,
    tf.goals_against,
    tf.goal_diff,
    tf.points,
    tf.form_last5,
    tf.attack_rating,
    tf.defense_rating
FROM team_form tf
JOIN teams t ON tf.team_id = t.id
JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
WHERE m.group IS NOT NULL
GROUP BY t.id, t.name, m.group, tf.played, tf.wins, tf.draws, tf.losses,
         tf.goals_for, tf.goals_against, tf.goal_diff, tf.points, tf.form_last5,
         tf.attack_rating, tf.defense_rating
ORDER BY m.group, tf.points DESC, tf.goal_diff DESC;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_team_form_points ON team_form(points DESC);
CREATE INDEX IF NOT EXISTS idx_match_stats_source ON match_stats_enriched(data_source);
CREATE INDEX IF NOT EXISTS idx_h2h_teams ON head_to_head(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_prediction_match ON prediction_features(match_id);
