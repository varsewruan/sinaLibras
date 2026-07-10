import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

const fetchAchievements = async () => (await api.get("/achievements/me")).data;

/** The catalog evaluated against the current user (unlocked + progress). */
export const useAchievements = () =>
  useQuery({ queryKey: ["achievements"], queryFn: fetchAchievements });
