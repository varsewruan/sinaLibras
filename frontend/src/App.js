import "@/index.css";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";

import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Toaster } from "@/components/ui/sonner";
import { queryClient } from "@/lib/query";
import Dictionary from "@/pages/Dictionary";
import Home from "@/pages/Home";
import Lesson from "@/pages/Lesson";
import Lessons from "@/pages/Lessons";
import Login from "@/pages/Login";
import Profile from "@/pages/Profile";
import Register from "@/pages/Register";

const Protected = ({ children }) => <ProtectedRoute>{children}</ProtectedRoute>;

/**
 * Wraps Routes so each pathname change is treated as an exit + enter pair.
 * `mode="wait"` ensures the old page finishes leaving before the new one enters.
 * `initial={false}` skips the entrance animation on the first paint (avoids a
 * flash when the SPA boots).
 */
const AnimatedRoutes = () => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
      >
        <Routes location={location}>
          <Route path="/login"        element={<Login />} />
          <Route path="/register"     element={<Register />} />
          <Route path="/"             element={<Protected><Home /></Protected>} />
          <Route path="/lessons"      element={<Protected><Lessons /></Protected>} />
          <Route path="/lesson/:id"   element={<Protected><Lesson /></Protected>} />
          <Route path="/dictionary"   element={<Protected><Dictionary /></Protected>} />
          <Route path="/profile"      element={<Protected><Profile /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AnimatedRoutes />
        </AuthProvider>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}

export default App;
