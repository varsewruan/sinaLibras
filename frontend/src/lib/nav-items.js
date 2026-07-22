import { GraduationCap, Home, Trophy, User } from "lucide-react";

// Single source of truth for primary navigation.
//
// There's no desktop sidebar anymore (removed 2026-07-18) — the Home hub is
// the screen that carries every entry point, and the Header brand is the way
// back to it. So this list now feeds only the mobile BottomNav.
//
// `primaryNav` is kept separate from `mobileNav` because the first two are
// the "always somewhere" destinations and the last two are the extras the
// bottom bar has room for; the split is what keeps the bar at four columns
// (see BottomNav's grid-cols-4).

export const primaryNav = [
  { to: "/",      label: "Início",   icon: Home,          match: (p) => p === "/" },
  { to: "/learn", label: "Aprender", icon: GraduationCap, match: (p) => p.startsWith("/learn") || p.startsWith("/lesson") || p.startsWith("/dictionary") },
];

export const mobileNav = [
  ...primaryNav,
  { to: "/ranking", label: "Ranking", icon: Trophy, match: (p) => p.startsWith("/ranking") },
  { to: "/profile", label: "Perfil",  icon: User,   match: (p) => p.startsWith("/profile") },
];
