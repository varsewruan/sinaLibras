/**
 * Aprender — the second mockup screen.
 *
 * COMEÇAR resumes the next lesson. Below it, the study-mode hub. Only the
 * modes that have a backend today are real links (Fases → the path,
 * Dicionário → the sign search); the rest render as "Em breve" tiles.
 */

import { BookMarked, CalendarCheck, CircleHelp, Clapperboard, Sparkles, SpellCheck2 } from "lucide-react";
import { motion } from "framer-motion";

import { AppShell } from "@/components/AppShell";
import { BigCTA } from "@/components/BigCTA";
import { DecorHands } from "@/components/DecorHands";
import { FeatureCard } from "@/components/FeatureCard";
import { Skeleton } from "@/components/ui/skeleton";
import { usePhases } from "@/lib/hooks/useLearning";
import { findNextLesson } from "@/lib/next-lesson";

const MODES = [
  {
    icon: SpellCheck2, iconColor: "#60A5FA", soon: true, testId: "mode-alfabeto",
    title: "Alfabeto", description: "Adquira conhecimento praticando o alfabeto em Libras.",
  },
  {
    icon: CircleHelp, iconColor: "#A78BFA", soon: true, testId: "mode-quiz",
    title: "Quiz", description: "Aprenda respondendo perguntas.",
  },
  {
    icon: Clapperboard, iconColor: "#F472B6", soon: true, testId: "mode-videoaulas",
    title: "Vídeo-aulas", description: "Aprenda assistindo vídeo-aulas com professores reais.",
  },
  {
    icon: Sparkles, iconColor: "#38BDF8", soon: true, testId: "mode-simulacao",
    title: "Simulação", description: "Aprenda língua de sinais com o Libro, seu amigo que ensina!",
  },
  {
    icon: BookMarked, iconColor: "#34D399", to: "/dictionary", testId: "mode-dicionario",
    title: "Dicionário", description: "Aprenda palavras da língua brasileira de sinais.",
  },
  {
    icon: CalendarCheck, iconColor: "#FB923C", soon: true, testId: "mode-revisao",
    title: "Revisão diária", description: "Revise os sinais que você já aprendeu, todo dia.",
  },
];

export default function Learn() {
  const { data: phases, isLoading } = usePhases();
  const next = phases ? findNextLesson(phases) : null;
  const ctaTo = next ? `/lesson/${next.lesson.id}` : "/lessons";

  return (
    <AppShell title="Aprender">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-3xl bg-card-glow ring-1 ring-white/10 px-6 py-10 sm:px-10 sm:py-14"
      >
        <DecorHands />

        <div className="relative flex flex-col items-center gap-10">
          {isLoading ? (
            <Skeleton className="h-[76px] w-[320px] rounded-full" />
          ) : (
            <BigCTA to={ctaTo} label="COMEÇAR" testId="cta-comecar" />
          )}

          <div className="grid w-full max-w-4xl grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {MODES.map((card) => (
              <FeatureCard key={card.title} {...card} />
            ))}
          </div>
        </div>
      </motion.section>
    </AppShell>
  );
}
