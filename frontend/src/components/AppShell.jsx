/**
 * Layout wrapper for every authenticated page.
 *
 * Composition:
 *   <Sidebar />            – fixed left, lg+ only
 *   <BottomNav />          – fixed bottom, mobile only
 *   <main>
 *     <Header />           – sticky top
 *     {children}
 *   </main>
 *
 * The pl-64 on <main> matches the sidebar width; pb-20 on mobile leaves
 * room for the bottom nav so content isn't covered.
 */

import { Sidebar } from "@/components/Sidebar";
import { BottomNav } from "@/components/BottomNav";
import { Header } from "@/components/Header";

export const AppShell = ({ title = "SINALibras", children }) => (
  <div className="min-h-screen text-foreground">
    <Sidebar />
    <BottomNav />
    <div className="lg:pl-64 min-h-screen flex flex-col">
      <Header title={title} />
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
