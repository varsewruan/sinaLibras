/**
 * First not-yet-completed lesson across the ordered phases, or null when the
 * whole catalog is done. Drives the "JOGAR" / "COMEÇAR" CTAs and the
 * "CONTINUAR" bubble on the learning path — they must all agree on which
 * lesson is "next", so the rule lives here once.
 */
export const findNextLesson = (phases = []) => {
  for (const phase of phases) {
    for (const lesson of phase.lessons) {
      if (!lesson.completed) return { phase, lesson };
    }
  }
  return null;
};
