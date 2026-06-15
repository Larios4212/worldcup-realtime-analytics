-- World Cup Realtime Analytics — Database Schema
-- Requires TimescaleDB extension for time-series optimization

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    short_name  TEXT NOT NULL,
    crest_url   TEXT,
    "group"     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Matches
CREATE TABLE IF NOT EXISTS matches (
    id                      TEXT PRIMARY KEY,
    home_team_id            TEXT REFERENCES teams(id),
    away_team_id            TEXT REFERENCES teams(id),
    status                  TEXT NOT NULL DEFAULT 'SCHEDULED',
    kickoff_utc             TIMESTAMPTZ NOT NULL,
    score_home              INTEGER DEFAULT 0,
    score_away              INTEGER DEFAULT 0,
    score_home_ht           INTEGER,
    score_away_ht           INTEGER,
    minute                  INTEGER,
    stage                   TEXT DEFAULT 'Group Stage',
    "group"                 TEXT,
    venue                   TEXT,
    -- Live stats
    possession_home         NUMERIC(5,2) DEFAULT 50.0,
    possession_away         NUMERIC(5,2) DEFAULT 50.0,
    shots_home              INTEGER DEFAULT 0,
    shots_away              INTEGER DEFAULT 0,
    shots_on_target_home    INTEGER DEFAULT 0,
    shots_on_target_away    INTEGER DEFAULT 0,
    xg_home                 NUMERIC(6,3) DEFAULT 0.0,
    xg_away                 NUMERIC(6,3) DEFAULT 0.0,
    passes_home             INTEGER DEFAULT 0,
    passes_away             INTEGER DEFAULT 0,
    pass_accuracy_home      NUMERIC(5,2) DEFAULT 0.0,
    pass_accuracy_away      NUMERIC(5,2) DEFAULT 0.0,
    fouls_home              INTEGER DEFAULT 0,
    fouls_away              INTEGER DEFAULT 0,
    corners_home            INTEGER DEFAULT 0,
    corners_away            INTEGER DEFAULT 0,
    offsides_home           INTEGER DEFAULT 0,
    offsides_away           INTEGER DEFAULT 0,
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Match Events (time-series hypertable)
CREATE TABLE IF NOT EXISTS match_events (
    id          TEXT,
    match_id    TEXT REFERENCES matches(id),
    event_type  TEXT NOT NULL,
    minute      INTEGER NOT NULL,
    team_id     TEXT NOT NULL,
    player_name TEXT,
    player_in_name TEXT,
    description TEXT,
    timestamp   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- Convert to TimescaleDB hypertable for efficient time-series queries
SELECT create_hypertable('match_events', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_kickoff ON matches(kickoff_utc);
CREATE INDEX IF NOT EXISTS idx_events_match_id ON match_events(match_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON match_events(event_type);
