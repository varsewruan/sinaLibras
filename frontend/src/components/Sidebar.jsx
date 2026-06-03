import { NavLink, useLocation } from "react-router-dom";
import clsx from "clsx";

import { navItems } from "../lib/nav-items";

export const Sidebar = () => {
  const { pathname } = useLocation();
  return (
    <aside
      className="hidden lg:flex fixed inset-y-0 left-0 w-64 flex-col bg-primary text-primary-foreground border-r border-primary/30 shadow-xl"
      aria-label="Navegação principal"
    >
      <div className="h-16 flex items-center px-6 border-b border-white/15">
        <span className="text-xl font-black tracking-tight">
          SINALibras
        </span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <NavLink
              key={to}
              to={to}
              aria-current={active ? "page" : undefined}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold transition-colors",
                active
                  ? "bg-white/15 text-white"
                  : "text-white/70 hover:text-white hover:bg-white/10"
              )}
            >
              <Icon className="w-5 h-5" strokeWidth={2.5} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};
