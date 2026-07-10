import { NavLink, useLocation } from "react-router-dom";
import { Flame, Hand } from "lucide-react";
import clsx from "clsx";

import { useAuth } from "@/context/AuthContext";
import { sidebarNav } from "@/lib/nav-items";

export const Sidebar = () => {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const streak = user?.streak?.current ?? 0;

  return (
    <aside
      className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col bg-[#0a1730] border-r border-white/10 shadow-2xl"
      aria-label="Navegação principal"
    >
      <div className="h-16 flex items-center gap-2 px-6 border-b border-white/10">
        <Hand className="w-6 h-6 text-primary -rotate-12" strokeWidth={2.5} aria-hidden="true" />
        <span className="text-xl font-black tracking-tight text-white">
          SINA<span className="text-primary">libras</span>
        </span>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {sidebarNav.map(({ to, label, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <NavLink
              key={to}
              to={to}
              aria-current={active ? "page" : undefined}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-full font-bold transition-all",
                active
                  ? "bg-gradient-to-r from-primary to-[#1f6fe0] text-white shadow-glow"
                  : "text-white/60 hover:text-white hover:bg-white/5"
              )}
            >
              <Icon className="w-5 h-5" strokeWidth={2.5} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Streak block — mirrors the mockup's big flame counter at the bottom. */}
      <div className="p-4">
        <div className="flex items-center gap-3 rounded-2xl bg-gradient-to-br from-[#13294f] to-[#0e1f3d] border border-white/10 px-4 py-3">
          <Flame
            className={clsx("w-8 h-8 text-streak", streak > 0 && "animate-flame-pulse")}
            strokeWidth={2.5}
            aria-hidden="true"
          />
          <div className="leading-tight">
            <p className="text-2xl font-black text-white tabular-nums">{streak}</p>
            <p className="text-[11px] font-bold uppercase tracking-wider text-white/50">
              {streak === 1 ? "dia de fogo" : "dias de fogo"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
};
