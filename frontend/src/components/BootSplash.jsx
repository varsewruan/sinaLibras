/**
 * Overlay shown while the backend is waking from Fly.io's scale-to-zero
 * idle state. Subscribes to onColdStart from @/lib/api, which fires when
 * the response interceptor catches a network error and starts polling
 * /api/healthz.
 *
 * Messaging escalates with elapsed time so the user has something to
 * read instead of staring at a static spinner:
 *   - 0-7s   "Acordando o servidor…"
 *   - 7-20s  "Está demorando um pouco mais hoje…"
 *   - 20s+   "Quase lá — só mais um instante…"
 */

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";

import { onColdStart } from "@/lib/api";

const MESSAGES = [
  { afterMs: 0,      text: "Acordando o servidor…" },
  { afterMs: 7_000,  text: "Está demorando um pouco mais hoje…" },
  { afterMs: 20_000, text: "Quase lá — só mais um instante…" },
];

const pickMessage = (elapsed) => {
  let chosen = MESSAGES[0].text;
  for (const { afterMs, text } of MESSAGES) {
    if (elapsed >= afterMs) chosen = text;
  }
  return chosen;
};

export const BootSplash = () => {
  const [active, setActive] = useState(false);
  const [startedAt, setStartedAt] = useState(null);
  const [message, setMessage] = useState(MESSAGES[0].text);

  useEffect(() => {
    const off = onColdStart((isActive) => {
      setActive(isActive);
      setStartedAt(isActive ? Date.now() : null);
      if (isActive) setMessage(MESSAGES[0].text);
    });
    return off;
  }, []);

  useEffect(() => {
    if (!active || startedAt == null) return undefined;
    const tick = () => setMessage(pickMessage(Date.now() - startedAt));
    const id = setInterval(tick, 1_000);
    tick();
    return () => clearInterval(id);
  }, [active, startedAt]);

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          // Fixed full-screen overlay above everything, so the user can't
          // interact with a stale UI mid-cold-start.
          className="fixed inset-0 z-[1000] flex flex-col items-center justify-center gap-6 bg-background/95 backdrop-blur-sm"
          role="status"
          aria-live="polite"
          data-testid="boot-splash"
        >
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 animate-spin text-primary" strokeWidth={2.5} />
            <p className="text-2xl font-black tracking-tight text-primary">SINALibras</p>
          </div>
          <motion.p
            key={message}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="text-sm text-muted-foreground max-w-xs text-center px-6"
            data-testid="boot-splash-message"
          >
            {message}
          </motion.p>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
