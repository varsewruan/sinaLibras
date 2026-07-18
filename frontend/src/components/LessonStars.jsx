/**
 * The 3-star medal row that straddles the bottom edge of a lesson node.
 *
 * Earned stars are the brand yellow with a soft halo; unearned ones are
 * hollow navy. The row is announced as a single label ("2 de 3 estrelas")
 * rather than three separate icons.
 */
import { Star } from "lucide-react";
import clsx from "clsx";

export const LessonStars = ({ earned, total = 3, size = 16 }) => (
  <span
    className="flex items-center justify-center gap-0.5"
    role="img"
    aria-label={`${earned} de ${total} estrelas`}
  >
    {Array.from({ length: total }, (_, i) => {
      const on = i < earned;
      return (
        <Star
          key={i}
          width={size}
          height={size}
          strokeWidth={2}
          aria-hidden="true"
          className={clsx(
            "transition-colors",
            on
              ? "fill-brand-yellow text-brand-yellow drop-shadow-[0_0_4px_rgba(255,198,26,0.7)]"
              : "fill-[#0f2547] text-white/20",
            // The middle star sits slightly higher, like the mockup's arc.
            i === 1 && "-translate-y-0.5"
          )}
        />
      );
    })}
  </span>
);
