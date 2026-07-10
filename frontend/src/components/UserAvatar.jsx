/**
 * Renders a user's avatar as a gradient disc + emoji (see lib/avatars).
 * Falls back to the "dummy" preset when the user has no avatar set, so the
 * UI never shows an empty circle.
 */
import clsx from "clsx";

import { avatarById, DEFAULT_AVATAR } from "@/lib/avatars";

export const UserAvatar = ({ avatar, size = 40, className, ring = false }) => {
  const preset = avatarById(avatar || DEFAULT_AVATAR);
  return (
    <span
      className={clsx(
        "inline-flex items-center justify-center rounded-full select-none shrink-0",
        ring && "ring-2 ring-white/70 shadow-glow",
        className
      )}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.55,
        background: `linear-gradient(160deg, ${preset.from}, ${preset.to})`,
      }}
      aria-hidden="true"
    >
      {preset.emoji}
    </span>
  );
};
