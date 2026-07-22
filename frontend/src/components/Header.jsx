/**
 * Top bar — mirrors the mockup. Left: avatar + name + level (links to the
 * profile). Right: XP (gold star), gems (cyan), notifications, settings.
 *
 * The star/level numbers roll in via framer-motion so an XP gain feels
 * rewarding. Since the sidebar was removed this bar carries the streak too —
 * it was the sidebar's only unique content, and losing it would have made the
 * streak invisible on desktop.
 */

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Bell, Flame, Gem, Hand, Plus, Settings, Star } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/context/AuthContext";
import { UserAvatar } from "@/components/UserAvatar";
import { Wordmark } from "@/components/Wordmark";
import { gemsFromXp, levelFromXp } from "@/lib/level";

const RollingNumber = ({ value }) => (
  <motion.span
    key={value}
    initial={{ opacity: 0, y: -6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25 }}
    className="tabular-nums"
  >
    {value}
  </motion.span>
);

const StatPill = ({ icon: Icon, value, color, label, trailing, testId }) => (
  <div
    data-testid={testId}
    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#0a1730] ring-1 ring-white/10"
    aria-label={`${label}: ${value}`}
  >
    <Icon className="w-4 h-4" style={{ color }} strokeWidth={2.5} aria-hidden="true" />
    <span className="text-sm font-black text-white">
      <RollingNumber value={value} />
    </span>
    {trailing}
  </div>
);

const IconButton = ({ icon: Icon, label, onClick, to }) => {
  const cls =
    "inline-flex items-center justify-center w-9 h-9 rounded-xl bg-[#0a1730] ring-1 ring-white/10 text-white/70 hover:text-white hover:ring-white/25 transition-colors";
  const inner = <Icon className="w-5 h-5" strokeWidth={2.5} aria-hidden="true" />;
  return to ? (
    <Link to={to} aria-label={label} className={cls}>{inner}</Link>
  ) : (
    <button type="button" aria-label={label} onClick={onClick} className={cls}>{inner}</button>
  );
};

export const Header = () => {
  const { user } = useAuth();
  const xp = user?.xp ?? 0;
  const level = levelFromXp(xp);
  const gems = gemsFromXp(xp);
  const streak = user?.streak?.current ?? 0;

  return (
    <header className="sticky top-0 z-30 bg-[#0e1f3d]/95 backdrop-blur border-b border-white/10 shadow-md">
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
        {/* Home link, compact form. Below lg the centered wordmark would
            collide with the stat pills, so the hand icon stands in — with the
            sidebar gone, losing the home link entirely would strand the user
            on whatever page they clicked into. */}
        <Link
          to="/"
          className="lg:hidden flex items-center shrink-0 mr-1"
          aria-label="Início"
        >
          <Hand className="w-6 h-6 text-primary -rotate-12 shrink-0" strokeWidth={2.5} aria-hidden="true" />
        </Link>

        {/* Home link, centered form (lg+). Absolute so it centers against the
            header itself rather than against whatever the flex row leaves
            over — the left and right clusters have very different widths. */}
        <Link
          to="/"
          aria-label="Início"
          className="hidden lg:block absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        >
          <Wordmark as="span" className="text-xl transition-opacity hover:opacity-80" />
        </Link>

        {/* Identity — links to profile */}
        <Link
          to="/profile"
          className="flex items-center gap-3 min-w-0 rounded-full pr-3 hover:bg-white/5 transition-colors"
          data-testid="header-profile"
        >
          <UserAvatar avatar={user?.avatar} accessory={user?.accessory} size={40} ring />
          <div className="hidden sm:block leading-tight min-w-0">
            <p className="font-black text-white truncate max-w-[10rem]">{user?.name ?? "—"}</p>
            <p className="text-xs font-bold text-white/50">Nível {String(level).padStart(2, "0")}</p>
          </div>
        </Link>

        <div className="flex items-center gap-2 ml-auto">
          <StatPill icon={Star}     value={xp}   color="#FFC61A" label="XP"    testId="stat-xp" />
          <StatPill
            icon={Gem} value={gems} color="#38BDF8" label="Gemas" testId="stat-gems"
            trailing={<Plus className="w-3 h-3 text-gem" strokeWidth={3} aria-hidden="true" />}
          />
          {/* The only place the streak appears now that the sidebar is gone. */}
          <div className="hidden sm:block">
            <StatPill icon={Flame} value={streak} color="#FB923C" label="Sequência" testId="stat-streak" />
          </div>
          <IconButton
            icon={Bell}
            label="Notificações"
            onClick={() => toast("Sem novas notificações", { description: "Você está em dia! 🎉" })}
          />
          <IconButton icon={Settings} label="Configurações" to="/profile" />
        </div>
      </div>
    </header>
  );
};
