/**
 * Renders a user's avatar as a gradient disc + emoji (see lib/avatars).
 * Falls back to the "dummy" preset when the user has no avatar set, so the
 * UI never shows an empty circle.
 *
 * `accessory` (id vindo da loja) desenha um segundo emoji encavalado na borda
 * de cima do disco — chapéu, óculos, coroa. Fica fora do fluxo do disco de
 * propósito: dentro dele o acessório teria que dividir espaço com a cara do
 * bicho e os dois virariam um borrão em tamanho 40px.
 */
import clsx from "clsx";

import { accessoryEmoji } from "@/lib/accessories";
import { avatarById, DEFAULT_AVATAR } from "@/lib/avatars";

export const UserAvatar = ({ avatar, accessory, size = 40, className, ring = false }) => {
  const preset = avatarById(avatar || DEFAULT_AVATAR);
  const badge = accessoryEmoji(accessory);

  return (
    <span
      className={clsx("relative inline-flex shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <span
        className={clsx(
          "inline-flex h-full w-full select-none items-center justify-center rounded-full",
          ring && "ring-2 ring-white/70 shadow-glow"
        )}
        style={{
          fontSize: size * 0.55,
          background: `linear-gradient(160deg, ${preset.from}, ${preset.to})`,
        }}
        aria-hidden="true"
      >
        {preset.emoji}
      </span>

      {badge && (
        <span
          className="pointer-events-none absolute left-1/2 -translate-x-1/2 select-none leading-none"
          style={{
            // Encosta na borda superior do disco, levemente por fora.
            top: -size * 0.28,
            fontSize: size * 0.5,
            filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.5))",
          }}
          aria-hidden="true"
        >
          {badge}
        </span>
      )}
    </span>
  );
};
