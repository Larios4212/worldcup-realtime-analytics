"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Header } from "@/components/Header";
import { MatchCard } from "@/components/MatchCard";
import { StatsGrid } from "@/components/StatsGrid";
import { EventFeed } from "@/components/EventFeed";
import { XGChart } from "@/components/XGChart";
import { FootballPitch } from "@/components/FootballPitch";
import { PossessionBar } from "@/components/PossessionBar";
import { useMatchWebSocket } from "@/hooks/useMatchWebSocket";
import { Match } from "@/types";
import { formatMinute } from "@/lib/utils";
import { getMatches } from "@/lib/api";

// ── Static mock (no Date.now() = no hydration mismatch) ──────────────────────
const STATIC_MOCK: Match[] = [
  {
    id: "m1",
    home_team: { id: "bra", name: "Brazil", short_name: "BRA" },
    away_team: { id: "arg", name: "Argentina", short_name: "ARG" },
    status: "LIVE", kickoff_utc: "2026-06-15T20:00:00Z", minute: 67,
    stage: "Quarter-Final", venue: "MetLife Stadium, New Jersey",
    score: { home: 1, away: 2 },
    stats: { possession_home: 42, possession_away: 58, shots_home: 8, shots_away: 14,
      shots_on_target_home: 3, shots_on_target_away: 6, xg_home: 0.87, xg_away: 2.14,
      passes_home: 312, passes_away: 445, fouls_home: 11, fouls_away: 8,
      corners_home: 3, corners_away: 7 },
  },
  {
    id: "m2",
    home_team: { id: "fra", name: "France", short_name: "FRA" },
    away_team: { id: "esp", name: "Spain", short_name: "ESP" },
    status: "LIVE", kickoff_utc: "2026-06-15T17:00:00Z", minute: 34,
    stage: "Quarter-Final", venue: "AT&T Stadium, Dallas",
    score: { home: 0, away: 1 },
    stats: { possession_home: 55, possession_away: 45, shots_home: 6, shots_away: 9,
      shots_on_target_home: 2, shots_on_target_away: 4, xg_home: 0.62, xg_away: 1.31,
      passes_home: 398, passes_away: 324, fouls_home: 6, fouls_away: 9,
      corners_home: 5, corners_away: 2 },
  },
  {
    id: "m3",
    home_team: { id: "eng", name: "England", short_name: "ENG" },
    away_team: { id: "ger", name: "Germany", short_name: "GER" },
    status: "SCHEDULED", kickoff_utc: "2026-06-15T23:00:00Z",
    stage: "Quarter-Final", venue: "SoFi Stadium, Los Angeles",
    score: { home: 0, away: 0 },
    stats: { possession_home: 50, possession_away: 50, shots_home: 0, shots_away: 0,
      shots_on_target_home: 0, shots_on_target_away: 0, xg_home: 0, xg_away: 0,
      passes_home: 0, passes_away: 0, fouls_home: 0, fouls_away: 0,
      corners_home: 0, corners_away: 0 },
  },
  {
    id: "m4",
    home_team: { id: "por", name: "Portugal", short_name: "POR" },
    away_team: { id: "ned", name: "Netherlands", short_name: "NED" },
    status: "FINISHED", kickoff_utc: "2026-06-15T14:00:00Z",
    stage: "Round of 16", venue: "Levi's Stadium, San Francisco",
    score: { home: 3, away: 2, home_ht: 1, away_ht: 0 },
    stats: { possession_home: 48, possession_away: 52, shots_home: 17, shots_away: 12,
      shots_on_target_home: 7, shots_on_target_away: 5, xg_home: 2.87, xg_away: 1.54,
      passes_home: 421, passes_away: 478, fouls_home: 14, fouls_away: 16,
      corners_home: 8, corners_away: 5 },
  },
];

const XG_MOCK = Array.from({ length: 19 }, (_, i) => ({
  minute: i * 5,
  xg_home: parseFloat(((i * 0.048) + (i % 3 === 0 ? 0.12 : 0)).toFixed(3)),
  xg_away: parseFloat(((i * 0.072) + (i % 4 === 0 ? 0.18 : 0)).toFixed(3)),
}));

// ── Match detail ─────────────────────────────────────────────────────────────
function MatchDetailPanel({ match }: { match: Match }) {
  const { messages, connected } = useMatchWebSocket(match.id);
  const isLive = match.status === "LIVE" || match.status === "HALFTIME";
  const liveScore = messages.find((m) => m.score)?.score ?? match.score;
  const latestStats = messages.find((m) => m.stats)?.stats;
  const currentStats = latestStats ? { ...match.stats, ...latestStats } : match.stats;

  return (
    <motion.div key={match.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.4 }}
      className="h-full flex flex-col gap-4 overflow-y-auto pr-1">

      {/* Hero */}
      <div className="glass rounded-xl p-6 relative overflow-hidden flex-shrink-0">
        {isLive && (
          <motion.div className="absolute inset-0 pointer-events-none"
            animate={{ background: [
              "radial-gradient(ellipse at 20% 50%, rgba(0,212,255,0.04), transparent 70%)",
              "radial-gradient(ellipse at 80% 50%, rgba(0,255,135,0.04), transparent 70%)",
              "radial-gradient(ellipse at 20% 50%, rgba(0,212,255,0.04), transparent 70%)",
            ]}} transition={{ duration: 6, repeat: Infinity }} />
        )}

        <div className="flex items-center justify-between mb-5">
          <div>
            <p className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--accent-green)" }}>
              {match.stage}
            </p>
            {match.venue && (
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>📍 {match.venue}</p>
            )}
          </div>
          {isLive ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
              style={{ background: "rgba(255,71,87,0.1)", border: "1px solid rgba(255,71,87,0.25)" }}>
              <span className="live-dot" />
              <span className="text-xs font-mono font-bold" style={{ color: "var(--live-pulse)" }}>
                {match.status === "HALFTIME" ? "HALF TIME" : `${formatMinute(match.minute ?? null)} LIVE`}
              </span>
            </div>
          ) : match.status === "FINISHED" ? (
            <span className="text-xs font-mono px-2 py-1 rounded"
              style={{ background: "var(--bg-elevated)", color: "var(--text-muted)" }}>FULL TIME</span>
          ) : (
            <span className="text-xs font-mono px-2 py-1 rounded"
              style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}>UPCOMING</span>
          )}
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1 text-right">
            <p className="text-4xl font-black" style={{ color: "var(--accent-cyan)" }}>
              {match.home_team.short_name}
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{match.home_team.name}</p>
          </div>

          <div className="flex flex-col items-center gap-1 min-w-[100px]">
            <div className="flex items-center gap-3">
              <motion.span key={`h-${liveScore.home}`} className="text-6xl font-mono font-black tabular-nums"
                style={{ color: "var(--text-primary)" }}
                animate={isLive ? { scale: [1, 1.08, 1] } : {}} transition={{ duration: 0.3 }}>
                {liveScore.home}
              </motion.span>
              <span className="text-3xl font-mono" style={{ color: "rgba(255,255,255,0.1)" }}>–</span>
              <motion.span key={`a-${liveScore.away}`} className="text-6xl font-mono font-black tabular-nums"
                style={{ color: "var(--text-primary)" }}
                animate={isLive ? { scale: [1, 1.08, 1] } : {}} transition={{ duration: 0.3 }}>
                {liveScore.away}
              </motion.span>
            </div>
            {match.score.home_ht !== undefined && (
              <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                HT {match.score.home_ht}–{match.score.away_ht}
              </p>
            )}
          </div>

          <div className="flex-1">
            <p className="text-4xl font-black" style={{ color: "var(--accent-green)" }}>
              {match.away_team.short_name}
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{match.away_team.name}</p>
          </div>
        </div>

        <div className="mt-5">
          <PossessionBar home={currentStats.possession_home} away={currentStats.possession_away}
            homeTeam={match.home_team.short_name} awayTeam={match.away_team.short_name} />
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-shrink-0">
        <div className="glass rounded-xl p-4">
          <XGChart data={XG_MOCK} homeTeam={match.home_team.short_name} awayTeam={match.away_team.short_name} />
        </div>
        <div className="glass rounded-xl p-4 flex flex-col items-center gap-2">
          <p className="text-xs font-mono uppercase tracking-widest w-full" style={{ color: "var(--text-muted)" }}>
            PITCH VIEW
          </p>
          <FootballPitch className="w-full max-w-xs" />
        </div>
      </div>

      {/* Stats + Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass rounded-xl p-4">
          <StatsGrid stats={currentStats}
            homeTeam={match.home_team.short_name} awayTeam={match.away_team.short_name} />
        </div>
        <div className="glass rounded-xl p-4">
          <EventFeed events={messages} />
        </div>
      </div>

      <div className="flex items-center gap-2 pb-4 flex-shrink-0">
        <div className="w-1.5 h-1.5 rounded-full"
          style={{ background: connected ? "var(--accent-green)" : "var(--accent-red)" }} />
        <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
          {connected ? "Connected · live stream active" : "Reconnecting to stream..."}
        </span>
      </div>
    </motion.div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [matches, setMatches] = useState<Match[]>([]);          // empty on SSR → no hydration mismatch
  const [selectedId, setSelectedId] = useState<string>("");
  const [filter, setFilter] = useState<"all" | "live" | "finished" | "scheduled">("all");
  const [isLoading, setIsLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  const loadMatches = useCallback(async () => {
    try {
      const data = await getMatches();
      if (data.length > 0) {
        setMatches(data);
        setUsingMock(false);
        if (!selectedId) setSelectedId(data[0].id);
      } else {
        throw new Error("empty");
      }
    } catch {
      // API not available — fall back to rich mock data
      setMatches(STATIC_MOCK);
      setUsingMock(true);
      if (!selectedId) setSelectedId(STATIC_MOCK[0].id);
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initial load
  useEffect(() => { loadMatches(); }, [loadMatches]);

  // Poll every 30 s for real data
  useEffect(() => {
    if (usingMock) return;
    const id = setInterval(loadMatches, 30_000);
    return () => clearInterval(id);
  }, [usingMock, loadMatches]);

  const selectedMatch = matches.find((m) => m.id === selectedId) ?? matches[0];
  const liveCount = matches.filter((m) => m.status === "LIVE" || m.status === "HALFTIME").length;

  const filtered = matches.filter((m) => {
    if (filter === "live") return m.status === "LIVE" || m.status === "HALFTIME";
    if (filter === "finished") return m.status === "FINISHED";
    if (filter === "scheduled") return m.status === "SCHEDULED";
    return true;
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-void)" }}>
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <motion.div className="w-8 h-8 rounded-full border-2"
              style={{ borderColor: "var(--accent-green)", borderTopColor: "transparent" }}
              animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }} />
            <p className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
              Connecting to live feed...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-void)" }}>
      <Header />

      {/* Data source banner */}
      {usingMock && (
        <div className="flex items-center justify-center gap-2 py-1.5 text-xs font-mono"
          style={{ background: "rgba(255,183,3,0.08)", borderBottom: "1px solid rgba(255,183,3,0.15)",
            color: "var(--accent-yellow)" }}>
          <span>⚠</span>
          <span>DEMO DATA — API offline. Add your <code>FOOTBALL_DATA_API_KEY</code> to .env and restart the ingestion service.</span>
        </div>
      )}

      <main className="flex-1 flex overflow-hidden" style={{ height: usingMock ? "calc(100vh - 91px)" : "calc(100vh - 57px)" }}>

        {/* Sidebar */}
        <aside className="w-80 flex-shrink-0 flex flex-col overflow-hidden"
          style={{ borderRight: "1px solid var(--border-dim)" }}>
          <div className="p-4 flex flex-col gap-3 flex-shrink-0"
            style={{ borderBottom: "1px solid var(--border-dim)" }}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
                MATCHES
              </span>
              {liveCount > 0 && (
                <motion.span
                  className="flex items-center gap-1.5 text-xs font-mono font-bold px-2 py-0.5 rounded"
                  style={{ background: "rgba(255,71,87,0.1)", color: "var(--live-pulse)",
                    border: "1px solid rgba(255,71,87,0.2)" }}
                  animate={{ opacity: [0.7, 1, 0.7] }} transition={{ duration: 1.5, repeat: Infinity }}>
                  <span className="live-dot" style={{ width: 5, height: 5 }} />
                  {liveCount} LIVE
                </motion.span>
              )}
            </div>

            <div className="flex gap-1">
              {(["all", "live", "finished", "scheduled"] as const).map((f) => (
                <button key={f} onClick={() => setFilter(f)}
                  className="flex-1 py-1 rounded text-[10px] font-mono uppercase tracking-wider transition-all"
                  style={{
                    background: filter === f ? "var(--bg-elevated)" : "transparent",
                    color: filter === f ? "var(--accent-green)" : "var(--text-muted)",
                    border: filter === f ? "1px solid var(--border-glow)" : "1px solid transparent",
                  }}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            <AnimatePresence>
              {filtered.map((match) => (
                <MatchCard key={match.id} match={match}
                  isSelected={match.id === selectedId}
                  onClick={() => setSelectedId(match.id)} />
              ))}
              {filtered.length === 0 && (
                <div className="flex items-center justify-center h-32">
                  <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>No matches found</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </aside>

        {/* Main panel */}
        <div className="flex-1 overflow-hidden p-4">
          <AnimatePresence mode="wait">
            {selectedMatch && <MatchDetailPanel key={selectedMatch.id} match={selectedMatch} />}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
