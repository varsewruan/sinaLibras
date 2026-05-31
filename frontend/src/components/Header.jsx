/**
 * Top bar with gamification stats. Shown on every authenticated page.
 *
 * Number rolls (XP, streak) animate via framer-motion so the user feels
 * the reward when XP lands. The Flame icon pulses while there's an active
 * streak — a small thing that makes the page feel "alive".
 */

import { motion } from "framer-motion";
import { Coins, Flame, LogOut, Zap } from "lucide-react";
import clsx from "clsx";

import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";

const RollingNumber = ({ value }) => (
  <motion.span
    key={value}
    initial={{ opacity: 0, y: -6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
    className="text-sm font-bold tabular-nums"
  >
    {value}
  </motion.span>
);

const Stat = ({ icon: Icon, value, color, label, animateIcon = false, testId }) => (
  <div
    data-testid={testId}
    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white text-foreground shadow-sm ring-1 ring-white/40"
    aria-label={`${label}: ${value}`}
  >
    <Icon
      className={clsx("w-4 h-4", animateIcon && "animate-flame-pulse")}
      style={{ color }}
      strokeWidth={2.5}
      aria-hidden="true"
    />
    <RollingNumber value={value} />
  </div>
);

export const Header = ({ title }) => {
  const { user, logout } = useAuth();
  const xp = user?.xp ?? 0;
  const streak = user?.streak?.current ?? 0;
  return (
    <header className="sticky top-0 z-30 bg-primary text-primary-foreground border-b border-primary/30 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <h1 className="hidden lg:block text-xl font-bold tracking-tight">{title}</h1>
        <div className="flex items-center gap-2 ml-auto">
          <Stat icon={Zap}   value={xp}     color="#7C3AED" label="XP"        testId="stat-xp" />
          <Stat icon={Flame} value={streak} color="#EA580C" label="Sequência" testId="stat-streak" animateIcon={streak > 0} />
          <Stat icon={Coins} value={0}      color="#CA8A04" label="Moedas"    testId="stat-coins" />
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            aria-label="Sair"
            data-testid="logout"
            className="ml-1 text-primary-foreground hover:bg-white/15 hover:text-primary-foreground"
          >
            <LogOut className="w-5 h-5" strokeWidth={2.5} />
          </Button>
        </div>
      </div>
    </header>
  );
};
