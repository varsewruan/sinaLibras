/**
 * Home — the game hub from the mockup.
 *
 * The wordmark over a 6-up grid of entry points. Four are live; Loja and
 * Vídeo Aulas have no backend yet and render as "Em breve" tiles.
 *
 * There is deliberately no JOGAR button here: the mockup's hub is the grid,
 * and "resume the next lesson" already lives on Aprender as COMEÇAR. Tile
 * tones follow the theme rule — structure is blue, rewards are yellow.
 */

import { BookOpen, MapPin, PlayCircle, ShoppingCart, Target, Trophy } from "lucide-react";
import { motion } from "framer-motion";

import { AppShell } from "@/components/AppShell";
import { DecorHands } from "@/components/DecorHands";
import { HubTile } from "@/components/HubTile";
import { Wordmark } from "@/components/Wordmark";

const HUB = [
  { icon: BookOpen,    tone: "blue",   to: "/learn",        testId: "hub-aprender",  title: "Aprender" },
  { icon: MapPin,      tone: "blue",   to: "/lessons",      testId: "hub-fases",     title: "Fases" },
  { icon: Target,      tone: "yellow", to: "/achievements", testId: "hub-objetivos", title: "Objetivos" },
  { icon: Trophy,      tone: "yellow", to: "/ranking",      testId: "hub-ranking",   title: "Ranking" },
  { icon: ShoppingCart,tone: "yellow", to: "/shop",          testId: "hub-loja",      title: "Loja" },
  { icon: PlayCircle,  tone: "blue",   to: "/video-lessons", testId: "hub-videoaulas",title: "Vídeo Aulas" },
];

export default function Home() {
  return (
    <AppShell title="Início">
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="relative overflow-hidden rounded-3xl bg-card-glow px-6 py-10 ring-1 ring-white/10 sm:px-10 sm:py-14"
      >
        {/* Two ornamental layers from the mockup: the dot grid and the drifting
            hand outlines. Both are aria-hidden. */}
        <div className="pointer-events-none absolute inset-0 bg-dots opacity-40" aria-hidden="true" />
        <DecorHands />

        <div className="relative flex flex-col items-center gap-10">
          <Wordmark className="text-5xl sm:text-7xl" />

          <div className="grid w-full max-w-3xl grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-5">
            {HUB.map((tile) => (
              <HubTile key={tile.title} {...tile} />
            ))}
          </div>
        </div>
      </motion.section>
    </AppShell>
  );
}
