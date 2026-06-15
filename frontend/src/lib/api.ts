import { Match } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    next: { revalidate: 0 }, // always fresh
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
