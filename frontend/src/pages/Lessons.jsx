/**
 * The Path — a winding trail of lesson nodes, Duolingo-style.
 *
 * Lessons unlock strictly in order: everything before the first unfinished
 * lesson is `done`, that lesson is `current` (it wears the CONTINUAR bubble),
 * and everything after is `locked`. Because that ordering spans phases, the
 * state is computed over a flattened list rather than per-phase.
 *
 * The dashed trail between nodes is drawn by <PathConnector/>, which takes
 * the same OFFSETS this file applies to the nodes — that shared table is
 * what keeps the curve's endpoints exactly on the discs without measuring
 * the DOM. Connectors are drawn *within* a phase only; the phase banner is
 * the intentional break in the trail.
 *
 * Note: locking is a UI affordance. /lesson/:id stays directly reachable —
 * lesson content is public, so there's nothing to guard server-side.
 */

import { Fragment, useMemo } from "react";
import { motion } from "framer-motion";
import { PartyPopper } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { LessonNode } from "@/components/LessonNode";
import { PathConnector } from "@/components/PathConnector";
import { PathMarker } from "@/components/PathMarker";
import { PathSkeleton } from "@/components/PathSkeleton";
import { PhaseBanner } from "@/components/PhaseBanner";
import { usePhases } from "@/lib/hooks/useLearning";

// Serpentine: horizontal offset (px) applied to each node, cycling down the
// trail so the path snakes instead of running straight.
const OFFSETS = [0, 56, 84, 56, 0, -56, -84, -56];

const offsetAt = (i) => OFFSETS[i % OFFSETS.length];

/**
 * Flatten the phases once: each lesson's position in the global order, the
 * index of the first unfinished one, and the total.
 */
const flatten = (phases = []) => {
  const indexById = new Map();
  let total = 0;
  let nextIndex = -1;

  for (const phase of phases) {
    for (const lesson of phase.lessons) {
      indexById.set(lesson.id, total);
      if (nextIndex === -1 && !lesson.completed) nextIndex = total;
      total += 1;
    }
  }
  return { indexById, nextIndex, total };
};

const stateFor = (globalIndex, nextIndex) => {
  if (nextIndex === -1) return "done";      // catalog complete
  if (globalIndex < nextIndex) return "done";
  if (globalIndex === nextIndex) return "current";
  return "locked";
};

const AllDone = () => (
  <div className="flex flex-col items-center gap-2 rounded-2xl bg-card-glow px-6 py-8 text-center ring-1 ring-white/10">
    <PartyPopper className="h-10 w-10 text-star" strokeWidth={2.5} aria-hidden="true" />
    <h3 className="text-xl font-black text-white">Você concluiu tudo!</h3>
    <p className="text-sm text-white/50">
      Mais conteúdo vem em breve. Enquanto isso, revise no dicionário.
    </p>
  </div>
);

export default function Lessons() {
  const { data: phases, isLoading, isError } = usePhases();

  const { indexById, nextIndex, total } = useMemo(() => flatten(phases), [phases]);
  const allDone = total > 0 && nextIndex === -1;

  return (
    <AppShell title="Fases">
      {isLoading && <PathSkeleton />}

      {isError && (
        <p role="alert" className="text-destructive">
          Não foi possível carregar as lições. Tente recarregar a página.
        </p>
      )}

      {phases && (
        <div className="mx-auto max-w-lg space-y-10 pb-8">
          {allDone && <AllDone />}

          {total > 0 && (
            <div className="flex justify-center">
              <PathMarker variant="start" label="Início" />
            </div>
          )}

          {phases.map((phase, pi) => {
            const phaseDone = phase.lessons.length > 0 && phase.lessons.every((l) => l.completed);
            return (
              <motion.section
                key={phase.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: pi * 0.06, duration: 0.3 }}
                aria-labelledby={`phase-${phase.id}-heading`}
                className="space-y-8"
              >
                <div id={`phase-${phase.id}-heading`}>
                  <PhaseBanner phase={phase} done={phaseDone} />
                </div>

                {/* Tight gap on purpose: the 72px connector supplies the
                    vertical rhythm between nodes (and the clearance the
                    CONTINUAR bubble needs). A large gap here would leave the
                    dashes floating short of both discs. */}
                <div className="flex flex-col items-center gap-3">
                  {phase.lessons.map((lesson, li) => (
                    <Fragment key={lesson.id}>
                      {li > 0 && (
                        <PathConnector fromOffset={offsetAt(li - 1)} toOffset={offsetAt(li)} />
                      )}
                      <LessonNode
                        lesson={lesson}
                        state={stateFor(indexById.get(lesson.id), nextIndex)}
                        // 1-based position in the whole path, matching the
                        // numbered nodes in the design.
                        number={indexById.get(lesson.id) + 1}
                        isPhaseEnd={li === phase.lessons.length - 1}
                        offset={offsetAt(li)}
                      />
                    </Fragment>
                  ))}
                </div>
              </motion.section>
            );
          })}

          {total > 0 && (
            <div className="flex justify-center">
              <PathMarker variant="finish" label="Final" />
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
