/**
 * Layout wrapper for every authenticated page.
 *
 * Composition:
 *   <Sidebar />            – fixed left, lg+ only
 *   <BottomNav />          – fixed bottom, mobile only
 *   <main>
 *     <Header />           – sticky top (identity + XP/gems)
 *     {children}
 *   </main>
 *
 * The pl-64 on <main> matches the sidebar width; pb-20 on mobile leaves
 * room for the bottom nav so content isn't covered.
 *
 * `title` names the page in the browser tab — the Header shows the user's
 * identity instead of a page heading, matching the mockup.
 */

import { useEffect } from "react";

import { Sidebar } from "@/components/Sidebar";
import { BottomNav } from "@/components/BottomNav";
import { Header } from "@/components/Header";

const BRAND = "SINALibras";

export const AppShell = ({ title, children }) => {
  useEffect(() => {
    document.title = title ? `${title} · ${BRAND}` : BRAND;
  }, [title]);

  return (
    <div className="min-h-screen text-foreground">
      <Sidebar />
      <BottomNav />
      <div className="lg:pl-64 min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 pb-20 lg:pb-8">
          {/* Page-level enter/exit animation lives in App.js (AnimatePresence
              keyed by pathname), so this wrapper stays static. */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
