/**
 * The "Path" — phases stacked vertically, each with a row of lesson dots.
 *
 * Polish notes:
 *   • A phase whose lessons are ALL completed gets a blue glow ring +
 *     small "Concluída" tag, so progress is visible at a glance.
 *   • Loading uses a Path-shaped skeleton instead of a spinner — feels
 *     instant even on slow connections.
 */

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Check } from "lucide-react";
import clsx from "clsx";

import { AppShell } from "@/components/AppShell";
import { PathSkeleton } from "@/components/PathSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { usePhases } from "@/lib/hooks/useLearning";

const LessonDot = ({ lesson, index }) => (
  <Link
    to={`/lesson/${lesson.id}`}
    aria-label={`Lição ${index + 1}: ${lesson.title}${lesson.completed ? " (concluída)" : ""}`}
    data-testid={`lesson-dot-${lesson.id}`}
    className="group flex flex-col items-center gap-2 min-w-[88px]"
  >
    <div
      className={clsx(
        "w-16 h-16 rounded-full flex items-center justify-center border-4 transition-all group-hover:scale-110",
        lesson.completed
          ? "bg-accent text-accent-foreground border-accent shadow-glow"
          : "bg-card text-foreground border-border group-hover:border-accent"
      )}
    >
      {lesson.completed ? (
        <Check className="w-7 h-7" strokeWidth={3} />
      ) : (
        <span className="font-black text-lg">{index + 1}</span>
      )}
    </div>
    <span className="text-xs font-bold text-center leading-tight max-w-[88px] text-muted-foreground group-hover:text-foreground">
      {lesson.title}
    </span>
  </Link>
);

const PhaseSection = ({ phase, sectionIndex }) => {
  const allDone = phase.lessons.length > 0 && phase.lessons.every((l) => l.completed);
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: sectionIndex * 0.08, duration: 0.3 }}
      aria-labelledby={`phase-${phase.id}-heading`}
    >
      <Card className={clsx(allDone && "ring-2 ring-accent shadow-glow")}>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-primary">
              Fase {phase.order}
            </p>
            <CardTitle id={`phase-${phase.id}-heading`} className="text-2xl">{phase.title}</CardTitle>
            {phase.description && (
              <p className="text-sm text-muted-foreground mt-1">{phase.description}</p>
            )}
          </div>
          {allDone && (
            <span className="shrink-0 text-xs font-bold uppercase tracking-wider text-primary bg-accent/20 px-3 py-1 rounded-full border border-primary/30">
              Concluída
            </span>
          )}
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {phase.lessons.map((lesson, i) => (
              <LessonDot key={lesson.id} lesson={lesson} index={i} />
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.section>
  );
};

export default function Lessons() {
  const { data: phases, isLoading, isError } = usePhases();

  return (
    <AppShell title="Lições">
      {isLoading && <PathSkeleton />}
      {isError && (
        <p role="alert" className="text-destructive">
          Não foi possível carregar as lições. Tente recarregar a página.
        </p>
      )}
      {phases && (
        <div className="space-y-6">
          {phases.map((phase, i) => (
            <PhaseSection key={phase.id} phase={phase} sectionIndex={i} />
          ))}
        </div>
      )}
    </AppShell>
  );
}
