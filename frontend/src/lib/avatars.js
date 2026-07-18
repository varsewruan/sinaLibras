/**
 * Avatar presets. No image assets — each avatar is a gradient disc + emoji,
 * which renders everywhere and needs no network. The user's chosen avatar is
 * stored as its `id` string on the backend; "dummy" is the default when the
 * user never picks one.
 *
 * The roster mirrors the cartoon-animal reference sheet (bear, lion, monkey,
 * fox, rabbit, dog, cat, panda, frog, tiger) plus the original non-animal
 * presets, which are kept so nobody's saved avatar silently changes.
 *
 * Gradients are warm/saturated so the discs pop against the navy chrome; the
 * `from`/`to` pairs approximate each animal's own coloring rather than the
 * brand palette — this is the one surface where color means "which character
 * am I", not "what does this control do".
 *
 * IMPORTANT: `backend/app/models/user.py::AVATAR_IDS` is the allowlist and
 * the authority. An id added here but missing there is rejected with a 422 —
 * keep the two lists in sync.
 *
 * Shared by the picker (Profile), the top bar, the sidebar and the ranking.
 */
export const DEFAULT_AVATAR = "dummy";

export const AVATARS = [
  { id: "dummy",  label: "Padrão",   emoji: "🧑", from: "#64748b", to: "#334155" },
  // Animals from the reference sheet.
  { id: "bear",   label: "Urso",     emoji: "🐻", from: "#d99a4e", to: "#a1662f" },
  { id: "lion",   label: "Leão",     emoji: "🦁", from: "#f6c445", to: "#b9761c" },
  { id: "monkey", label: "Macaco",   emoji: "🐵", from: "#c98f63", to: "#8d5a34" },
  { id: "fox",    label: "Raposa",   emoji: "🦊", from: "#fb923c", to: "#ea580c" },
  { id: "rabbit", label: "Coelho",   emoji: "🐰", from: "#cbd5e1", to: "#8a94a6" },
  { id: "dog",    label: "Cachorro", emoji: "🐶", from: "#e8c49a", to: "#a9743f" },
  { id: "cat",    label: "Gato",     emoji: "🐱", from: "#f59e0b", to: "#b45309" },
  { id: "panda",  label: "Panda",    emoji: "🐼", from: "#e5e7eb", to: "#4b5563" },
  { id: "frog",   label: "Sapo",     emoji: "🐸", from: "#4ade80", to: "#16a34a" },
  { id: "tiger",  label: "Tigre",    emoji: "🐯", from: "#fb923c", to: "#c2410c" },
  // Original non-animal presets — retained so existing users keep theirs.
  { id: "owl",    label: "Coruja",   emoji: "🦉", from: "#a78bfa", to: "#7c3aed" },
  { id: "robot",  label: "Robô",     emoji: "🤖", from: "#38bdf8", to: "#0284c7" },
  { id: "hero",   label: "Herói",    emoji: "🦸", from: "#60a5fa", to: "#2563eb" },
  { id: "star",   label: "Estrela",  emoji: "⭐", from: "#ffd966", to: "#c98a00" },
  { id: "alien",  label: "Alien",    emoji: "👽", from: "#2dd4bf", to: "#0d9488" },
  { id: "unicorn",label: "Unicórnio",emoji: "🦄", from: "#f472b6", to: "#db2777" },
  { id: "ninja",  label: "Ninja",    emoji: "🥷", from: "#818cf8", to: "#4f46e5" },
];

export const avatarById = (id) =>
  AVATARS.find((a) => a.id === id) ?? AVATARS[0];
