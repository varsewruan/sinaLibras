/**
 * The bookends of the path: the INÍCIO flag at the top and the checkered
 * FINAL flag at the bottom, from the mockup.
 *
 * `variant="start"` plants a yellow pennant on a glowing base ring;
 * `variant="finish"` is the checkered flag inside a burst of light. Both
 * carry a label pill matching the lesson nodes' typography.
 */
import { Flag, FlagTriangleRight } from "lucide-react";

const Pill = ({ children }) => (
  <span className="mt-2 rounded-lg bg-[#16294f] px-3 py-1 text-[11px] font-black uppercase tracking-wide text-white/80 ring-1 ring-white/10">
    {children}
  </span>
);

export const PathMarker = ({ variant, label }) => {
  const isFinish = variant === "finish";
  const Icon = isFinish ? Flag : FlagTriangleRight;

  return (
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
        <Icon
          className="relative h-10 w-10 text-brand-yellow drop-shadow-[0_0_10px_rgba(255,198,26,0.6)]"
          strokeWidth={2.5}
          aria-hidden="true"
        />
      </span>
      <Pill>{label}</Pill>
    </div>
  );
};
