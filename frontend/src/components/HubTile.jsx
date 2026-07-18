/**
 * A single tile in the Home hub grid — big centered icon over an uppercase
 * label, matching the 6-up grid in the mockup.
 *
 * Distinct from <FeatureCard/>, which is the left-aligned card with a
 * description used by the Aprender hub. These stayed separate rather than
 * becoming one component with a layout flag: they share no structure beyond
 * "icon + words in a rounded box", and merging them would mean a prop that
 * rewrites the whole body.
 *
 * `soon` renders an inert dimmed tile with an "Em breve" badge, kept as a
 * <button> so keyboard users get feedback instead of hitting a dead <div>.
 */
import { Link } from "react-router-dom";
import clsx from "clsx";
import { toast } from "sonner";

const base =
  "group relative flex aspect-[4/3] flex-col items-center justify-center gap-3 rounded-2xl " +
  "bg-gradient-to-br from-[#17305c] to-[#101f3f] ring-1 ring-white/10 transition-all";

export const HubTile = ({ icon: Icon, tone = "blue", title, to, soon = false, testId }) => {
  const iconColor = soon ? "#64748b" : tone === "yellow" ? "#FFC61A" : "#3b8bff";

  const body = (
    <>
      <Icon
        className="h-12 w-12 sm:h-14 sm:w-14 transition-transform group-hover:scale-110"
        style={{ color: iconColor }}
        strokeWidth={2}
        aria-hidden="true"
      />
      <span className="text-sm font-black uppercase tracking-wide text-white sm:text-base">
        {title}
      </span>
      {soon && (
        <span className="absolute right-3 top-3 rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white/60">
          Em breve
        </span>
      )}
    </>
  );

  if (soon) {
    return (
      <button
        type="button"
        data-testid={testId}
        onClick={() =>
          toast(`${title} chega em breve`, { description: "Estamos construindo essa parte. 🚧" })
        }
        className={clsx(base, "cursor-pointer opacity-60 hover:opacity-80")}
      >
        {body}
      </button>
    );
  }

  return (
    <Link
      to={to}
      data-testid={testId}
      className={clsx(
        base,
        "shadow-glow hover:-translate-y-1 hover:brightness-110",
        // The hover halo follows the tile's own tone, so the yellow tiles
        // stay yellow on interaction instead of snapping to the blue ring.
        tone === "yellow"
          ? "hover:ring-brand-yellow/50 hover:shadow-glow-yellow"
          : "hover:ring-primary/50 hover:shadow-glow-lg"
      )}
    >
      {body}
    </Link>
  );
};
