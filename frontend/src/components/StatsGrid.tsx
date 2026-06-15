"use client";

import { motion } from "framer-motion";
import { MatchStats } from "@/types";

interface StatRowProps {
  label: string;
  home: number;
  away: number;
  format?: (n: number) => string;
  highlight?: boolean;
}

function StatRow({ label, home, away, format, highlight }: StatRowProps) {
  const total = home + away || 1;
  const homePct = (home / total) * 100;
  const awayPct = (away / total) * 100;
  const fmt = format ?? ((n: number) => n.toString());

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span
          className="text-sm font-mono tabular-nums font-bold"
          style={{ color: highlight ? "var(--accent-cyan)" : "var(--text-primary)" }}
        >
          {fmt(home)}
        </span>
        <span className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
        <span
          className="text-sm font-mono tabular-nums font-bold"
          style={{ color: highlight ? "var(--accent-green)" : "var(--text-primary)" }}
        >
          {fmt(away)}
        </span>
      </div>
      <div className="flex gap-0.5 h-1">
        <motion.div
          className="rounded-l-full"
          style={{ background: "var(--accent-cyan)", opacity: 0.7 }}
          initial={{ width: 0 }}
          animate={{ width: `${homePct}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <motion.div
          className="rounded-r-full ml-auto"
          style={{ background: "var(--accent-green)", opacity: 0.7 }}
          initial={{ width: 0 }}
          animate={{ width: `${awayPct}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

interface StatsGridProps {
  stats: MatchStats;
  homeTeam: string;
  awayTeam: string;
}

export function StatsGrid({ stats, homeTeam, awayTeam }: StatsGridProps) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between text-xs font-mono opacity-50 uppercase tracking-widest pb-1"
        style={{ borderBottom: "1px solid var(--border-dim)" }}>
        <span style={{ color: "var(--accent-cyan)" }}>{homeTeam}</span>
        <span>STATISTICS</span>
        <span style={{ color: "var(--accent-green)" }}>{awayTeam}</span>
      </div>

      <StatRow label="xG" home={stats.xg_home} away={stats.xg_away}
        format={(n) => n.toFixed(2)} highlight />
      <StatRow label="SHOTS" home={stats.shots_home} away={stats.shots_away} />
      <StatRow label="ON TARGET" home={stats.shots_on_target_home} away={stats.shots_on_target_away} />
      <StatRow label="CORNERS" home={stats.corners_home} away={stats.corners_away} />
      <StatRow label="FOULS" home={stats.fouls_home} away={stats.fouls_away} />
      <StatRow label="PASSES" home={stats.passes_home} away={stats.passes_away} />
    </div>
  );
}
