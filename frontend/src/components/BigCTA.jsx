/**
 * The hero pill button from the mockup — "JOGAR" / "COMEÇAR".
 *
 * A dark navy pill with a bright play disc and a heavy blue halo. Presses in
 * on :active like the rest of the 3D buttons in the app.
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
      "px-8 sm:px-12 py-4 sm:py-5 ring-1 ring-primary/40 shadow-glow-lg",
      "transition-all hover:brightness-110 hover:ring-primary/70 active:translate-y-0.5"
    )}
  >
    <span className="flex items-center justify-center w-11 h-11 sm:w-14 sm:h-14 rounded-full bg-primary shadow-glow shrink-0">
      <Play className="w-5 h-5 sm:w-7 sm:h-7 text-white translate-x-[1px]" fill="currentColor" strokeWidth={0} />
    </span>
    <span className="text-3xl sm:text-5xl font-black tracking-wide text-white">{label}</span>
  </Link>
);
