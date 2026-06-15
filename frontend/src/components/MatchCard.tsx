"use client";

import { motion } from "framer-motion";
import { Match } from "@/types";
import { formatMinute, formatTime } from "@/lib/utils";
import { useMatchWebSocket } from "@/hooks/useMatchWebSocket";

interface MatchCardProps {
  match: Match;
  onClick?: () => void;
  isSelected?: boolean;
}

export function MatchCard({ match, onClick, isSelected }: MatchCardProps) {
  const { connected, messages } = useMatchWebSocket(match.id);
  const isLive = match.status === "LIVE" || match.status === "HALFTIME";

  // Use latest score from WS if available
  const latestScore = messages.find((m) => m.score)?.score ?? match.score;

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className="w-full text-left glass glass-hover rounded-xl p-4 relative overflow-hidden"
      style={{
        border: isSelected
          ? "1px solid rgba(0,255,135,0.4)"
          : "1px solid var(--border-dim)",
        boxShadow: isSelected
          ? "0 0 30px rgba(0,255,135,0.08), inset 0 0 30px rgba(0,255,135,0.02)"
          : undefined,
      }}
    >
      {/* Live indicator strip */}
      {isLive && (
        <motion.div
          className="absolute top-0 left-0 right-0 h-0.5"
          style={{ background: "linear-gradient(90deg, var(--live-pulse), transparent)" }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      )}

      <div className="flex items-center justify-between gap-4">
        {/* Home team */}
        <div className="flex-1 text-right">
          <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
            {match.home_team.short_name}
          </p>
          <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
            {match.home_team.name}
          </p>
        </div>

        {/* Score / Time */}
        <div className="flex flex-col items-center gap-1 min-w-[80px]">
          {isLive ? (
            <>
              <div className="flex items-center gap-2">
                <span className="live-dot" />
                <span className="text-xs font-mono font-bold" style={{ color: "var(--live-pulse)" }}>
                  {match.status === "HALFTIME" ? "HT" : formatMinute(match.minute ?? null)}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-mono font-black tabular-nums"
                  style={{ color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                  {latestScore.home}
                </span>
                <span className="text-sm font-mono" style={{ color: "var(--text-muted)" }}>–</span>
                <span className="text-2xl font-mono font-black tabular-nums"
                  style={{ color: "var(--text-primary)" }}>
                  {latestScore.away}
                </span>
              </div>
            </>
          ) : match.status === "FINISHED" ? (
            <>
              <span className="text-xs font-mono uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                FT
              </span>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-mono font-black">{match.score.home}</span>
                <span className="text-sm font-mono" style={{ color: "var(--text-muted)" }}>–</span>
                <span className="text-2xl font-mono font-black">{match.score.away}</span>
              </div>
            </>
          ) : (
            <>
              <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                {formatTime(match.kickoff_utc)}
              </span>
              <span className="text-xl font-mono font-bold" style={{ color: "var(--text-secondary)" }}>
                vs
              </span>
            </>
          )}
        </div>

        {/* Away team */}
        <div className="flex-1">
          <p className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
            {match.away_team.short_name}
          </p>
          <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
            {match.away_team.name}
          </p>
        </div>
      </div>

      {/* xG bar (only for live/finished) */}
      {(isLive || match.status === "FINISHED") && (
        <div className="mt-3 space-y-1">
          <div className="flex justify-between text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            <span>xG {match.stats.xg_home.toFixed(2)}</span>
            <span className="uppercase tracking-widest text-[10px]">expected goals</span>
            <span>xG {match.stats.xg_away.toFixed(2)}</span>
          </div>
          <div className="flex h-1 rounded-full overflow-hidden gap-px"
            style={{ background: "var(--bg-elevated)" }}>
            <motion.div
              className="rounded-l-full"
              style={{
                background: "linear-gradient(90deg, var(--accent-cyan), rgba(0,212,255,0.5))",
                width: `${(match.stats.xg_home / (match.stats.xg_home + match.stats.xg_away + 0.01)) * 100}%`,
              }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 1.2 }}
            />
            <motion.div
              className="rounded-r-full ml-auto"
              style={{
                background: "linear-gradient(90deg, rgba(0,255,135,0.5), var(--accent-green))",
                width: `${(match.stats.xg_away / (match.stats.xg_home + match.stats.xg_away + 0.01)) * 100}%`,
              }}
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 1.2 }}
            />
          </div>
        </div>
      )}

      {/* Connection dot */}
      <div className="absolute top-3 right-3">
        <div className="w-1.5 h-1.5 rounded-full"
          style={{ background: connected ? "var(--accent-green)" : "var(--text-muted)" }} />
      </div>
    </motion.button>
  );
}
