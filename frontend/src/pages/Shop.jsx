/**
 * Loja — avatares e acessórios comprados com XP.
 *
 * O XP mostrado aqui é o SALDO (`xp_balance`), não o total. Comprar não
 * derruba ranking nem nível: o backend cobra de `xp_spent` e deixa `xp`
 * intacto (ver backend/app/models/shop.py). A tela deixa os dois números
 * visíveis pra que ninguém ache que "perdeu" XP ao comprar.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, Loader2, Lock, Star } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { AppShell } from "@/components/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { useEquip, usePurchase, useShop, useUnequip } from "@/lib/hooks/useShop";

const TABS = [
  { id: "avatar", label: "Avatares" },
  { id: "accessory", label: "Acessórios" },
];

const Price = ({ value }) => (
  <span className="inline-flex items-center gap-1 text-sm font-black text-brand-yellow">
    <Star className="h-3.5 w-3.5 fill-brand-yellow" strokeWidth={0} aria-hidden="true" />
    {value}
  </span>
);

const ItemCard = ({ item, balance, onBuy, onEquip, onUnequip, busy }) => {
  const affordable = balance >= item.price;
  const locked = !item.owned && !affordable;

  const action = item.equipped
    ? { label: "Usando", handler: item.kind === "accessory" ? onUnequip : null }
    : item.owned
      ? { label: "Usar", handler: onEquip }
      : { label: "Comprar", handler: affordable ? onBuy : null };

  return (
    <div
      data-testid={`shop-item-${item.id}`}
      data-owned={item.owned}
      className={clsx(
        "flex flex-col items-center gap-2 rounded-2xl p-4 ring-1 transition-all",
        item.equipped
          ? "bg-gradient-to-br from-[#2a3f18] to-[#16294f] ring-brand-yellow/60 shadow-glow-yellow"
          : "bg-gradient-to-br from-[#17305c] to-[#101f3f] ring-white/10",
        locked && "opacity-60"
      )}
    >
      <span className="text-4xl leading-none select-none" aria-hidden="true">
        {item.emoji}
      </span>
      <span className="text-center text-xs font-bold leading-tight text-white">
        {item.label}
      </span>

      {item.owned ? (
        <span className="flex items-center gap-1 text-[11px] font-black uppercase tracking-wide text-success">
          <Check className="h-3 w-3" strokeWidth={3} aria-hidden="true" />
          Seu
        </span>
      ) : (
        <Price value={item.price} />
      )}

      <button
        type="button"
        disabled={!action.handler || busy}
        onClick={action.handler ?? undefined}
        data-testid={`shop-action-${item.id}`}
        className={clsx(
          "mt-1 w-full rounded-lg px-2 py-1.5 text-[11px] font-black uppercase tracking-wide transition-all",
          item.equipped && "bg-brand-yellow/20 text-brand-yellow",
          !item.equipped && item.owned && "bg-primary text-white hover:brightness-110",
          !item.owned && affordable && "bg-brand-yellow text-[#0d1c3d] hover:brightness-105",
          !item.owned && !affordable && "bg-white/5 text-white/40",
          busy && "opacity-60"
        )}
      >
        {locked ? (
          <span className="inline-flex items-center gap-1">
            <Lock className="h-3 w-3" strokeWidth={3} aria-hidden="true" />
            Faltam {item.price - balance}
          </span>
        ) : (
          action.label
        )}
      </button>
    </div>
  );
};

export default function Shop() {
  const [tab, setTab] = useState("avatar");
  const { data, isLoading, isError } = useShop();
  const purchase = usePurchase();
  const equip = useEquip();
  const unequip = useUnequip();

  const busy = purchase.isPending || equip.isPending || unequip.isPending;

  const run = (mutation, arg, successMessage) =>
    mutation.mutate(arg, {
      onSuccess: () => toast.success(successMessage),
      onError: (error) =>
        toast.error(error?.response?.data?.detail?.message ?? "Não deu certo. Tente de novo."),
    });

  const items = (data?.items ?? []).filter((item) => item.kind === tab);

  return (
    <AppShell title="Loja">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-black text-white">Loja</h1>
            <p className="text-sm text-white/50">
              Troque seu XP por avatares e acessórios.
            </p>
          </div>

          {data && (
            <div
              className="rounded-2xl bg-[#0a1730] px-4 py-2 text-right ring-1 ring-white/10"
              data-testid="shop-balance"
            >
              <p className="flex items-center justify-end gap-1.5 text-xl font-black text-brand-yellow">
                <Star className="h-4 w-4 fill-brand-yellow" strokeWidth={0} aria-hidden="true" />
                {data.balance}
              </p>
              {/* Deixa explícito que o total não some ao comprar — senão
                  "gastei XP" lê como "perdi posição no ranking". */}
              <p className="text-[11px] font-bold text-white/40">
                saldo · {data.xp_total} XP ganhos no total
              </p>
            </div>
          )}
        </header>

        <div className="flex gap-2" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              data-testid={`shop-tab-${t.id}`}
              className={clsx(
                "rounded-full px-4 py-2 text-sm font-black uppercase tracking-wide transition-colors",
                tab === t.id
                  ? "bg-primary text-white shadow-glow"
                  : "bg-white/5 text-white/50 hover:text-white"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        {isError && (
          <p role="alert" className="text-destructive">
            Não foi possível carregar a loja. Tente recarregar a página.
          </p>
        )}

        {isLoading && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-40 rounded-2xl" />
            ))}
          </div>
        )}

        {data && (
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5"
          >
            {items.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                balance={data.balance}
                busy={busy}
                onBuy={() => run(purchase, item.id, `${item.label} é seu!`)}
                onEquip={() => run(equip, item.id, `${item.label} equipado`)}
                onUnequip={() => run(unequip, undefined, "Acessório removido")}
              />
            ))}
          </motion.div>
        )}

        {busy && (
          <p className="flex items-center gap-2 text-sm text-white/50" role="status">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Processando…
          </p>
        )}
      </div>
    </AppShell>
  );
}
