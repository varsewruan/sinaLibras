/**
 * "Ver em Libras" button — opens a modal with the sign's demo, at a size worth
 * opening a modal for.
 *
 * The VLibras 3D player was removed because the official gov.br dictionary
 * endpoint (https://www.vlibras.gov.br/dict-static/BR/<SIGN>) is currently
 * returning 403 with no public mirror, so the avatar had no animation data
 * to play. Filmed signs now cover part of the catalog; the rest still fall
 * back to the themed SVG, which SignMedia decides between.
 */

import { useState } from "react";
import { Hand } from "lucide-react";
import clsx from "clsx";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { SignMedia } from "@/components/SignMedia";

export const LibrasButton = ({ sign, className, size = "default" }) => {
  const [open, setOpen] = useState(false);
  const sizeClasses = size === "sm" ? "h-8 px-3 text-xs" : "h-10 px-4 text-sm";
  const term = sign?.portuguese_term ?? "";
  const hasVideo = Boolean(sign?.video_url || sign?.video_webm_url);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        data-testid="libras-button"
        aria-label={`Ver sinal de ${term} em Libras`}
        title={`Ver "${term}" em Libras`}
        className={clsx(
          "inline-flex items-center justify-center gap-2 rounded-xl font-bold border-2 transition-all",
          "bg-card text-foreground border-border hover:border-primary hover:bg-primary/5 active:scale-95",
          sizeClasses,
          className,
        )}
      >
        <Hand className="w-4 h-4" strokeWidth={2.5} aria-hidden="true" />
        <span>Ver em Libras</span>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-2xl font-black">{term}</DialogTitle>
            <DialogDescription>
              {hasVideo
                ? "Demonstração do sinal em vídeo"
                : "Representação visual do sinal"}
            </DialogDescription>
          </DialogHeader>
          <div className="rounded-xl overflow-hidden border border-border bg-muted">
            <SignMedia
              sign={sign}
              className="w-full h-auto block"
              fallbackLabel="Sem prévia disponível"
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
