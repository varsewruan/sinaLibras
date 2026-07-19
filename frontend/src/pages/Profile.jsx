import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { BookCheck, Flame, LogOut, ShoppingCart, Star, Trophy } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { UserAvatar } from "@/components/UserAvatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { useSummary } from "@/lib/hooks/useLearning";
import { useShop } from "@/lib/hooks/useShop";
import { useUpdateAvatar } from "@/lib/hooks/useProfile";
import { DEFAULT_AVATAR } from "@/lib/avatars";
import { levelFromXp, levelProgress } from "@/lib/level";

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

/**
 * Só mostra os avatares que a pessoa realmente tem.
 *
 * Antes listava o catálogo inteiro, o que virou armadilha quando avatares
 * passaram a ser comprados: o backend recusa equipar um avatar não comprado
 * (403), então metade dos botões daria erro. Quem decide o que aparece é o
 * `owned` que a loja devolve — a mesma fonte que o backend usa pra validar.
 */
const AvatarPicker = ({ current }) => {
  const { mutate, isPending, variables } = useUpdateAvatar();
  const { data: shop, isLoading } = useShop();

  const choose = (id) => {
    if (id === current || isPending) return;
    mutate(id, {
      onSuccess: () => toast.success("Avatar atualizado!"),
      onError: () => toast.error("Não foi possível trocar o avatar."),
    });
  };

  const owned = (shop?.items ?? []).filter((i) => i.kind === "avatar" && i.owned);
  const lockedCount = (shop?.items ?? []).filter((i) => i.kind === "avatar" && !i.owned).length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="text-lg">Escolha seu avatar</CardTitle>
        <Button asChild variant="outline" size="sm">
          <Link to="/shop" data-testid="profile-to-shop">
            <ShoppingCart className="mr-1.5 h-4 w-4" />
            Loja
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-20 w-full rounded-2xl" />
        ) : (
          <>
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-3">
              {owned.map((a) => {
                const selected = a.id === current;
                const pending = isPending && variables === a.id;
                return (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => choose(a.id)}
                    disabled={isPending}
                    aria-pressed={selected}
                    aria-label={a.label}
                    data-testid={`avatar-${a.id}`}
                    className={clsx(
                      "flex flex-col items-center gap-1.5 rounded-2xl p-2 transition-all",
                      "hover:bg-white/5 disabled:cursor-not-allowed",
                      selected && "bg-primary/15 ring-2 ring-primary",
                      pending && "animate-pulse"
                    )}
                  >
                    <UserAvatar avatar={a.id} size={48} />
                    <span className="text-[10px] font-bold text-muted-foreground truncate max-w-full">
                      {a.label}
                    </span>
                  </button>
                );
              })}
            </div>

            {lockedCount > 0 && (
              <p className="mt-4 text-xs text-muted-foreground">
                Mais {lockedCount} avatares esperando na{" "}
                <Link to="/shop" className="font-bold text-primary hover:underline">
                  loja
                </Link>
                .
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default function Profile() {
  const { user, logout } = useAuth();
  const { data: summary, isLoading } = useSummary();

  if (!user) return null;

  const xp = user.xp ?? 0;
  const level = levelFromXp(xp);
  const { into, needed, toNext } = levelProgress(xp);

  return (
    <AppShell title="Perfil">
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <Card>
          <CardHeader className="flex flex-row items-center gap-5">
            <UserAvatar
              avatar={user.avatar ?? DEFAULT_AVATAR}
              accessory={user.accessory}
              size={80}
              ring
            />
            <div className="min-w-0 flex-1">
              <CardTitle className="text-2xl truncate">{user.name}</CardTitle>
              <p className="text-sm text-muted-foreground truncate">{user.email}</p>

              <div className="mt-3 space-y-1.5">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-primary">Nível {String(level).padStart(2, "0")}</span>
                  <span className="text-muted-foreground">
                    faltam {toNext} XP
                  </span>
                </div>
                <div
                  className="h-2.5 w-full rounded-full bg-white/10 overflow-hidden"
                  role="progressbar"
                  aria-valuenow={into}
                  aria-valuemin={0}
                  aria-valuemax={needed}
                  aria-label={`Progresso para o nível ${level + 1}`}
                >
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
                    style={{ width: `${(into / needed) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </CardHeader>
        </Card>

        <AvatarPicker current={user.avatar ?? DEFAULT_AVATAR} />

        <div className="grid sm:grid-cols-2 gap-4">
          {isLoading ? (
            <>
              <StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton /><StatCardSkeleton />
            </>
          ) : (
            <>
              <StatCard icon={Star}       color="#FFC61A" label="XP total"          value={xp} />
              <StatCard icon={Flame}      color="#FB923C" label="Sequência atual"   value={user.streak?.current ?? 0} />
              <StatCard icon={Trophy}     color="#38BDF8" label="Maior sequência"   value={user.streak?.longest ?? 0} />
              <StatCard icon={BookCheck}  color="#34D399" label="Lições concluídas" value={summary?.lessons_completed ?? 0} />
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
