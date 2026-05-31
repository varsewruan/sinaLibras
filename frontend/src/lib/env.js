/**
 * Runtime environment access.
 *
 * REACT_APP_BACKEND_URL contract:
 *   - undefined  → boot error (dev/CI misconfig)
 *   - ""         → same-origin (single-host prod deploy: SPA + API on same domain)
 *   - "http://…" → split-host dev (CRA dev server at :3000, FastAPI at :8000)
 *
 * CRA inlines process.env.REACT_APP_* at build time. An unset variable
 * becomes JS `undefined`; an explicitly empty one becomes the string "".
 */

const raw = process.env.REACT_APP_BACKEND_URL;

if (raw === undefined) {
  throw new Error(
    "[env] REACT_APP_BACKEND_URL must be defined at build time. " +
    "Set it to an empty string for same-origin deploys, or to the API URL for split-host dev."
  );
}

export const BACKEND_URL = raw.replace(/\/+$/, "");
export const API_URL = `${BACKEND_URL}/api`;

/**
 * Resolve a sign asset URL (manifest entry from the backend) into something
 * the browser can fetch.
 *   - Absolute (https://…) URLs pass through (e.g. an external CDN).
 *   - Backend-relative paths (/signs/ola.svg) get prefixed with BACKEND_URL,
 *     so split-host dev (CRA :3000 → API :8000) and same-origin prod
 *     (BACKEND_URL = "") both work.
 *   - Anything falsy returns null so callers can render a "Sem prévia" state.
 */
export const resolveSignUrl = (url) => {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("/")) return `${BACKEND_URL}${url}`;
  return url;
};
