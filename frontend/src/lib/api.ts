import { Match } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    next: { revalidate: 0 },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

export async function getMatches(liveOnly = false): Promise<Match[]> {
  const qs = liveOnly ? "?live_only=true" : "";
  const data = await apiFetch<{ matches: Match[]; total: number }>(`/matches${qs}`);
  return data.matches;
}

export async function getMatch(id: string): Promise<Match> {
  return apiFetch<Match>(`/matches/${id}`);
}

export async function getTimeline(id: string) {
  return apiFetch<{ match_id: string; events: unknown[] }>(`/matches/${id}/timeline`);
}

export async function getPredictions(id: string) {
  return apiFetch(`/predictions/${id}`);
}

export interface MatchStats {
  match_id: string;
  shots_home: number;
  shots_away: number;
  shots_on_target_home: number;
  shots_on_target_away: number;
  shots_blocked_home: number;
  shots_blocked_away: number;
  possession_home: number;
  possession_away: number;
  corners_home: number;
  corners_away: number;
  offsides_home: number;
  offsides_away: number;
  fouls_home: number;
  fouls_away: number;
  yellow_cards_home: number;
  yellow_cards_away: number;
  red_cards_home: number;
  red_cards_away: number;
  passes_home: number;
  passes_away: number;
  pass_accuracy_home: number;
  pass_accuracy_away: number;
  xg_home: number;
  xg_away: number;
  data_source: string;
}

export interface TeamForm {
  team_id: string;
  team_name: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  form_last5: string;
  attack_rating: number;
  defense_rating: number;
  avg_goals_for: number;
  avg_goals_against: number;
  avg_shots: number;
  avg_possession: number;
  clean_sheets: number;
  xg_scored_avg: number;
  xg_conceded_avg: number;
}

export interface Prediction {
  match_id: string;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  predicted_goals_home: number;
  predicted_goals_away: number;
  home_attack_rating: number;
  away_attack_rating: number;
  home_form: string;
  away_form: string;
  model_version: string;
  confidence: number;
}

export async function getMatchStats(id: string): Promise<MatchStats | null> {
  try {
    return await apiFetch<MatchStats>(`/stats/matches/${id}`);
  } catch {
    return null;
  }
}

export async function getTeamForm(teamId: string): Promise<TeamForm | null> {
  try {
    return await apiFetch<TeamForm>(`/stats/teams/${teamId}`);
  } catch {
    return null;
  }
}

export async function getMatchPrediction(id: string): Promise<Prediction | null> {
  try {
    return await apiFetch<Prediction>(`/predictions/${id}`);
  } catch {
    return null;
  }
}

export interface StandingsEntry {
  team_id: string;
  team_name: string;
  group: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  form_last5: string;
  attack_rating: number;
  defense_rating: number;
}

export async function getStandings(): Promise<Record<string, StandingsEntry[]>> {
  try {
    const data = await apiFetch<{ standings: Record<string, StandingsEntry[]> }>("/stats/standings");
    return data.standings;
  } catch {
    return {};
  }
}

