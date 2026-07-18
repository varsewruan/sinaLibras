/**
 * The dashed trail segment drawn between two consecutive lesson nodes.
 *
 * Geometry is derived from the two nodes' serpentine offsets rather than
 * measured from the DOM, which is what keeps it exact: Lessons.jsx owns the
 * OFFSETS table, so it already knows where both endpoints sit. A cubic
 * bezier with vertical control handles gives the lazy S-curve of the mockup
 * instead of a straight diagonal.
 *
 * Purely decorative — hidden from assistive tech, since the path's meaning
 * is already carried by each node's own state label.
 */

const WIDTH = 260;   // enough to cover the ±84px offset range plus stroke
// The connector *is* the vertical rhythm between nodes — Lessons.jsx uses a
// tight flex gap and lets this height do the spacing, so the dashes run the
// full distance instead of floating in the middle of a large gap. Tall
// enough to clear the CONTINUAR bubble that overhangs the node below.
const HEIGHT = 72;

export const PathConnector = ({ fromOffset = 0, toOffset = 0 }) => {
  const cx = WIDTH / 2;
  const x1 = cx + fromOffset;
  const x2 = cx + toOffset;
  // Control points pulled straight down/up so the curve leaves and enters
  // each node vertically — a diagonal exit reads as a kink.
  const d = `M ${x1} 0 C ${x1} ${HEIGHT * 0.5}, ${x2} ${HEIGHT * 0.5}, ${x2} ${HEIGHT}`;

  return (
    <svg
      width={WIDTH}
      height={HEIGHT}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="pointer-events-none shrink-0 overflow-visible"
      aria-hidden="true"
      focusable="false"
    >
      {/* Chunky capsules, not dots: the mockup's trail reads as a dashed road.
          With a round cap the drawn dash runs ~strokeWidth longer than the
          array says, so the gap is padded to keep the dashes separate. */}
      <path
        d={d}
        fill="none"
        stroke="rgba(255,255,255,0.38)"
        strokeWidth={7}
        strokeLinecap="round"
        strokeDasharray="11 15"
      />
    </svg>
  );
};
