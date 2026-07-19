/**
 * Vídeo aulas — uma aula por fase (Cumprimentos, Família, Cores…).
 *
 * As aulas saem das fases reais do catálogo em vez de uma lista fixa: assim
 * uma fase nova aparece aqui sozinha, e nunca existe uma "aula" apontando pra
 * conteúdo que não existe.
 *
 * O vídeo é o mesmo material dos sinais (SignMedia decide entre filmagem real
 * e o SVG). Só 13 dos 37 termos têm filmagem, então a contagem de vídeos reais
 * aparece em cada aula — prometer "vídeo aula" e entregar desenho estático sem
 * avisar seria pior do que dizer quantos são.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, PlayCircle, Video } from "lucide-react";
import clsx from "clsx";

import { AppShell } from "@/components/AppShell";
import { SignMedia } from "@/components/SignMedia";
import { Skeleton } from "@/components/ui/skeleton";
import { useLesson, usePhases } from "@/lib/hooks/useLearning";

/** Quantos sinais da fase têm filmagem de verdade (o resto cai no SVG). */
const countClips = (signs = []) =>
  signs.filter((s) => s.video_url || s.video_webm_url).length;

const PhaseCard = ({ phase, onOpen }) => (
  <button
    type="button"
    onClick={() => onOpen(phase)}
    data-testid={`video-phase-${phase.id}`}
    className="group flex items-center gap-4 rounded-2xl bg-gradient-to-br from-[#17305c] to-[#101f3f] p-5 text-left ring-1 ring-white/10 shadow-glow transition-all hover:-translate-y-1 hover:ring-primary/50"
  >
    <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-primary/15">
      <PlayCircle className="h-8 w-8 text-primary transition-transform group-hover:scale-110" strokeWidth={2} aria-hidden="true" />
    </span>
    <span className="min-w-0 flex-1">
      <span className="block text-base font-black uppercase tracking-wide text-white">
        {phase.title}
      </span>
      {phase.description && (
        <span className="mt-0.5 block text-xs leading-snug text-white/50">
          {phase.description}
        </span>
      )}
      <span className="mt-1 block text-[11px] font-bold uppercase tracking-wider text-brand-yellow">
        {phase.lessons.length} {phase.lessons.length === 1 ? "aula" : "aulas"}
      </span>
    </span>
  </button>
);

/** Uma lição da fase, com a galeria de sinais dela. */
const LessonSection = ({ lessonId, title }) => {
  const { data: lesson, isLoading } = useLesson(lessonId);

  if (isLoading) return <Skeleton className="h-56 rounded-2xl" />;
  if (!lesson) return null;

  const clips = countClips(lesson.signs);

  return (
    <section className="space-y-3" aria-labelledby={`vl-${lessonId}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id={`vl-${lessonId}`} className="text-lg font-black text-white">
          {title}
        </h3>
        <span className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-white/40">
          <Video className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden="true" />
          {clips} de {lesson.signs.length} com vídeo
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {lesson.signs.map((sign) => (
          <figure
            key={sign.id}
            className="overflow-hidden rounded-xl bg-card ring-1 ring-white/10"
            data-testid={`video-sign-${sign.id}`}
          >
            <div className="aspect-video bg-muted">
              <SignMedia
                sign={sign}
                className="h-full w-full object-cover"
                fallbackClassName="h-full w-full"
                fallbackLabel="Sem vídeo"
              />
            </div>
            <figcaption className="px-2 py-1.5 text-center text-xs font-bold text-white/80">
              {sign.portuguese_term}
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
};

export default function VideoLessons() {
  const { data: phases, isLoading, isError } = usePhases();
  const [openPhase, setOpenPhase] = useState(null);

  return (
    <AppShell title="Vídeo aulas">
      <div className="mx-auto max-w-4xl space-y-6">
        {openPhase ? (
          <>
            <button
              type="button"
              onClick={() => setOpenPhase(null)}
              data-testid="video-back"
              className="inline-flex items-center gap-1 text-sm font-bold text-white/60 hover:text-white"
            >
              <ChevronLeft className="h-4 w-4" strokeWidth={3} aria-hidden="true" />
              Todas as aulas
            </button>

            <div>
              <h1 className="text-2xl font-black text-white">{openPhase.title}</h1>
              {openPhase.description && (
                <p className="text-sm text-white/50">{openPhase.description}</p>
              )}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="space-y-8"
            >
              {openPhase.lessons.map((lesson) => (
                <LessonSection key={lesson.id} lessonId={lesson.id} title={lesson.title} />
              ))}
            </motion.div>
          </>
        ) : (
          <>
            <div>
              <h1 className="text-2xl font-black text-white">Vídeo aulas</h1>
              <p className="text-sm text-white/50">
                Assista aos sinais de cada tema quantas vezes quiser.
              </p>
            </div>

            {isError && (
              <p role="alert" className="text-destructive">
                Não foi possível carregar as aulas. Tente recarregar a página.
              </p>
            )}

            {isLoading && (
              <div className={clsx("grid gap-4 sm:grid-cols-2")}>
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-28 rounded-2xl" />
                ))}
              </div>
            )}

            {phases && (
              <div className="grid gap-4 sm:grid-cols-2">
                {phases.map((phase) => (
                  <PhaseCard key={phase.id} phase={phase} onOpen={setOpenPhase} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
