/**
 * A single stop on the learning path — the numbered disc from the mockup.
 *
 * Three states:
 *   done    → blue disc showing its number, star row lit by the real score
 *   current → the first unfinished lesson: yellow disc, glowing, wears the
 *             "CONTINUAR" bubble. Yellow is the theme's "act here" color, so
 *             the eye lands on the next step without reading a word.
 *   locked  → dim disc with a padlock; not navigable
 *
 * The thick bottom border collapses on :active, giving the physical press
 * used by the rest of the app's 3D buttons.
 *
 * Stars come from `lesson.score` (best score ever, served by the backend) —
 * see lib/stars.js. A phase's last lesson shows a trophy instead of its
 * number, marking the checkpoint.
 */

import { Link } from "react-router-dom";
import { Lock, Trophy } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { LessonStars } from "@/components/LessonStars";
import { starsFor } from "@/lib/stars";

const ContinueBubble = () => (
  <div className="absolute -top-12 left-1/2 z-10 -translate-x-1/2">
    <div className="relative rounded-xl border-2 border-brand-yellow bg-[#0d1f42] px-4 py-2 shadow-glow-yellow">
      <span className="text-xs font-black uppercase tracking-wider text-brand-yellow">
        Continuar
      </span>
      <span
        className="absolute -bottom-[7px] left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b-2 border-r-2 border-brand-yellow bg-[#0d1f42]"
        aria-hidden="true"
      />
    </div>
  </div>
);

const STATE_LABEL = {
  done: "concluída",
  current: "próxima lição",
  locked: "bloqueada",
};

export const LessonNode = ({ lesson, state, number, isPhaseEnd, offset }) => {
  const size = state === "current" ? 88 : 76;
  const stars = starsFor(lesson);

  // What goes inside the disc: a padlock when locked, the phase-end trophy,
  // otherwise the lesson's position in the path.
  const inner =
    state === "locked" ? (
      <Lock className="h-8 w-8" strokeWidth={3} aria-hidden="true" />
    ) : isPhaseEnd ? (
      <Trophy className={state === "current" ? "h-9 w-9" : "h-8 w-8"} strokeWidth={2.5} aria-hidden="true" />
    ) : (
      <span
        className={clsx("font-black tabular-nums", state === "current" ? "text-4xl" : "text-3xl")}
        aria-hidden="true"
      >
        {number}
      </span>
    );

  const disc = (
    <span
      className={clsx(
        "relative flex items-center justify-center rounded-full transition-all",
        "border-b-[6px] active:translate-y-[3px] active:border-b-0",
        state === "done" && "bg-primary border-[#123a7d] text-white ring-4 ring-white/15",
        state === "current" &&
          "bg-gradient-to-b from-brand-yellow-light to-brand-yellow border-brand-yellow-dark text-[#5a3d00] shadow-glow-yellow-lg ring-4 ring-brand-yellow/30",
        state === "locked" && "bg-[#1b2b4d] border-[#101d33] text-white/25"
      )}
      style={{ width: size, height: size }}
    >
      {inner}
    </span>
  );

  const label = `Lição ${number}: ${lesson.title} (${STATE_LABEL[state]})`;

  return (
    <div
      className="relative flex flex-col items-center"
      style={{ transform: `translateX(${offset}px)` }}
    >
      {state === "current" && <ContinueBubble />}

      {state === "locked" ? (
        <button
          type="button"
          aria-label={label}
          data-testid={`lesson-node-${lesson.id}`}
          data-state={state}
          onClick={() =>
            toast("Lição bloqueada", {
              description: "Conclua a lição anterior para desbloquear esta.",
            })
          }
          className="cursor-not-allowed"
        >
          {disc}
        </button>
      ) : (
        <Link
          to={`/lesson/${lesson.id}`}
          aria-label={label}
          data-testid={`lesson-node-${lesson.id}`}
          data-state={state}
          className="group"
        >
          {disc}
        </Link>
      )}

      {/* Stars straddle the disc's bottom edge, as in the mockup. Only earned
          rows are drawn: an all-hollow row reads as "you scored zero" rather
          than "you haven't been here yet", and on the yellow current-node it
          just looked like debris on the disc. */}
      {stars > 0 && (
        <span className="-mt-2 z-10" data-testid={`lesson-stars-${lesson.id}`} data-stars={stars}>
          <LessonStars earned={stars} />
        </span>
      )}
    </div>
  );
};
