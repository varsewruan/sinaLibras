/**
 * AuthContext — single source of truth for "who is the current user".
 *
 * On mount, we ask `/auth/me`. A 401 means "not logged in" — not an error,
 * just a state. After login/register the backend already returns the user
 * in the response body, so we don't need a second round-trip.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, onAuthFailure } from "@/lib/api";

const AuthContext = createContext(null);

const initialState = {
  user: null,
  status: "loading", // "loading" | "authenticated" | "anonymous"
};

export const AuthProvider = ({ children }) => {
  const [state, setState] = useState(initialState);

  const hydrate = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setState({ user: data, status: "authenticated" });
    } catch (err) {
      // 401 is expected when not logged in.
      setState({ user: null, status: "anonymous" });
    }
  }, []);

  useEffect(() => {
    hydrate();
    // Refresh failure (e.g. user logged out elsewhere) → drop to anonymous.
    return onAuthFailure(() => setState({ user: null, status: "anonymous" }));
  }, [hydrate]);

  const login = useCallback(async ({ email, password }) => {
    const { data } = await api.post("/auth/login", { email, password });
    setState({ user: data.user, status: "authenticated" });
    return data.user;
  }, []);

  const register = useCallback(async ({ email, name, password }) => {
    const { data } = await api.post("/auth/register", { email, name, password });
    setState({ user: data.user, status: "authenticated" });
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } finally {
      setState({ user: null, status: "anonymous" });
    }
  }, []);

  const value = useMemo(
    () => ({ ...state, login, register, logout, refresh: hydrate }),
    [state, login, register, logout, hydrate]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
};
