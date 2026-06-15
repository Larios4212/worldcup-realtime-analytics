"use client";

import { motion, AnimatePresence } from "framer-motion";
import { WsMessage, EventType } from "@/types";

const EVENT_CONFIG: Record<string, { icon: string; color: string; cssClass: string; label: string }> = {
  GOAL:         { icon: "⚽", color: "var(--accent-gold)",   cssClass: "event-goal",   label: "GOAL" },
  OWN_GOAL:     { icon: "⚽", color: "var(--accent-red)",    cssClass: "event-goal",   label: "OWN GOAL" },
  YELLOW_CARD:  { icon: "🟨", color: "var(--accent-yellow)", cssClass: "event-yellow", label: "YELLOW" },
  RED_CARD:     { icon: "🟥", color: "var(--accent-red)",    cssClass: "event-red",    label: "RED CARD" },
  SUBSTITUTION: { icon: "↕",  color: "var(--accent-cyan)",   cssClass: "event-sub",    label: "SUB" },
  PENALTY:      { icon: "🎯", color: "var(--accent-gold)",   cssClass: "event-goal",   label: "PENALTY" },
  VAR:          { icon: "📺", color: "#a78bfa",              cssClass: "event-var",    label: "VAR" },
};

interface EventFeedProps {
  events: WsMessage[];
}

export function EventFeed({ events }: EventFeedProps) {
  const filtered = events.filter(
    (e) => e.type !== "PING" && e.type !== "STATS_UPDATE"
  );

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 pb-2" style={{ borderBottom: "1px solid var(--border-dim)" }}>
        <span className="text-xs uppercase tracking-widest font-mono" style={{ color: "var(--text-muted)" }}>
          LIVE FEED
        </span>
        {filtered.length > 0 && (
          <span className="text-xs font-mono px-1.5 py-0.5 rounded"
            style={{ background: "var(--bg-elevated)", color: "var(--accent-green)" }}>
            {filtered.length}
          </span>
        )}
      </div>

      <div className="space-y-1.5 max-h-80 overflow-y-auto pr-1">
        <AnimatePresence initial={false}>
          {filtered.length === 0 && (
            <p className="text-xs text-center py-8 font-mono" style={{ color: "var(--text-muted)" }}>
              Waiting for match events...
            </p>
          )}
          {filtered.map((event, i) => {
            const cfg = EVENT_CONFIG[event.type] ?? {
              icon: "•", color: "var(--text-muted)", cssClass: "", label: event.type
            };
            return (
              <motion.div
                key={`${event.timestamp}-${i}`}
                initial={{ opacity: 0, x: -20, height: 0 }}
                animate={{ opacity: 1, x: 0, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className={`pl-3 py-2 rounded-r glass ${cfg.cssClass}`}
              >
                <div className="flex items-start gap-2">
                  <span className="text-base leading-none mt-0.5">{cfg.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold tabular-nums"
                        style={{ color: "var(--accent-cyan)" }}>
                        {event.minute ? `${event.minute}'` : "--"}
                      </span>
                      <span className="text-xs font-bold uppercase tracking-wider"
                        style={{ color: cfg.color }}>
                        {cfg.label}
                      </span>
                    </div>
                    {event.player && (
                      <p className="text-sm font-medium mt-0.5 truncate"
                        style={{ color: "var(--text-primary)" }}>
                        {event.player}
                      </p>
                    )}
                    {event.description && (
                      <p className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
                        {event.description}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
