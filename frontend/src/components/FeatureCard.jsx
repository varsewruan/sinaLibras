/**
 * Glowing navy tile used by the Home hub (FASES / OBJETIVOS / RANKING) and
 * the Aprender hub (ALFABETO / QUIZ / ...).
 *
 * `soon` renders the tile as an inert, dimmed card with an "Em breve" badge —
 * used for the mockup's features that have no backend yet. It stays a
 * <button> so keyboard users still get feedback instead of a dead <div>.
 */
import { Link } from "react-router-dom";
import clsx from "clsx";
import { toast } from "sonner";

const base =
  "group relative flex h-full flex-col items-start gap-2 rounded-2xl p-5 text-left " +
  "bg-gradient-to-br from-[#17305c] to-[#101f3f] ring-1 ring-white/10 transition-all";

export const FeatureCard = ({ icon: Icon, iconColor, title, description, to, soon = false, testId }) => {
  const body = (
    <>
      <Icon
        className="w-8 h-8 mb-1"
        style={{ color: soon ? "#64748b" : iconColor }}
        strokeWidth={2.5}
        aria-hidden="true"
      />
      <h3 className="text-base font-black uppercase tracking-wide text-white">{title}</h3>
      <p className="text-xs leading-snug text-white/55">{description}</p>
      {soon && (
        <span className="absolute top-3 right-3 rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white/60">
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
        onClick={() => toast(`${title} chega em breve`, { description: "Estamos construindo essa parte. 🚧" })}
        className={clsx(base, "opacity-60 hover:opacity-80 cursor-pointer")}
      >
        {body}
      </button>
    );
  }

  return (
    <Link
      to={to}
      data-testid={testId}
      className={clsx(base, "shadow-glow hover:-translate-y-1 hover:ring-primary/50 hover:brightness-110")}
    >
      {body}
    </Link>
  );
};
