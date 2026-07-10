/**
 * Conquistas — the achievement catalog, evaluated server-side.
 *
 * Unlocked badges glow and carry a check; locked ones stay dim and show a
 * progress bar toward their target. The backend caps `progress` at `target`,
 * so the bar never overflows.
 */

import { motion } from "framer-motion";
import {
  BookCheck, Check, Crown, Flame, GraduationCap, Sparkles, Star, Target, Trophy,
} from "lucide-react";
import clsx from "clsx";

import { AppShell } from "@/components/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAchievements } from "@/lib/hooks/useAchievements";

// The API sends a lucide icon *name*; map it here so the bundle only pulls
// the icons we actually use.
const ICONS = { Sparkles, Star, Trophy, Crown, Flame, BookCheck, GraduationCap };

// Tint per metric — XP gold, streak orange, lessons green.
const TINT = {
  xp: "#FBBF24",
  streak: "#FB923C",
  lessons: "#34D399",
};

const AchievementCard = ({ a }) => {
  const Icon = ICONS[a.icon] ?? Trophy;
  const color = TINT[a.metric] ?? "#38BDF8";
  const pct = Math.round((a.progress / a.target) * 100);

  return (
    <Card
      data-testid={`achievement-${a.id}`}
      data-unlocked={a.unlocked}
      className={clsx(
        "relative overflow-hidden transition-all",
        a.unlocked
          ? "ring-1 ring-white/15 shadow-glow"
          : "opacity-70 hover:opacity-90"
      )}
    >
      <CardContent className="p-5 flex items-start gap-4">
        <div
          className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl"
          style={{
            background: a.unlocked ? `${color}26` : "rgba(255,255,255,0.05)",
            color: a.unlocked ? color : "#64748b",
            boxShadow: a.unlocked ? `0 0 22px -6px ${color}` : "none",
          }}
        >
          <Icon className="h-7 w-7" strokeWidth={2.5} aria-hidden="true" />
          {a.unlocked && (
            <span
              className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-success ring-2 ring-card"
              aria-hidden="true"
            >
              <Check className="h-3 w-3 text-[#06281a]" strokeWidth={4} />
            </span>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className={clsx("font-black", a.unlocked ? "text-white" : "text-white/70")}>
              {a.title}
            </h3>
            {a.unlocked && (
              <span className="rounded-full bg-success/20 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-success">
                Concluída
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs leading-snug text-white/50">{a.description}</p>

          <div className="mt-3 space-y-1">
            <div
              className="h-2 w-full overflow-hidden rounded-full bg-white/10"
              role="progressbar"
              aria-valuenow={a.progress}
              aria-valuemin={0}
              aria-valuemax={a.target}
              aria-label={a.title}
            >
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${pct}%`, background: a.unlocked ? color : "#475569" }}
              />
            </div>
            <p className="text-right text-[11px] font-bold tabular-nums text-white/40">
              {a.progress}/{a.target}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default function Achievements() {
  const { data, isLoading, isError } = useAchievements();

  return (
    <AppShell title="Conquistas">
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3">
          <Target className="h-8 w-8 text-gem" strokeWidth={2.5} aria-hidden="true" />
          <div className="flex-1">
            <h2 className="text-2xl font-black text-white">Conquistas</h2>
            <p className="text-sm text-white/50">
              {data
                ? `${data.unlocked_count} de ${data.total} desbloqueadas.`
                : "Complete metas e ganhe recompensas."}
            </p>
          </div>
          {data && (
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-[#0a1730] px-3 py-1.5 ring-1 ring-white/10">
              <Trophy className="h-4 w-4 text-star" strokeWidth={2.5} aria-hidden="true" />
              <span className="text-sm font-black tabular-nums text-white">
                {data.unlocked_count}/{data.total}
              </span>
            </span>
          )}
        </div>

        {isError && (
          <p role="alert" className="text-destructive">
            Não foi possível carregar as conquistas. Tente recarregar a página.
          </p>
        )}

        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-[130px] w-full rounded-2xl" />
            ))}
          </div>
        )}

        {data && (
          <div className="grid gap-4 sm:grid-cols-2">
            {data.achievements.map((a) => (
              <AchievementCard key={a.id} a={a} />
            ))}
          </div>
        )}
      </motion.div>
    </AppShell>
  );
}
