"use client";

import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";

interface XGPoint {
  minute: number;
  xg_home: number;
  xg_away: number;
}

interface XGChartProps {
  data: XGPoint[];
  homeTeam: string;
  awayTeam: string;
}

export function XGChart({ data, homeTeam, awayTeam }: XGChartProps) {
  const defaultData: XGPoint[] = data.length > 0 ? data : [
    { minute: 0, xg_home: 0, xg_away: 0 },
    { minute: 45, xg_home: 0, xg_away: 0 },
    { minute: 90, xg_home: 0, xg_away: 0 },
  ];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded" style={{ background: "var(--accent-cyan)" }} />
            <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>{homeTeam}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded" style={{ background: "var(--accent-green)" }} />
            <span className="text-xs font-mono" style={{ color: "var(--text-secondary)" }}>{awayTeam}</span>
          </div>
        </div>
        <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
          xG TIMELINE
        </span>
      </div>

      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={defaultData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="xgHome" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="xgAway" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00ff87" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00ff87" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Tooltip
              contentStyle={{
                background: "var(--bg-surface)",
                border: "1px solid var(--border-dim)",
                borderRadius: "8px",
                fontSize: "12px",
                fontFamily: "monospace",
                color: "var(--text-primary)",
              }}
              formatter={(value: number, name: string) => [value.toFixed(3), name === "xg_home" ? homeTeam : awayTeam]}
              labelFormatter={(label) => `Minute ${label}'`}
            />
            <Area
              type="monotone"
              dataKey="xg_home"
              stroke="#00d4ff"
              strokeWidth={2}
              fill="url(#xgHome)"
            />
            <Area
              type="monotone"
              dataKey="xg_away"
              stroke="#00ff87"
              strokeWidth={2}
              fill="url(#xgAway)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Minute markers */}
      <div className="flex justify-between text-xs font-mono px-0.5" style={{ color: "var(--text-muted)" }}>
        <span>0'</span>
        <span>45'</span>
        <span>90'</span>
      </div>
    </div>
  );
}
