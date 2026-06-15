export interface Team {
  id: string;
  name: string;
  short_name: string;
  crest_url?: string;
}

export interface Score {
  home: number;
  away: number;
  home_ht?: number;
  away_ht?: number;
}

export interface MatchStats {
  possession_home: number;
  possession_away: number;
  shots_home: number;
  shots_away: number;
  shots_on_target_home: number;
  shots_on_target_away: number;
  xg_home: number;
  xg_away: number;
  passes_home: number;
  passes_away: number;
  fouls_home: number;
  fouls_away: number;
  corners_home: number;
  corners_away: number;
}

export type MatchStatus = "SCHEDULED" | "LIVE" | "HALFTIME" | "FINISHED" | "POSTPONED";

export type EventType =
  | "GOAL"
  | "OWN_GOAL"
  | "YELLOW_CARD"
  | "RED_CARD"
  | "SUBSTITUTION"
  | "PENALTY"
  | "VAR"
  | "KICK_OFF"
  | "HALF_TIME"
  | "FULL_TIME"
  | "STATS_UPDATE";

export interface MatchEvent {
  id: string;
  match_id: string;
  event_type: EventType;
  minute: number;
  team_id: string;
  player_name?: string;
  description?: string;
  timestamp: string;
}

export interface Match {
  id: string;
  home_team: Team;
  away_team: Team;
  status: MatchStatus;
  kickoff_utc: string;
  score: Score;
  stats: MatchStats;
  minute?: number;
  stage: string;
  group?: string;
  venue?: string;
}

export interface WsMessage {
  type: EventType | "PING" | "STATS_UPDATE";
  match_id: string;
  minute?: number;
  score?: Score;
  stats?: Partial<MatchStats>;
  player?: string;
  team_id?: string;
  description?: string;
  timestamp?: string;
  status?: MatchStatus;
}
