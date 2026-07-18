/**
 * The SINALibras wordmark from the hub mockup.
 *
 * Two-tone on purpose: "SINA" in the brand yellow, "Libras" in the brand
 * blue. The mockup renders it all-blue, but the blue/yellow split is what
 * makes the pairing read as a brand rather than as a blue app with yellow
 * highlights — it's the same move Gartic makes with its logo.
 *
 * Decorative: the accessible name is carried by the <h1>, and the halves are
 * hidden from assistive tech so a screen reader doesn't hear "SINA Libras"
 * as two words.
 */

export const Wordmark = ({ className = "" }) => (
  <h1
    className={`text-center font-black leading-none tracking-tight ${className}`}
    aria-label="SINALibras"
  >
    <span
      aria-hidden="true"
      className="text-brand-yellow [text-shadow:0_0_28px_rgba(255,198,26,0.45)]"
    >
      SINA
    </span>
    <span
      aria-hidden="true"
      className="text-[#4a97ff] [text-shadow:0_0_28px_rgba(47,127,240,0.55)]"
    >
      Libras
    </span>
  </h1>
);
