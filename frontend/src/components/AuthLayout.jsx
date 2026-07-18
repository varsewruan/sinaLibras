/**
 * Shared chrome for the two logged-out screens (Login / Register).
 *
 * The app shell isn't available here — there's no user, so no Header, no
 * Sidebar. This gives those screens the same visual language anyway: navy
 * canvas, dot grid, drifting hand outlines, and the two-tone wordmark over a
 * glowing card.
 *
 * DELIBERATELY ROUTER-FREE. Login.test.jsx renders <Login/> with
 * react-router-dom mocked down to Link/useNavigate/useLocation and no Router
 * in the tree; importing anything else from the router here would break it.
 * Callers pass their own <Link> in via `footer`.
 */

import { motion } from "framer-motion";

import { DecorHands } from "@/components/DecorHands";
import { Wordmark } from "@/components/Wordmark";

export const AuthLayout = ({ title, subtitle, children, footer }) => (
  <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
    {/* Ornamental layers, same pair the Home hub uses. */}
    <div className="pointer-events-none absolute inset-0 bg-dots opacity-30" aria-hidden="true" />
    <DecorHands />

    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="relative w-full max-w-md"
    >
      <div className="mb-8 flex flex-col items-center gap-2">
        <Wordmark className="text-4xl sm:text-5xl" />
        <p className="text-sm font-bold text-white/50">{subtitle}</p>
      </div>

      <div className="rounded-3xl bg-card-glow px-6 py-8 shadow-glow ring-1 ring-white/10 sm:px-8">
        <h2 className="mb-6 text-center text-xl font-black tracking-tight text-white">
          {title}
        </h2>
        {children}
        {footer && <div className="mt-6 text-center text-sm text-white/50">{footer}</div>}
      </div>
    </motion.div>
  </div>
);

/**
 * One labelled input. `hint` renders under the field (used for the password
 * length rule); `children` is the <Input/> so callers keep full control of
 * its props and testid.
 */
export const AuthField = ({ id, label, hint, children }) => (
  <div className="space-y-1.5">
    <label
      htmlFor={id}
      className="text-xs font-black uppercase tracking-wider text-white/60"
    >
      {label}
    </label>
    {children}
    {hint && <p className="text-xs text-white/40">{hint}</p>}
  </div>
);

/**
 * Shared input styling — taller than the shadcn default, filled navy so the
 * field reads as an inset well on the card, with the brand blue focus ring.
 */
export const authInputClass =
  "h-11 rounded-xl border-white/10 bg-[#0d1c3d] px-4 text-base text-white " +
  "placeholder:text-white/30 transition-colors focus-visible:border-primary/60 " +
  "focus-visible:ring-2 focus-visible:ring-primary/40";
