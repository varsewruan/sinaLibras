/**
 * Wrap a route element to require authentication.
 *
 * While the AuthContext is still hydrating, we render a tiny placeholder
 * instead of redirecting — otherwise an authed user briefly bounces to
 * /login on every full page refresh.
 */

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export const ProtectedRoute = ({ children }) => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <div style={{ padding: 24 }}>Carregando…</div>;
  }
  if (status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
};
