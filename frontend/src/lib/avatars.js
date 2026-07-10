/**
 * Avatar presets. No image assets — each avatar is a gradient disc + emoji,
 * which renders everywhere and needs no network. The user's chosen avatar is
 * stored as its `id` string on the backend; "dummy" is the default when the
 * user never picks one.
 *
 * Shared by the picker (Profile), the top bar, the sidebar and the ranking.
 */
export const DEFAULT_AVATAR = "dummy";

export const AVATARS = [
  { id: "dummy",  label: "Padrão",   emoji: "🧑", from: "#64748b", to: "#334155" },
  { id: "fox",    label: "Raposa",   emoji: "🦊", from: "#fb923c", to: "#ea580c" },
  { id: "cat",    label: "Gato",     emoji: "🐱", from: "#f59e0b", to: "#b45309" },
  { id: "panda",  label: "Panda",    emoji: "🐼", from: "#94a3b8", to: "#475569" },
  { id: "owl",    label: "Coruja",   emoji: "🦉", from: "#a78bfa", to: "#7c3aed" },
  { id: "frog",   label: "Sapo",     emoji: "🐸", from: "#4ade80", to: "#16a34a" },
  { id: "robot",  label: "Robô",     emoji: "🤖", from: "#38bdf8", to: "#0284c7" },
  { id: "hero",   label: "Herói",    emoji: "🦸", from: "#60a5fa", to: "#2563eb" },
  { id: "star",   label: "Estrela",  emoji: "⭐", from: "#fbbf24", to: "#d97706" },
  { id: "alien",  label: "Alien",    emoji: "👽", from: "#2dd4bf", to: "#0d9488" },
  { id: "unicorn",label: "Unicórnio",emoji: "🦄", from: "#f472b6", to: "#db2777" },
  { id: "ninja",  label: "Ninja",    emoji: "🥷", from: "#818cf8", to: "#4f46e5" },
];

export const avatarById = (id) =>
  AVATARS.find((a) => a.id === id) ?? AVATARS[0];
