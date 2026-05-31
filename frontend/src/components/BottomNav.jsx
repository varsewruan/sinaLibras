import { NavLink, useLocation } from "react-router-dom";
import { BookOpen, Home, Search, User } from "lucide-react";
import clsx from "clsx";

const items = [
  { to: "/",           label: "Início",     icon: Home,     match: (p) => p === "/" },
  { to: "/lessons",    label: "Lições",     icon: BookOpen, match: (p) => p.startsWith("/lessons") || p.startsWith("/lesson/") },
  { to: "/dictionary", label: "Dicionário", icon: Search,   match: (p) => p.startsWith("/dictionary") },
  { to: "/profile",    label: "Perfil",     icon: User,     match: (p) => p.startsWith("/profile") },
];

export const BottomNav = () => {
  const { pathname } = useLocation();
  return (
    <nav
      className="lg:hidden fixed bottom-0 inset-x-0 h-16 z-30 bg-primary text-primary-foreground border-t border-primary/30 shadow-[0_-4px_12px_-2px_rgba(3,31,85,0.25)]"
      aria-label="Navegação principal"
    >
      <ul className="h-full grid grid-cols-4">
        {items.map(({ to, label, icon: Icon, match }) => {
          const active = match(pathname);
          return (
            <li key={to} className="contents">
              <NavLink
                to={to}
                aria-current={active ? "page" : undefined}
                className={clsx(
                  "flex flex-col items-center justify-center gap-0.5 text-xs font-bold transition-colors",
                  active ? "text-white" : "text-white/60 hover:text-white"
                )}
              >
                <Icon className="w-5 h-5" strokeWidth={2.5} aria-hidden="true" />
                <span>{label}</span>
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
