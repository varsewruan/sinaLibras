import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const fetchPhases = async () => (await api.get("/learning/phases")).data;
const fetchLesson = async (id) => (await api.get(`/learning/lessons/${id}`)).data;
const fetchSummary = async () => (await api.get("/progress/me/summary")).data;
const completeLessonFn = (body) => api.post("/progress/complete-lesson", body).then((r) => r.data);

export const usePhases = () =>
  useQuery({ queryKey: ["phases"], queryFn: fetchPhases });

export const useLesson = (id) =>
  useQuery({ queryKey: ["lesson", id], queryFn: () => fetchLesson(id), enabled: Boolean(id) });

export const useSummary = () =>
  useQuery({ queryKey: ["summary"], queryFn: fetchSummary });

export const useCompleteLesson = () => {
  const qc = useQueryClient();
  const { refresh } = useAuth(); // re-hydrate /me so the Header XP/streak updates instantly
  return useMutation({
    mutationFn: completeLessonFn,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["phases"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      // XP/streak/lesson-count all moved, so the derived views are stale.
      qc.invalidateQueries({ queryKey: ["achievements"] });
      qc.invalidateQueries({ queryKey: ["ranking"] });
      refresh();
    },
  });
};
