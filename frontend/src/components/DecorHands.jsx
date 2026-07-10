/**
 * Faded Libras hand outlines drifting behind a hero panel — the decorative
 * layer from the mockup. Purely ornamental, hidden from assistive tech.
 */
import { Hand } from "lucide-react";

const MARKS = [
  { top: "6%",  left: "4%",  size: 120, rotate: -18, opacity: 0.05 },
  { top: "52%", left: "-2%", size: 90,  rotate: 12,  opacity: 0.04 },
  { top: "12%", right: "6%", size: 150, rotate: 20,  opacity: 0.05 },
  { bottom: "-6%", right: "22%", size: 110, rotate: -8, opacity: 0.04 },
];

export const DecorHands = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    {MARKS.map((m, i) => {
      const { size, rotate, opacity, ...pos } = m;
      return (
        <Hand
          key={i}
          className="absolute text-white"
          style={{ ...pos, width: size, height: size, opacity, transform: `rotate(${rotate}deg)` }}
          strokeWidth={1.5}
        />
      );
    })}
  </div>
);
