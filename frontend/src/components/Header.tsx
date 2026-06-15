"use client";

import { motion } from "framer-motion";

export function Header() {
  return (
    <header
      className="sticky top-0 z-50 px-6 py-3 flex items-center justify-between"
      style={{
        background: "rgba(5,6,15,0.95)",
        borderBottom: "1px solid var(--border-dim)",
        backdropFilter: "blur(20px)",
      }}
    >
      <div className="flex items-center gap-4">
        {/* Logo mark */}
        <motion.div
          className="flex items-center gap-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 rounded-lg"
              style={{ background: "linear-gradient(135deg, var(--accent-cyan), var(--accent-green))", opacity: 0.15 }} />
            <div className="absolute inset-0 rounded-lg"
              style={{ border: "1px solid rgba(0,255,135,0.3)" }} />
            <div className="absolute inset-0 flex items-center justify-center text-sm">
              ⚽
            </div>
          </div>
          <div>
            <p className="text-xs font-black tracking-[0.3em] uppercase"
              style={{ color: "var(--accent-green)", letterSpacing: "0.3em" }}>
              WAR ROOM
            </p>
            <p className="text-[10px] font-mono" style={{ color: "var(--text-muted)" }}>
              WORLD CUP 2026
            </p>
          </div>
        </motion.div>
      </div>

      {/* Center — live matches count */}
      <motion.div
        className="flex items-center gap-2 px-3 py-1 rounded-full"
        style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-dim)" }}
        animate={{ borderColor: ["rgba(255,71,87,0.1)", "rgba(255,71,87,0.4)", "rgba(255,71,87,0.1)"] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <span className="live-dot" />
        <span className="text-xs font-mono font-bold" style={{ color: "var(--live-pulse)" }}>
          REALTIME
        </span>
      </motion.div>

      {/* Right — system info */}
      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <p className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
          </p>
          <p className="text-xs font-mono" style={{ color: "var(--accent-green)" }}>
            LIVE ANALYTICS
          </p>
        </div>
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent-green)" }} />
      </div>
    </header>
  );
}
