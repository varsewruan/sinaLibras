import { GraduationCap, Home, Trophy, User } from "lucide-react";

// Single source of truth for primary navigation.
//
// The desktop Sidebar mirrors the mockup: only Início + Aprender (the mockup's
// "Comunidade" and "Loja" are intentionally omitted). Ranking / Conquistas /
// Perfil are reached from Home cards and the avatar. On mobile there are no
// such cards in the chrome, so the BottomNav carries a couple extra tabs.

export const sidebarNav = [
  { to: "/",      label: "Início",   icon: Home,          match: (p) => p === "/" },
  { to: "/learn", label: "Aprender", icon: GraduationCap, match: (p) => p.startsWith("/learn") || p.startsWith("/lesson") || p.startsWith("/dictionary") },
];

export const mobileNav = [
  ...sidebarNav,
  { to: "/ranking", label: "Ranking", icon: Trophy, match: (p) => p.startsWith("/ranking") },
  { to: "/profile", label: "Perfil",  icon: User,   match: (p) => p.startsWith("/profile") },
];
