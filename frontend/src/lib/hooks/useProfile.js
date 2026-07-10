import { useMutation } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const updateAvatarFn = (avatar) =>
  api.patch("/users/me", { avatar }).then((r) => r.data);

/**
 * Persist the chosen avatar preset, then re-hydrate /auth/me so the top bar
 * and sidebar pick up the new face immediately.
 */
export const useUpdateAvatar = () => {
  const { refresh } = useAuth();
  return useMutation({
    mutationFn: updateAvatarFn,
    onSuccess: () => refresh(),
  });
};
