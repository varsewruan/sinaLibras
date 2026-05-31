/**
 * Shared React Query client. Defaults are tuned for an SPA with cookie auth:
 *   - No refetch on window focus by default (annoying when typing).
 *   - 30s stale time (most lists don't change that fast).
 *   - Retry once on network errors only — not on 4xx (those are deterministic).
 */

import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error?.response?.status >= 400 && error?.response?.status < 500) return false;
        return failureCount < 1;
      },
    },
    mutations: {
      retry: false,
    },
  },
});
