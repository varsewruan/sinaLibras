/**
 * The INÍCIO flag that opens the path, from the mockup: a yellow pennant on a
 * glowing base ring, with a label pill matching the lesson nodes' typography.
 *
 * There is no closing "FINAL" marker on purpose — the game is meant to read as
 * endless, so the path just keeps going by phase number and name instead of
 * planting a finish flag at the bottom.
 */
import { FlagTriangleRight } from "lucide-react";

const Pill = ({ children }) => (
  <span className="mt-2 rounded-lg bg-[#16294f] px-3 py-1 text-[11px] font-black uppercase tracking-wide text-white/80 ring-1 ring-white/10">
    {children}
  </span>
);

export const PathMarker = ({ label }) => (
  <div className="flex flex-col items-center">
    <span className="relative flex h-16 w-16 items-center justify-center">
      {/* Glow puddle under the marker. */}
      <span
        aria-hidden="true"
        className="absolute inset-0 rounded-full bg-brand-yellow/15 blur-md"
      />
      <span
        aria-hidden="true"
        className="absolute bottom-1 h-2 w-10 rounded-full bg-brand-yellow/40 blur-[3px]"
      />
      <FlagTriangleRight
        className="relative h-10 w-10 text-brand-yellow drop-shadow-[0_0_10px_rgba(255,198,26,0.6)]"
        strokeWidth={2.5}
        aria-hidden="true"
      />
    </span>
    <Pill>{label}</Pill>
  </div>
);
