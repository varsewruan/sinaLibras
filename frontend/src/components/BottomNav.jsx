import { NavLink, useLocation } from "react-router-dom";
import clsx from "clsx";

import { mobileNav } from "@/lib/nav-items";

export const BottomNav = () => {
  const { pathname } = useLocation();
  return (
    <nav
      className="lg:hidden fixed bottom-0 inset-x-0 h-16 z-30 bg-[#0a1730]/95 backdrop-blur border-t border-white/10 shadow-[0_-4px_16px_-2px_rgba(0,0,0,0.5)]"
      aria-label="Navegação principal"
    >
      <ul className="h-full grid grid-cols-4">
        {mobileNav.map(({ to, label, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <li key={to} className="contents">
              <NavLink
                to={to}
                aria-current={active ? "page" : undefined}
                className="flex flex-col items-center justify-center gap-1"
              >
                <span
                  className={clsx(
                    "flex items-center justify-center w-11 h-8 rounded-full transition-colors",
                    active ? "bg-primary/20 text-primary" : "text-white/50"
                  )}
                >
                  <Icon className="w-5 h-5" strokeWidth={2.5} aria-hidden="true" />
                </span>
                <span
                  className={clsx(
                    "text-[10px] font-bold",
                    active ? "text-white" : "text-white/50"
                  )}
                >
                  {label}
                </span>
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
