import { BookOpen, Home, Search, User } from "lucide-react";

// Single source of truth for primary navigation. Consumed by both the
// desktop Sidebar and the mobile BottomNav so the two never drift apart.
export const navItems = [
  { to: "/",           label: "Início",     icon: Home,     match: (p) => p === "/" },
  { to: "/lessons",    label: "Lições",     icon: BookOpen, match: (p) => p.startsWith("/lessons") || p.startsWith("/lesson/") },
  { to: "/dictionary", label: "Dicionário", icon: Search,   match: (p) => p.startsWith("/dictionary") },
  { to: "/profile",    label: "Perfil",     icon: User,     match: (p) => p.startsWith("/profile") },
];
