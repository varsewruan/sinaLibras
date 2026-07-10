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

export const PhaseBanner = ({ phase, done }) => (
  <div
    className={clsx(
      "flex items-stretch overflow-hidden rounded-2xl shadow-glow",
      done
        ? "bg-gradient-to-r from-success/80 to-success/60"
        : "bg-gradient-to-r from-primary to-[#1f6fe0]"
    )}
  >
    <div className="flex-1 px-5 py-4">
      <p className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider text-white/70">
        Fase {phase.order}
        {done && (
          <>
            <Check className="h-3.5 w-3.5" strokeWidth={3} aria-hidden="true" />
            concluída
          </>
        )}
      </p>
      <h2 className="text-lg font-black leading-tight text-white sm:text-xl">
        {phase.title}
      </h2>
      {phase.description && (
        <p className="mt-0.5 text-xs text-white/70">{phase.description}</p>
      )}
    </div>

    <Link
      to="/dictionary"
      aria-label={`Ver sinais da fase ${phase.title} no dicionário`}
      className="flex w-16 shrink-0 items-center justify-center border-l border-white/20 text-white/90 transition-colors hover:bg-white/10"
    >
      <BookOpen className="h-6 w-6" strokeWidth={2.5} aria-hidden="true" />
    </Link>
  </div>
);
