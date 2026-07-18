/**
 * Ranking — global leaderboard by XP.
 *
 * Top three get a podium; everyone else is a row. The caller's own row is
 * always reachable: highlighted inline when they're on the page, pinned to
 * the bottom when they aren't.
 */

import { motion } from "framer-motion";
import { Crown, Flame, Star, Trophy } from "lucide-react";
import clsx from "clsx";

import { AppShell } from "@/components/AppShell";
import { UserAvatar } from "@/components/UserAvatar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useRanking } from "@/lib/hooks/useRanking";
import { levelFromXp } from "@/lib/level";

// 1st / 2nd / 3rd — gold, silver, bronze.
const MEDAL = {
  1: { ring: "ring-[#FFC61A]", text: "text-[#FFC61A]", glow: "shadow-[0_0_28px_-4px_rgba(251,191,36,0.6)]", size: 88 },
  2: { ring: "ring-[#CBD5E1]", text: "text-[#CBD5E1]", glow: "shadow-[0_0_22px_-6px_rgba(203,213,225,0.5)]", size: 72 },
  3: { ring: "ring-[#D97706]", text: "text-[#D97706]", glow: "shadow-[0_0_22px_-6px_rgba(217,119,6,0.5)]", size: 72 },
};

const XpBadge = ({ xp }) => (
  <span className="inline-flex items-center gap-1 rounded-full bg-[#0a1730] px-2.5 py-1 ring-1 ring-white/10">
    <Star className="w-3.5 h-3.5 text-star" strokeWidth={2.5} aria-hidden="true" />
    <span className="text-xs font-black tabular-nums text-white">{xp}</span>
  </span>
);

const PodiumSpot = ({ entry, place }) => {
  const m = MEDAL[place];
  return (
    <div className={clsx("flex flex-col items-center gap-2", place === 1 && "-mt-6")}>
      <div className="relative">
        {place === 1 && (
          <Crown
            className="absolute -top-6 left-1/2 -translate-x-1/2 w-7 h-7 text-[#FFC61A]"
            strokeWidth={2.5}
            aria-hidden="true"
          />
        )}
        <UserAvatar
          avatar={entry.avatar}
          size={m.size}
          className={clsx("ring-4", m.ring, m.glow)}
        />
        <span
          className={clsx(
            "absolute -bottom-1 left-1/2 -translate-x-1/2 flex items-center justify-center",
            "w-7 h-7 rounded-full bg-[#0a1730] ring-2 text-sm font-black",
            m.ring, m.text
          )}
        >
          {place}
        </span>
      </div>
      <p
        className={clsx(
          "mt-1 max-w-[8rem] truncate text-center text-sm font-black",
          entry.is_me ? "text-primary" : "text-white"
        )}
      >
        {entry.name}
      </p>
      <XpBadge xp={entry.xp} />
    </div>
  );
};

const Row = ({ entry }) => (
  <li
    data-testid={entry.is_me ? "ranking-row-me" : undefined}
    className={clsx(
      "flex items-center gap-3 rounded-2xl px-4 py-3 ring-1 transition-colors",
      entry.is_me
        ? "bg-primary/15 ring-primary/60"
        : "bg-white/[0.03] ring-white/10 hover:bg-white/[0.06]"
    )}
  >
    <span className="w-7 shrink-0 text-center text-sm font-black tabular-nums text-white/50">
      {entry.rank}
    </span>
    <UserAvatar avatar={entry.avatar} size={40} />
    <div className="min-w-0 flex-1">
      <p className={clsx("truncate font-bold", entry.is_me ? "text-primary" : "text-white")}>
        {entry.name}
        {entry.is_me && <span className="ml-2 text-xs font-black uppercase">você</span>}
      </p>
      <p className="text-xs text-white/45">Nível {String(levelFromXp(entry.xp)).padStart(2, "0")}</p>
    </div>
    {entry.streak > 0 && (
      <span className="hidden sm:inline-flex items-center gap-1 text-xs font-bold text-streak">
        <Flame className="w-3.5 h-3.5" strokeWidth={2.5} aria-hidden="true" />
        {entry.streak}
      </span>
    )}
    <XpBadge xp={entry.xp} />
  </li>
);

const RankingSkeleton = () => (
  <div className="space-y-3">
    {Array.from({ length: 6 }).map((_, i) => (
      <Skeleton key={i} className="h-[66px] w-full rounded-2xl" />
    ))}
  </div>
);

export default function Ranking() {
  const { data, isLoading, isError } = useRanking(20);

  const entries = data?.entries ?? [];
  const podium = entries.slice(0, 3);
  const rest = entries.slice(3);
  const me = data?.me;
  const meOnPage = entries.some((e) => e.is_me);

  return (
    <AppShell title="Ranking">
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3">
          <Trophy className="w-8 h-8 text-star" strokeWidth={2.5} aria-hidden="true" />
          <div>
            <h2 className="text-2xl font-black text-white">Ranking global</h2>
            <p className="text-sm text-white/50">Os jogadores com mais XP.</p>
          </div>
        </div>

        {isError && (
          <p role="alert" className="text-destructive">
            Não foi possível carregar o ranking. Tente recarregar a página.
          </p>
        )}

        {isLoading && <RankingSkeleton />}

        {data && entries.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-white/60">
              Ninguém pontuou ainda. Complete uma lição para abrir o ranking!
            </CardContent>
          </Card>
        )}

        {podium.length > 0 && (
          <Card className="overflow-hidden">
            <CardContent className="flex items-end justify-center gap-6 sm:gap-10 px-4 pt-12 pb-8">
              {podium[1] && <PodiumSpot entry={podium[1]} place={2} />}
              {podium[0] && <PodiumSpot entry={podium[0]} place={1} />}
              {podium[2] && <PodiumSpot entry={podium[2]} place={3} />}
            </CardContent>
          </Card>
        )}

        {rest.length > 0 && (
          <ul className="space-y-2">
            {rest.map((e) => <Row key={e.id} entry={e} />)}
          </ul>
        )}

        {/* Off the visible page → pin the caller's position so they always see it. */}
        {me && !meOnPage && (
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-white/40">Sua posição</p>
            <ul><Row entry={me} /></ul>
          </div>
        )}
      </motion.div>
    </AppShell>
  );
}
