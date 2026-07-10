/**
 * Home — the game hub from the mockup.
 *
 * One glowing panel: a big JOGAR button that resumes the first unfinished
 * lesson, plus the three entry points (Fases / Objetivos / Ranking).
 */

import { MapPin, Target, Trophy } from "lucide-react";
import { motion } from "framer-motion";

import { AppShell } from "@/components/AppShell";
import { BigCTA } from "@/components/BigCTA";
import { DecorHands } from "@/components/DecorHands";
import { FeatureCard } from "@/components/FeatureCard";
import { Skeleton } from "@/components/ui/skeleton";
import { usePhases } from "@/lib/hooks/useLearning";
import { findNextLesson } from "@/lib/next-lesson";

const HUB = [
  {
    icon: MapPin, iconColor: "#FBBF24", to: "/lessons", testId: "hub-fases",
    title: "Fases", description: "Escolha sua próxima missão e avance!",
  },
  {
    icon: Target, iconColor: "#38BDF8", to: "/achievements", testId: "hub-objetivos",
    title: "Objetivos", description: "Complete conquistas e ganhe recompensas!",
  },
  {
    icon: Trophy, iconColor: "#FBBF24", to: "/ranking", testId: "hub-ranking",
    title: "Ranking", description: "Veja sua posição no ranking e compita!",
  },
];

export default function Home() {
  const { data: phases, isLoading } = usePhases();
  const next = phases ? findNextLesson(phases) : null;

  // Everything done (or catalog empty) → send the CTA to the path overview.
  const ctaTo = next ? `/lesson/${next.lesson.id}` : "/lessons";

  return (
    <AppShell title="Início">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-3xl bg-card-glow ring-1 ring-white/10 px-6 py-10 sm:px-10 sm:py-14"
      >
        <DecorHands />

        <div className="relative flex flex-col items-center gap-10">
          {isLoading ? (
            <Skeleton className="h-[76px] w-[280px] rounded-full" />
          ) : (
            <BigCTA to={ctaTo} label="JOGAR" testId="cta-jogar" />
          )}

          <div className="grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
            {HUB.map((card) => (
              <FeatureCard key={card.title} {...card} />
            ))}
          </div>
        </div>
      </motion.section>
    </AppShell>
  );
}
