/**
 * Synthetic feedback sounds via the Web Audio API.
 *
 * Why synth instead of audio files?
 *   - Zero asset weight (no .mp3/.ogg to ship).
 *   - Zero licensing concerns.
 *   - 100% gain control — easy to add a global mute later.
 *
 * Autoplay policy: browsers suspend AudioContext until a user gesture.
 * We lazily create the context on first call and resume() if suspended,
 * so the first click anywhere on the app unlocks audio.
 */

const AudioCtx = typeof window !== "undefined"
  ? (window.AudioContext || window.webkitAudioContext)
  : null;

let ctx = null;
let muted = false;

const getCtx = () => {
  if (!AudioCtx) return null;
  if (!ctx) ctx = new AudioCtx();
  if (ctx.state === "suspended") ctx.resume();
  return ctx;
};

export const setMuted = (value) => { muted = Boolean(value); };
export const isMuted = () => muted;

const beep = ({ freq, duration = 0.12, type = "sine", gainPeak = 0.12, delay = 0 }) => {
  if (muted) return;
  const c = getCtx();
  if (!c) return;
  const start = c.currentTime + delay;
  const osc = c.createOscillator();
  const gain = c.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  osc.connect(gain).connect(c.destination);
  gain.gain.setValueAtTime(0, start);
  gain.gain.linearRampToValueAtTime(gainPeak, start + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  osc.start(start);
  osc.stop(start + duration);
};

/** Quick high blip — used on correct answers. */
export const playCorrect = () => beep({ freq: 880, duration: 0.15 });

/** Lower, slightly buzzy tone for wrong answers. */
export const playWrong = () =>
  beep({ freq: 196, duration: 0.25, type: "sawtooth", gainPeak: 0.08 });

/** Arpejo C5 → E5 → G5 for lesson completion (passed). */
export const playComplete = () => {
  beep({ freq: 523, duration: 0.14, delay: 0 });
  beep({ freq: 659, duration: 0.14, delay: 0.13 });
  beep({ freq: 784, duration: 0.22, delay: 0.26 });
};
