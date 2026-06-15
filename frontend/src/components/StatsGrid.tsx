"use client";

import { motion } from "framer-motion";
import { MatchStats } from "@/types";

interface StatRowProps {
  label: string;
  home: number;
  away: number;
  format?: (n: number) => string;
  highlight?: boolean;
  invert?: boolean; // lower is better (e.g. fouls)
}

function StatRow({ label, home, away, format, highlight, invert }: StatRowProps) {
  const total = home + away || 1;
  const homePct = (home / total) * 100;
  const awayPct = (away / total) * 100;
  const fmt = format ?? ((n: number) => n.toString());

  const homeColor = highlight
    ? "var(--accent-cyan)"
    : invert
    ? away > home ? "var(--accent-cyan)" : "var(--text-primary)"
    : "var(--text-primary)";
  const awayColor = highlight
    ? "var(--accent-green)"
    : invert
    ? home > away ? "var(--accent-green)" : "var(--text-primary)"
    : "var(--text-primary)";

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-sm font-mono tabular-nums font-bold w-10 text-left" style={{ color: homeColor }}>
          {fmt(home)}
        </span>
        <span className="text-xs uppercase tracking-widest flex-1 text-center" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
        <span className="text-sm font-mono tabular-nums font-bold w-10 text-right" style={{ color: awayColor }}>
          {fmt(away)}
        </span>
      </div>
      <div className="flex gap-0.5 h-1">
        <motion.div
          className="rounded-l-full"
          style={{ background: highlight ? "var(--accent-cyan)" : "rgba(0,200,255,0.4)" }}
          initial={{ width: 0 }}
          animate={{ width: `${homePct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
        <motion.div
          className="rounded-r-full ml-auto"
          style={{ background: highlight ? "var(--accent-green)" : "rgba(0,255,150,0.4)" }}
          initial={{ width: 0 }}
          animate={{ width: `${awayPct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

interface StatsGridProps {
  stats: MatchStats;
  homeTeam: string;
  awayTeam: string;
  dataSource?: string;
}

export function StatsGrid({ stats, homeTeam, awayTeam, dataSource }: StatsGridProps) {
  const isReal = dataSource === "api_football";
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex justify-between items-center text-xs font-mono uppercase tracking-widest pb-1"
        style={{ borderBottom: "1px solid var(--border-dim)" }}>
        <span style={{ color: "var(--accent-cyan)" }}>{homeTeam}</span>
        <div className="flex items-center gap-2">
          <span style={{ color: "var(--text-muted)" }}>STATS</span>
          <span
            className="text-[9px] px-1.5 py-0.5 rounded-sm font-bold"
            style={{
              background: isReal ? "rgba(0,255,150,0.15)" : "rgba(255,200,0,0.15)",
              color: isReal ? "var(--accent-green)" : "#ffc107",
              border: `1px solid ${isReal ? "rgba(0,255,150,0.3)" : "rgba(255,200,0,0.3)"}`,
            }}
          >
            {isReal ? "REAL" : "MODEL"}
          </span>
        </div>
        <span style={{ color: "var(--accent-green)" }}>{awayTeam}</span>
      </div>

      {/* xG — primary metric */}
      <StatRow label="xG" home={stats.xg_home} away={stats.xg_away}
        format={(n) => n.toFixed(2)} highlight />

      {/* Shots group */}
      <StatRow label="SHOTS" home={stats.shots_home} away={stats.shots_away} />
      <StatRow label="ON TARGET" home={stats.shots_on_target_home} away={stats.shots_on_target_away} />
      <StatRow label="BLOCKED" home={stats.shots_blocked_home ?? 0} away={stats.shots_blocked_away ?? 0} />

      {/* Possession */}
      <StatRow label="POSSESSION %" home={stats.possession_home} away={stats.possession_away}
        format={(n) => `${n.toFixed(0)}%`} />

      {/* Passing */}
      <StatRow label="PASSES" home={stats.passes_home} away={stats.passes_away} />
      <StatRow label="PASS ACC %" home={stats.pass_accuracy_home} away={stats.pass_accuracy_away}
        format={(n) => `${n.toFixed(0)}%`} />

      {/* Set pieces */}
      <StatRow label="CORNERS" home={stats.corners_home} away={stats.corners_away} />
      <StatRow label="OFFSIDES" home={stats.offsides_home ?? 0} away={stats.offsides_away ?? 0} />

      {/* Fouls & cards */}
      <StatRow label="FOULS" home={stats.fouls_home} away={stats.fouls_away} invert />
      <StatRow label="YELLOW CARDS" home={stats.yellow_cards_home ?? 0} away={stats.yellow_cards_away ?? 0} invert />
    </div>
  );
}

