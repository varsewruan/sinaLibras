/**
 * Sinal dictionary — searchable grid.
 *
 * The empty query returns the first 50 signs (a useful "browse" mode),
 * so the page is never blank. Search is debounced; previous results stay
 * on screen during a new request to avoid flicker.
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Search } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/lib/hooks/useDebouncedValue";
import { useSearchSigns } from "@/lib/hooks/useSearchSigns";
import { LibrasButton } from "@/components/LibrasButton";
import { SignMedia } from "@/components/SignMedia";

const SignCard = ({ sign, index }) => {
  return (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: Math.min(index * 0.02, 0.3), duration: 0.2 }}
  >
    <Card className="overflow-hidden hover:border-accent transition-colors h-full">
      <div className="aspect-video bg-muted overflow-hidden">
        <SignMedia
          sign={sign}
          className="w-full h-full object-cover"
          fallbackClassName="w-full h-full"
        />
      </div>
      <CardContent className="p-4 space-y-3">
        <h3 className="font-bold text-lg">{sign.portuguese_term}</h3>
        {sign.text_description && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {sign.text_description}
          </p>
        )}
        <LibrasButton sign={sign} size="sm" className="w-full" />
      </CardContent>
    </Card>
  </motion.div>
  );
};

const GridSkeleton = () => (
  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" aria-hidden="true">
    {Array.from({ length: 6 }).map((_, i) => (
      <Card key={i} className="overflow-hidden">
        <Skeleton className="aspect-video rounded-none" />
        <CardContent className="p-4 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-3 w-full" />
        </CardContent>
      </Card>
    ))}
  </div>
);

export default function Dictionary() {
  const [q, setQ] = useState("");
  const debounced = useDebouncedValue(q, 300);
  const { data: signs, isLoading, isFetching, isError } = useSearchSigns(debounced);

  return (
    <AppShell title="Dicionário">
      <div className="space-y-6">
        <div className="relative max-w-xl">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none"
            aria-hidden="true"
            strokeWidth={2.5}
          />
          <Input
            type="search"
            placeholder="Buscar um termo em português…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="pl-11 h-12 text-base"
            aria-label="Buscar sinais"
            data-testid="dictionary-search"
          />
          {isFetching && !isLoading && (
            <Loader2
              className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground animate-spin"
              aria-hidden="true"
            />
          )}
        </div>

        {isError && (
          <p role="alert" className="text-destructive">
            Falha ao buscar sinais. Tente recarregar.
          </p>
        )}

        {isLoading && <GridSkeleton />}

        {signs && signs.length === 0 && (
          <p className="text-muted-foreground" role="status" aria-live="polite">
            Nenhum sinal encontrado para “{debounced}”.
          </p>
        )}

        {signs && signs.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {signs.map((sign, i) => (
              <SignCard key={sign.id} sign={sign} index={i} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
