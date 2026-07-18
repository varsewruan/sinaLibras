import { Fragment } from "react";

import { Skeleton } from "@/components/ui/skeleton";

// Mirrors the serpentine in pages/Lessons.jsx so there's no layout jump.
// The spacing must mirror it too: the real path uses a tight gap-3 and lets
// the 72px <PathConnector/> supply the rhythm, so a plain gap-16 here would
// render a visibly shorter trail than the one that replaces it.
const OFFSETS = [0, 56, 84, 56, 0, -56, -84, -56];
const CONNECTOR_H = 72;

/** Loading placeholder shaped like the Path. */
export const PathSkeleton = () => (
  <div className="mx-auto max-w-lg space-y-10" aria-hidden="true">
    {Array.from({ length: 2 }).map((_, phase) => (
      <div key={phase} className="space-y-8">
        <Skeleton className="h-[86px] w-full rounded-2xl" />
        <div className="flex flex-col items-center gap-3">
          {Array.from({ length: 3 }).map((__, i) => (
            <Fragment key={i}>
              {i > 0 && <div style={{ height: CONNECTOR_H }} />}
              <div
                className="flex flex-col items-center gap-2"
                style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }}
              >
                <Skeleton className="h-[76px] w-[76px] rounded-full" />
                <Skeleton className="h-4 w-24 rounded-lg" />
              </div>
            </Fragment>
          ))}
        </div>
      </div>
    ))}
  </div>
);
