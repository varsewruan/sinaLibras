/**
 * XP → level + cosmetic currencies. Single source so the top bar, profile
 * and ranking all agree on "what level is this user".
 *
 * Linear tiers: every 175 XP is one level, starting at level 1. Chosen so
 * the mockup's reference (950 XP → "Nível 06") lands exactly.
 */
export const levelFromXp = (xp = 0) => Math.floor(Math.max(0, xp) / 175) + 1;

/** XP remaining until the next level, and the 0..1 progress within it. */
export const levelProgress = (xp = 0) => {
  const safe = Math.max(0, xp);
  const into = safe % 175;
  return { into, needed: 175, ratio: into / 175, toNext: 175 - into };
};

/** Cosmetic "gems" currency derived from XP (no separate persistence yet). */
export const gemsFromXp = (xp = 0) => Math.floor(Math.max(0, xp) / 50);
