import { motion } from "framer-motion";
import { BookCheck, Flame, LogOut, Trophy, Zap } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { useSummary } from "@/lib/hooks/useLearning";

const StatCard = ({ icon: Icon, color, label, value }) => (
  <Card>
    <CardContent className="p-6 flex items-center gap-4">
      <div
        className="w-12 h-12 rounded-2xl flex items-center justify-center"
        style={{ background: `${color}22`, color }}
      >
        <Icon className="w-6 h-6" strokeWidth={2.5} />
      </div>
      <div>
        <p className="text-xs uppercase tracking-wider text-muted-foreground font-bold">{label}</p>
        <p className="text-2xl font-black tabular-nums">{value}</p>
      </div>
    </CardContent>
  </Card>
);

const StatCardSkeleton = () => (
  <Card>
    <CardContent className="p-6 flex items-center gap-4">
      <Skeleton className="w-12 h-12 rounded-2xl" />
      <div className="space-y-2 flex-1">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-6 w-16" />
      </div>
    </CardContent>
  </Card>
);

export default function Profile() {
  const { user, logout } = useAuth();
  const { data: summary, isLoading } = useSummary();

  if (!user) return null;

  return (
    <AppShell title="Perfil">
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <Card>
          <CardHeader className="flex flex-row items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-accent/30 text-primary flex items-center justify-center text-2xl font-black uppercase">
              {user.name?.[0] ?? "?"}
            </div>
            <div>
              <CardTitle className="text-2xl">{user.name}</CardTitle>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </CardHeader>
        </Card>

        <div className="grid sm:grid-cols-2 gap-4">
          {isLoading ? (
            <>
              <StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton />
            </>
          ) : (
            <>
              <StatCard icon={Zap}        color="#7C3AED" label="XP total"            value={user.xp ?? 0} />
              <StatCard icon={Flame}      color="#EA580C" label="Sequência atual"     value={user.streak?.current ?? 0} />
              <StatCard icon={Trophy}     color="#CA8A04" label="Maior sequência"     value={user.streak?.longest ?? 0} />
              <StatCard icon={BookCheck}  color="#16A34A" label="Lições concluídas"   value={summary?.lessons_completed ?? 0} />
            </>
          )}
        </div>

        <Card>
          <CardContent className="p-6">
            <Button
              onClick={logout}
              variant="outline"
              className="w-full font-bold"
              data-testid="profile-logout"
            >
              <LogOut className="w-4 h-4 mr-2" /> Sair
            </Button>
          </CardContent>
        </Card>
      </motion.div>
    </AppShell>
  );
}
