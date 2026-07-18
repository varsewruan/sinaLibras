/**
 * A sign's demo media: looping video where real footage exists, the themed SVG
 * placeholder everywhere else. Most of the catalog is still placeholders.
 *
 * Two encodes ship per filmed sign (backend/scripts/build_sign_videos.py):
 * WebM/VP9 carries a live alpha channel so the interpreter sits directly on
 * the card surface, and MP4/H.264 has the background pre-flattened for Safari,
 * which cannot decode VP9 alpha. <source> order is load-bearing — the browser
 * takes the first type it claims to support, so WebM must come first or
 * Chrome would settle for the flattened MP4.
 */

import { useReducedMotion } from "framer-motion";
import clsx from "clsx";

import { resolveSignUrl } from "@/lib/env";

export const SignMedia = ({
  sign,
  className = "",
  fallbackClassName = "aspect-video",
  fallbackLabel = "Sem prévia",
}) => {
  const reduceMotion = useReducedMotion();

  const webm = resolveSignUrl(sign?.video_webm_url);
  const mp4 = resolveSignUrl(sign?.video_url);
  const poster = resolveSignUrl(sign?.poster_url);
  const thumbnail = resolveSignUrl(sign?.thumbnail_url);
  const label = sign?.text_description || `Sinal: ${sign?.portuguese_term ?? ""}`;

  if (webm || mp4) {
    return (
      <video
        className={className}
        poster={poster || undefined}
        // <video> has no alt; the accessible name has to be spelled out.
        aria-label={label}
        // Clips run 1-1.6s. Looping lets a learner watch the gesture over and
        // over without hunting for a replay control.
        loop
        muted
        playsInline
        // Autoplaying motion is hostile to someone who asked for less of it.
        // They get the poster frame and real controls instead.
        autoPlay={!reduceMotion}
        controls={reduceMotion}
        preload="metadata"
        data-testid="sign-video"
      >
        {webm && <source src={webm} type="video/webm" />}
        {mp4 && <source src={mp4} type="video/mp4" />}
      </video>
    );
  }

  if (thumbnail) {
    return (
      <img
        src={thumbnail}
        alt={label}
        className={className}
        loading="lazy"
        data-testid="sign-image"
      />
    );
  }

  return (
    <div
      className={clsx(
        "flex items-center justify-center text-muted-foreground text-sm",
        fallbackClassName,
      )}
    >
      {fallbackLabel}
    </div>
  );
};
