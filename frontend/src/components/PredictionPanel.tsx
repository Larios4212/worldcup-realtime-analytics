"use client";

import { motion } from "framer-motion";
import { Prediction } from "@/lib/api";

interface PredictionPanelProps {
  prediction: Prediction;
  homeTeam: string;
  awayTeam: string;
}

function ProbBar({
  label,
  prob,
  color,
  team,
}: {
  label: string;
  prob: number;
  color: string;
  team?: string;
}) {
  const pct = Math.round(prob * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-baseline">
        <span className="text-xs uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
          {team || label}
        </span>
        <span className="text-lg font-mono font-black" style={{ color }}>
          {pct}%
        </span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.05)" }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function FormBadges({ form, color }: { form: string; color: string }) {
  if (!form) return <span style={{ color: "var(--text-muted)" }} className="text-xs">—</span>;
  return (
    <div className="flex gap-1">
      {form.split("").map((c, i) => (
        <span
          key={i}
          className="text-[10px] font-bold w-5 h-5 flex items-center justify-center rounded-sm"
          style={{
            background:
              c === "W"
                ? "rgba(0,255,150,0.2)"
                : c === "D"
                ? "rgba(255,200,0,0.2)"
                : "rgba(255,50,50,0.2)",
            color:
              c === "W" ? "var(--accent-green)" : c === "D" ? "#ffc107" : "#ff4444",
            border: `1px solid ${c === "W" ? "rgba(0,255,150,0.4)" : c === "D" ? "rgba(255,200,0,0.4)" : "rgba(255,50,50,0.4)"}`,
          }}
        >
          {c}
        </span>
      ))}
    </div>
  );
}

export function PredictionPanel({ prediction, homeTeam, awayTeam }: PredictionPanelProps) {
  const confidence = Math.round(prediction.confidence * 100);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div
        className="flex justify-between items-center text-xs font-mono uppercase tracking-widest pb-1"
        style={{ borderBottom: "1px solid var(--border-dim)" }}
      >
        <span style={{ color: "var(--text-muted)" }}>PREDICTION</span>
        <div className="flex items-center gap-1.5">
          <span
            className="text-[9px] px-1.5 py-0.5 rounded-sm font-bold"
            style={{
              background: "rgba(147,51,234,0.15)",
              color: "#a855f7",
              border: "1px solid rgba(147,51,234,0.3)",
            }}
          >
            ELO + POISSON
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            {confidence}% conf
          </span>
        </div>
      </div>

      {/* Win probabilities */}
      <div className="space-y-2">
        <ProbBar
          label="HOME WIN"
          prob={prediction.home_win_prob}
          color="var(--accent-cyan)"
          team={homeTeam}
        />
        <ProbBar label="DRAW" prob={prediction.draw_prob} color="#ffc107" />
        <ProbBar
          label="AWAY WIN"
          prob={prediction.away_win_prob}
          color="var(--accent-green)"
          team={awayTeam}
        />
      </div>

      {/* Expected goals */}
      {(prediction.predicted_goals_home > 0 || prediction.predicted_goals_away > 0) && (
        <div
          className="flex justify-between items-center pt-2"
          style={{ borderTop: "1px solid var(--border-dim)" }}
        >
          <div className="text-center">
            <div
              className="text-2xl font-black font-mono"
              style={{ color: "var(--accent-cyan)" }}
            >
              {prediction.predicted_goals_home.toFixed(1)}
            </div>
            <div className="text-[9px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
              xGoals
            </div>
          </div>
          <div className="text-xs" style={{ color: "var(--text-muted)" }}>
            EXPECTED
          </div>
          <div className="text-center">
            <div
              className="text-2xl font-black font-mono"
              style={{ color: "var(--accent-green)" }}
            >
              {prediction.predicted_goals_away.toFixed(1)}
            </div>
            <div className="text-[9px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
              xGoals
            </div>
          </div>
        </div>
      )}

      {/* Team ratings */}
      <div
        className="grid grid-cols-2 gap-3 pt-2"
        style={{ borderTop: "1px solid var(--border-dim)" }}
      >
        <div className="space-y-1">
          <div className="text-[9px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
            {homeTeam} form
          </div>
          <FormBadges form={prediction.home_form} color="var(--accent-cyan)" />
          <div className="flex items-center gap-1 mt-1">
            <div
              className="text-xs font-bold"
              style={{ color: "var(--accent-cyan)" }}
            >
              ATK {Math.round(prediction.home_attack_rating)}
            </div>
          </div>
        </div>
        <div className="space-y-1 text-right">
          <div className="text-[9px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
            {awayTeam} form
          </div>
          <div className="flex justify-end">
            <FormBadges form={prediction.away_form} color="var(--accent-green)" />
          </div>
          <div className="flex items-center justify-end gap-1 mt-1">
            <div
              className="text-xs font-bold"
              style={{ color: "var(--accent-green)" }}
            >
              ATK {Math.round(prediction.away_attack_rating)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
