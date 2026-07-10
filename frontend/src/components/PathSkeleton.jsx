import { Skeleton } from "@/components/ui/skeleton";

// Mirrors the serpentine in pages/Lessons.jsx so there's no layout jump.
const OFFSETS = [0, 56, 84, 56, 0, -56, -84, -56];

/** Loading placeholder shaped like the Path. */
export const PathSkeleton = () => (
  <div className="mx-auto max-w-lg space-y-10" aria-hidden="true">
    {Array.from({ length: 2 }).map((_, phase) => (
      <div key={phase} className="space-y-8">
        <Skeleton className="h-[86px] w-full rounded-2xl" />
        <div className="flex flex-col items-center gap-16">
          {Array.from({ length: 3 }).map((__, i) => (
            <div
              key={i}
              className="flex flex-col items-center gap-2"
              style={{ transform: `translateX(${OFFSETS[i % OFFSETS.length]}px)` }}
            >
              <Skeleton className="h-[76px] w-[76px] rounded-full" />
              <Skeleton className="h-3 w-24" />
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);
