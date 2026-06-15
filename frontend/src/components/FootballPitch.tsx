"use client";

// SVG Football Pitch with shot heatmap zones
export function FootballPitch({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 80"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Pitch background */}
      <rect x="0" y="0" width="120" height="80" rx="2"
        fill="rgba(0,40,15,0.6)" stroke="rgba(255,255,255,0.08)" strokeWidth="0.5" />

      {/* Grass stripes */}
      {[0,1,2,3,4,5,6,7,8,9].map(i => (
        <rect key={i} x={i * 12} y="0" width="12" height="80"
          fill={i % 2 === 0 ? "rgba(0,60,20,0.3)" : "transparent"} />
      ))}

      {/* Outer boundary */}
      <rect x="2" y="2" width="116" height="76" rx="1"
        fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />

      {/* Center line */}
      <line x1="60" y1="2" x2="60" y2="78" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />

      {/* Center circle */}
      <circle cx="60" cy="40" r="10" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
      <circle cx="60" cy="40" r="0.8" fill="rgba(255,255,255,0.4)" />

      {/* Left penalty box */}
      <rect x="2" y="18" width="18" height="44"
        fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
      {/* Left 6-yard box */}
      <rect x="2" y="30" width="6" height="20"
        fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      {/* Left penalty spot */}
      <circle cx="14" cy="40" r="0.6" fill="rgba(255,255,255,0.3)" />
      {/* Left penalty arc */}
      <path d="M 20 31 A 10 10 0 0 1 20 49"
        fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />

      {/* Right penalty box */}
      <rect x="100" y="18" width="18" height="44"
        fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="0.5" />
      {/* Right 6-yard box */}
      <rect x="112" y="30" width="6" height="20"
        fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      {/* Right penalty spot */}
      <circle cx="106" cy="40" r="0.6" fill="rgba(255,255,255,0.3)" />
      {/* Right penalty arc */}
      <path d="M 100 31 A 10 10 0 0 0 100 49"
        fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />

      {/* Goals */}
      <rect x="0" y="34" width="2" height="12" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="0.5" />
      <rect x="118" y="34" width="2" height="12" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="0.5" />

      {/* Corner arcs */}
      <path d="M 2 5 A 3 3 0 0 0 5 2" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      <path d="M 115 2 A 3 3 0 0 0 118 5" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      <path d="M 2 75 A 3 3 0 0 1 5 78" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      <path d="M 115 78 A 3 3 0 0 1 118 75" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
    </svg>
  );
}
