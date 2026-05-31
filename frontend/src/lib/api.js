/**
 * Shared axios instance + 401 → refresh interceptor.
 *
 * Auth tokens live in httpOnly cookies set by the backend. `withCredentials`
 * tells the browser to include them on every request. The 401 interceptor
 * tries `/auth/refresh` once; if that succeeds it replays the original
 * request transparently; if it fails it surfaces the error so the UI can
 * redirect to /login.
 *
 * A single in-flight refresh promise is shared across concurrent 401s so
 * we never fire two refresh requests at once (which would also rotate
 * tokens twice and confuse the backend).
 */

import axios from "axios";
import { API_URL } from "@/lib/env";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 15_000,
  withCredentials: true,
});

let refreshPromise = null;
const subscribers = new Set();

/** Optional: subscribe to logout events triggered by a refresh failure. */
export const onAuthFailure = (handler) => {
  subscribers.add(handler);
  return () => subscribers.delete(handler);
};

const notifyAuthFailure = () => {
  for (const handler of subscribers) {
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

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
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
