import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const fetchSigns = async (q) => {
  const params = q ? `?q=${encodeURIComponent(q)}` : "?limit=50";
  return (await api.get(`/learning/signs${params}`)).data;
};

/**
 * Live sign search. Pass the *debounced* query — this hook doesn't debounce.
 * placeholderData keeps the previous result visible while a new one loads,
 * so the grid doesn't flash empty on every keystroke.
 */
export const useSearchSigns = (debouncedQuery) =>
  useQuery({
    queryKey: ["signs:search", debouncedQuery],
    queryFn: () => fetchSigns(debouncedQuery),
    placeholderData: keepPreviousData,
  });
