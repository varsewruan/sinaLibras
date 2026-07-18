/**
 * Lesson score → star rating (0-3), the mockup's per-node medal row.
 *
 * The score is real, not decorative: `progress_service.complete_lesson`
 * keeps the BEST score the user ever got on a lesson, and it rides along on
 * every lesson in GET /learning/phases as `LessonSummary.score`. So a node's
 * stars only ever go up, and replaying a lesson can improve them even though
 * it awards no extra XP.
 *
 * Thresholds are deliberately generous at the bottom: passing at all
 * (>= 60%, PASS_THRESHOLD in the backend) already earns a star, so a
 * completed lesson never shows an empty row.
 */

export const STAR_THRESHOLDS = [
  { min: 90, stars: 3 },
  { min: 70, stars: 2 },
  { min: 0, stars: 1 },
];

/**
 * @param {{completed?: boolean, score?: number|null}} lesson
 * @returns {number} 0-3. Zero means "not completed yet" — an attempted but
 *   failed lesson scores no stars, since `completed` is what the backend
 *   flips at the pass threshold.
 */
export const starsFor = (lesson) => {
  if (!lesson?.completed) return 0;
  const score = lesson.score ?? 0;
  return STAR_THRESHOLDS.find((t) => score >= t.min)?.stars ?? 1;
};
