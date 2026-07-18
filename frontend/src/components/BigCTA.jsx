/**
 * The hero pill button — "COMEÇAR" on the Aprender screen.
 *
 * A dark navy pill with a yellow play disc and a warm halo. The disc is the
 * theme's "act here" yellow while the pill stays navy: an all-yellow slab
 * this size would out-shout the tiles below it, and yellow is supposed to
 * mark one target per screen, not dominate the screen.
 *
 * Presses in on :active like the rest of the 3D buttons in the app.
 */
import { Link } from "react-router-dom";
import { Play } from "lucide-react";
import clsx from "clsx";

export const BigCTA = ({ to, label, testId }) => (
  <Link
    to={to}
    data-testid={testId}
    className={clsx(
      "group inline-flex items-center gap-4 sm:gap-5 rounded-full",
      "bg-gradient-to-b from-[#132c56] to-[#0c1c3c]",
      "px-8 sm:px-12 py-4 sm:py-5 ring-1 ring-brand-yellow/40 shadow-glow-yellow",
      "transition-all hover:brightness-110 hover:ring-brand-yellow/70 active:translate-y-0.5"
    )}
  >
    <span className="flex items-center justify-center w-11 h-11 sm:w-14 sm:h-14 rounded-full bg-brand-yellow shadow-glow-yellow shrink-0">
      <Play className="w-5 h-5 sm:w-7 sm:h-7 text-[#0d1c3d] translate-x-[1px]" fill="currentColor" strokeWidth={0} />
    </span>
    <span className="text-3xl sm:text-5xl font-black tracking-wide text-white">{label}</span>
  </Link>
);
