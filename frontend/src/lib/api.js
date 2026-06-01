/**
 * Shared axios instance with two response interceptors:
 *
 *   1. Cold-start recovery — on a network error (timeout / ECONNABORTED /
 *      "Network Error"), we poll /api/healthz with exponential backoff
 *      and replay the original request once the backend wakes up. Fly.io
 *      scales the machine to zero, so the first request after idle pays
 *      a 5-15s wake penalty. A single shared healthz poll handles every
 *      concurrent in-flight request. Subscribers (BootSplash) are
 *      notified so the UI can show a "waking server" state.
 *
 *   2. 401 → /auth/refresh — auth tokens live in httpOnly cookies set
 *      by the backend. On a 401 we try the refresh endpoint once; if
 *      that succeeds we replay; if it fails we emit onAuthFailure so
 *      the AuthContext can drop to anonymous and the UI to /login.
 *      A single in-flight refresh promise is shared across concurrent
 *      401s.
 */

import axios from "axios";
import { API_URL, BACKEND_URL } from "@/lib/env";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 15_000,
  withCredentials: true,
});

// ---------------------------------------------------------------------------
// Cold-start recovery
// ---------------------------------------------------------------------------

const coldStartSubscribers = new Set();
let coldStartActive = false;

/** Subscribe to "backend is waking up" events. Returns an unsubscribe fn. */
export const onColdStart = (handler) => {
  coldStartSubscribers.add(handler);
  // Push current state so a freshly mounted listener doesn't miss an
  // in-progress cold-start.
  handler(coldStartActive);
  return () => coldStartSubscribers.delete(handler);
};

const setColdStart = (active) => {
  if (active === coldStartActive) return;
  coldStartActive = active;
  for (const h of coldStartSubscribers) {
    try { h(active); } catch (_) { /* listeners must be defensive */ }
  }
};

const isNetworkError = (error) =>
  !error.response && (
    error.code === "ECONNABORTED" ||
    error.code === "ERR_NETWORK" ||
    error.message === "Network Error" ||
    /timeout/i.test(error.message || "")
  );

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Poll /api/healthz until it responds 200 or we've exhausted ~30s of attempts.
 * Backend cold-start on Fly is usually 5-15s.
 */
const pingHealthzUntilUp = async () => {
  let delay = 500;
  const deadline = Date.now() + 45_000;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${BACKEND_URL}/api/healthz`, {
        method: "GET",
        cache: "no-store",
        // Native fetch — bypass axios so this poll doesn't recurse into our
        // own interceptor. No credentials needed; healthz is public.
      });
      if (r.ok) return;
    } catch (_) {
      // network still down; back off and retry
    }
    await sleep(delay);
    delay = Math.min(Math.round(delay * 1.7), 4_000);
  }
  throw new Error("backend did not respond within 45s");
};

let wakePromise = null;
const waitForBackend = () => {
  if (!wakePromise) {
    setColdStart(true);
    wakePromise = pingHealthzUntilUp().finally(() => {
      wakePromise = null;
      setColdStart(false);
    });
  }
  return wakePromise;
};

// ---------------------------------------------------------------------------
// 401 → refresh
// ---------------------------------------------------------------------------

let refreshPromise = null;
const authFailureSubscribers = new Set();

/** Optional: subscribe to logout events triggered by a refresh failure. */
export const onAuthFailure = (handler) => {
  authFailureSubscribers.add(handler);
  return () => authFailureSubscribers.delete(handler);
};

const notifyAuthFailure = () => {
  for (const handler of authFailureSubscribers) {
    try { handler(); } catch (_) { /* swallow — listeners must be defensive */ }
  }
};

const refresh = () => {
  if (!refreshPromise) {
    refreshPromise = api
      .post("/auth/refresh")
      .finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
};

// ---------------------------------------------------------------------------
// Interceptors
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    // Cold-start path — no response means the network didn't reach the server.
    if (config && !config._coldStartRetry && isNetworkError(error)) {
      config._coldStartRetry = true;
      try {
        await waitForBackend();
      } catch (wakeErr) {
        return Promise.reject(error);
      }
      return api(config);
    }

    // 401 → refresh path.
    if (!response || response.status !== 401 || !config || config._retry) {
      return Promise.reject(error);
    }
    // Don't try to refresh on /auth/* endpoints — that would loop.
    if (config.url && config.url.startsWith("/auth/")) {
      return Promise.reject(error);
    }
    config._retry = true;
    try {
      await refresh();
    } catch (refreshErr) {
      notifyAuthFailure();
      return Promise.reject(error);
    }
    return api(config);
  }
);
