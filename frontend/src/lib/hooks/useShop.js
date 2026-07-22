import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const fetchShop = async () => (await api.get("/shop/items")).data;

/**
 * Catálogo + estado do usuário (saldo, o que já tem, o que está vestindo).
 * O backend é quem decide tudo isso; aqui não há cálculo de preço nem de
 * saldo, justamente pra não existirem duas versões da regra.
 */
export const useShop = () => useQuery({ queryKey: ["shop"], queryFn: fetchShop });

/**
 * Invalida o que a compra/equipamento mexe e re-hidrata o /me.
 *
 * `refresh()` importa: o saldo e o avatar vivem no AuthContext, que alimenta
 * o topo da tela. Sem isso a pílula de XP e o avatar do header ficariam
 * mostrando o estado anterior até a próxima navegação.
 */
const useShopMutation = (mutationFn) => {
  const qc = useQueryClient();
  const { refresh } = useAuth();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["shop"] });
      qc.invalidateQueries({ queryKey: ["ranking"] });
      refresh();
    },
  });
};

export const usePurchase = () =>
  useShopMutation((itemId) => api.post("/shop/purchase", { item_id: itemId }).then((r) => r.data));

export const useEquip = () =>
  useShopMutation((itemId) => api.post("/shop/equip", { item_id: itemId }).then((r) => r.data));

export const useUnequip = () =>
  useShopMutation(() => api.post("/shop/unequip").then((r) => r.data));
