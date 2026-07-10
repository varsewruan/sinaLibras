import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

const fetchRanking = async (limit) =>
  (await api.get("/ranking", { params: { limit } })).data;

/** Top players by XP + the caller's own row (pinned even when off-list). */
export const useRanking = (limit = 20) =>
  useQuery({ queryKey: ["ranking", limit], queryFn: () => fetchRanking(limit) });
