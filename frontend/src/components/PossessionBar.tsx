"use client";

import { motion } from "framer-motion";

interface PossessionBarProps {
  home: number;
  away: number;
  homeTeam: string;
  awayTeam: string;
}

export function PossessionBar({ home, away, homeTeam, awayTeam }: PossessionBarProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-xs font-mono">
        <span style={{ color: "var(--accent-cyan)" }}>{homeTeam}</span>
        <span style={{ color: "var(--text-muted)" }}>POSSESSION</span>
        <span style={{ color: "var(--accent-green)" }}>{awayTeam}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-mono font-bold tabular-nums" style={{ color: "var(--accent-cyan)" }}>
          {home.toFixed(0)}%
        </span>
        <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "var(--bg-elevated)" }}>
          <motion.div
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(90deg, var(--accent-cyan) 0%, rgba(0,212,255,0.4) ${home}%, rgba(0,255,135,0.4) ${home}%, var(--accent-green) 100%)`,
            }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </div>
        <span className="text-sm font-mono font-bold tabular-nums" style={{ color: "var(--accent-green)" }}>
          {away.toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
