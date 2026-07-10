/**
 * A single stop on the learning path — the Duolingo-style circular button.
 *
 * Three states:
 *   done    → filled blue disc with a check
 *   current → the first unfinished lesson: bright, glowing, wears the
 *             "CONTINUAR" bubble
 *   locked  → dim disc with a padlock; not navigable
 *
 * The thick bottom border collapses on :active, giving the physical press
 * used by the rest of the app's 3D buttons.
 */

import { Link } from "react-router-dom";
import { Check, Lock, Star, Trophy } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

const ContinueBubble = () => (
  <div className="absolute -top-12 left-1/2 z-10 -translate-x-1/2">
    <div className="relative rounded-xl border-2 border-primary bg-[#0d1f42] px-4 py-2 shadow-glow">
      <span className="text-xs font-black uppercase tracking-wider text-primary">
        Continuar
      </span>
      <span
        className="absolute -bottom-[7px] left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b-2 border-r-2 border-primary bg-[#0d1f42]"
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

export const LessonNode = ({ lesson, state, isPhaseEnd, offset }) => {
  const size = state === "current" ? 88 : 76;
  const Icon = state === "done" ? Check : state === "locked" ? Lock : isPhaseEnd ? Trophy : Star;

  const disc = (
    <span
      className={clsx(
        "relative flex items-center justify-center rounded-full transition-all",
        "border-b-[6px] active:translate-y-[3px] active:border-b-0",
        state === "done" && "bg-primary border-[#123a7d] text-white",
        state === "current" &&
          "bg-gradient-to-b from-[#8dcef0] to-[#4fa3dd] border-[#2a6ea3] text-[#06203f] shadow-glow-lg ring-4 ring-primary/30",
        state === "locked" && "bg-[#1b2b4d] border-[#101d33] text-white/25"
      )}
      style={{ width: size, height: size }}
    >
      <Icon className={state === "current" ? "h-9 w-9" : "h-8 w-8"} strokeWidth={3} aria-hidden="true" />
    </span>
  );

  const label = `${lesson.title} (${STATE_LABEL[state]})`;

  return (
    <div
      className="relative flex flex-col items-center gap-2"
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

      <span
        className={clsx(
          "max-w-[120px] text-center text-xs font-bold leading-tight",
          state === "locked" ? "text-white/30" : "text-white/70"
        )}
      >
        {lesson.title}
      </span>
    </div>
  );
};
