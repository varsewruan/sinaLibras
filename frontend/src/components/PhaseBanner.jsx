/**
 * The sticky section header above each stretch of the path — the mockup's
 * "SEÇÃO 1, UNIDADE 7" banner, in SINALibras blue.
 *
 * The trailing button jumps to the dictionary filtered on nothing in
 * particular; it's the "see the material" affordance from the reference.
 */

import { Link } from "react-router-dom";
import { BookOpen, Check } from "lucide-react";
import clsx from "clsx";

// A finished phase wears the brand yellow rather than a success green: the
// stars, the streak and the XP star are all yellow, so "you earned this"
// already reads as yellow everywhere else on the path. Green would be a
// third color carrying a meaning the palette already covers.
export const PhaseBanner = ({ phase, done }) => (
  <div
    className={clsx(
      "flex items-stretch overflow-hidden rounded-2xl",
      done
        ? "bg-gradient-to-r from-brand-yellow to-brand-yellow-dark shadow-glow-yellow"
        : "bg-gradient-to-r from-primary to-[#1f6fe0] shadow-glow"
    )}
  >
    <div className="flex-1 px-5 py-4">
      <p
        className={clsx(
          "flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider",
          done ? "text-[#5a3d00]" : "text-white/70"
        )}
      >
        Fase {phase.order}
        {done && (
          <>
            <Check className="h-3.5 w-3.5" strokeWidth={3} aria-hidden="true" />
            concluída
          </>
        )}
      </p>
      <h2
        className={clsx(
          "text-lg font-black leading-tight sm:text-xl",
          done ? "text-[#3d2900]" : "text-white"
        )}
      >
        {phase.title}
      </h2>
      {phase.description && (
        <p className={clsx("mt-0.5 text-xs", done ? "text-[#5a3d00]" : "text-white/70")}>
          {phase.description}
        </p>
      )}
    </div>

    <Link
      to="/dictionary"
      aria-label={`Ver sinais da fase ${phase.title} no dicionário`}
      className={clsx(
        "flex w-16 shrink-0 items-center justify-center border-l transition-colors hover:bg-white/10",
        done ? "border-black/15 text-[#3d2900]" : "border-white/20 text-white/90"
      )}
    >
      <BookOpen className="h-6 w-6" strokeWidth={2.5} aria-hidden="true" />
    </Link>
  </div>
);
