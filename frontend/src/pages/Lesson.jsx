/**
 * Interactive lesson — one sign per question, 4 multiple-choice options.
 *
 * Polish 2:
 *   • Synth sounds on correct / wrong / lesson-pass (zero asset weight).
 *   • Keyboard 1–4 picks the corresponding option (with visible <kbd> hints).
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Loader2, Trophy, X, Zap } from "lucide-react";
import clsx from "clsx";

import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useCompleteLesson, useLesson } from "@/lib/hooks/useLearning";
import { playComplete, playCorrect, playWrong } from "@/lib/audio";
import { SignMedia } from "@/components/SignMedia";
import { LessonStars } from "@/components/LessonStars";
import { starsFor } from "@/lib/stars";

// ---------- helpers ---------------------------------------------------------

const shuffle = (arr) => {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
};

const buildQuestions = (signs) =>
  signs.map((sign) => {
    const others = signs.filter((s) => s.id !== sign.id);
    const distractors = shuffle(others).slice(0, 3).map((s) => s.portuguese_term);
    while (distractors.length < 3) distractors.push("—");
    const options = shuffle([sign.portuguese_term, ...distractors]);
    return { sign, options, correct: sign.portuguese_term };
  });

// ---------- subcomponents ---------------------------------------------------

const Intro = ({ lesson, onStart }) => (
  <Card>
    <CardContent className="py-12 text-center space-y-6">
      <h2 className="text-3xl font-black tracking-tight">{lesson.title}</h2>
      <p className="text-muted-foreground max-w-md mx-auto">
        {lesson.signs.length} sinais nesta lição. Acerte pelo menos 60% para concluir.
        <br />
        <span className="text-xs">Dica: use as teclas <Kbd>1</Kbd>–<Kbd>4</Kbd> para responder.</span>
      </p>
      <Button onClick={onStart} variant="yellow3d" size="lg"
              className="font-bold uppercase tracking-wider px-10"
              data-testid="lesson-start">
        Iniciar lição
      </Button>
    </CardContent>
  </Card>
);

const Kbd = ({ children }) => (
  <kbd className="inline-flex items-center justify-center min-w-[1.5rem] h-6 px-1.5 rounded-md bg-muted border border-border text-[11px] font-bold text-muted-foreground font-mono">
    {children}
  </kbd>
);

const Question = ({ question, index, total, onAnswer }) => {
  const [picked, setPicked] = useState(null);
  const isCorrect = picked === question.correct;

  const pick = (option) => {
    if (picked) return;
    setPicked(option);
    const correct = option === question.correct;
    (correct ? playCorrect : playWrong)();
    setTimeout(() => onAnswer(correct), 750);
  };

  // Keyboard 1..N picks the option at that index (1-based for human ergonomics).
  useEffect(() => {
    const onKey = (e) => {
      if (picked) return;
      const n = parseInt(e.key, 10);
      if (Number.isInteger(n) && n >= 1 && n <= question.options.length) {
        pick(question.options[n - 1]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [picked, question]);

  return (
    <motion.div
      key={index}
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -24 }}
      transition={{ duration: 0.25 }}
    >
      <Card>
        <CardContent className="p-6 space-y-6">
          <div className="aspect-video bg-muted rounded-xl overflow-hidden flex items-center justify-center">
            <SignMedia
              sign={question.sign}
              className="w-full h-full object-cover"
              fallbackClassName="w-full h-full"
              fallbackLabel="Sem imagem"
            />
          </div>
          <h3 className="text-xl font-bold text-center">Qual é este sinal?</h3>
          <div className="grid grid-cols-2 gap-3" aria-keyshortcuts="1 2 3 4">
            {question.options.map((opt, i) => {
              const isPickedOption = picked === opt;
              const showCorrect = picked && opt === question.correct;
              const showWrong = isPickedOption && !isCorrect;
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => pick(opt)}
                  disabled={!!picked}
                  data-testid={`option-${opt}`}
                  className={clsx(
                    "relative px-4 py-4 rounded-xl border-2 font-bold text-base transition-all text-left flex items-center gap-3",
                    !picked && "border-border hover:border-accent hover:-translate-y-0.5",
                    showCorrect && "border-success bg-success/10 text-success",
                    showWrong   && "border-destructive bg-destructive/10 text-destructive",
                    picked && !showCorrect && !showWrong && "border-border opacity-50"
                  )}
                >
                  <Kbd>{i + 1}</Kbd>
                  <span className="flex-1">{opt}</span>
                  {showCorrect && isPickedOption && (
                    <span
                      aria-hidden="true"
                      className="absolute -top-2 right-2 text-success font-black text-lg pointer-events-none animate-xp-burst"
                    >
                      +1
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const Result = ({ score, awardedXp, passed, onRetry }) => {
  useEffect(() => {
    if (passed) playComplete();
  }, [passed]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardContent className="py-12 text-center space-y-6">
          <div
            className={clsx(
              "w-20 h-20 mx-auto rounded-full flex items-center justify-center",
              passed ? "bg-success/15 text-success" : "bg-destructive/15 text-destructive"
            )}
          >
            {passed ? <Trophy className="w-10 h-10" strokeWidth={2.5} /> : <X className="w-10 h-10" strokeWidth={3} />}
          </div>
          <div>
            <h2 className="text-3xl font-black">{passed ? "Mandou bem!" : "Quase lá!"}</h2>
            <p className="mt-2 text-muted-foreground">
              Você acertou <span className="font-bold text-foreground">{score}%</span> dos sinais.
            </p>
          </div>

          {/* Same star rating the path node will show — earned here, so the
              user sees what they just unlocked before seeing it on the map. */}
          <div className="flex justify-center">
            <LessonStars earned={starsFor({ completed: passed, score })} size={36} />
          </div>
          {awardedXp > 0 && (
            <motion.div
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-xp/15 text-xp"
            >
              <Zap className="w-5 h-5" strokeWidth={2.5} /> +{awardedXp} XP
            </motion.div>
          )}
          <div className="flex gap-3 justify-center pt-4">
            <Button asChild variant="outline">
              <Link to="/lessons" data-testid="back-to-lessons">Voltar</Link>
            </Button>
            {!passed && (
              <Button onClick={onRetry} variant="default3d" data-testid="retry">
                Tentar de novo
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

// ---------- main ------------------------------------------------------------

export default function Lesson() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: lesson, isLoading, isError } = useLesson(id);
  const complete = useCompleteLesson();

  const [stage, setStage] = useState("intro");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);

  const questions = useMemo(() => (lesson ? buildQuestions(lesson.signs) : []), [lesson]);

  if (isLoading) {
    return (
      <AppShell title="Lição">
        <div className="flex items-center gap-2 text-muted-foreground" role="status">
          <Loader2 className="w-4 h-4 animate-spin" /> Carregando lição…
        </div>
      </AppShell>
    );
  }
  if (isError || !lesson) {
    return (
      <AppShell title="Lição">
        <p role="alert" className="text-destructive">Lição não encontrada.</p>
        <Button onClick={() => navigate("/lessons")} className="mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" /> Voltar
        </Button>
      </AppShell>
    );
  }

  const reset = () => {
    setStage("intro");
    setQuestionIndex(0);
    setCorrectCount(0);
    complete.reset();
  };

  const onAnswer = (correct) => {
    const nextCorrect = correctCount + (correct ? 1 : 0);
    setCorrectCount(nextCorrect);
    const next = questionIndex + 1;
    if (next >= questions.length) {
      const score = Math.round((nextCorrect / questions.length) * 100);
      complete.mutate({ lesson_id: lesson.id, score });
      setStage("result");
    } else {
      setQuestionIndex(next);
    }
  };

  const progressPct =
    stage === "playing" ? Math.round((questionIndex / questions.length) * 100) :
    stage === "result"  ? 100 : 0;

  return (
    <AppShell title={lesson.title}>
      <div className="max-w-2xl mx-auto space-y-4">
        {stage !== "intro" && (
          <div className="flex items-center gap-3">
            <Button
              variant="ghost" size="icon"
              onClick={() => navigate("/lessons")}
              aria-label="Voltar para a lista de lições"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <Progress
              value={progressPct}
              className="flex-1 [&>div]:bg-gradient-to-r [&>div]:from-primary [&>div]:to-accent"
              aria-label={`Progresso da lição: ${progressPct}%`}
            />
            <span className="text-sm font-bold text-muted-foreground tabular-nums shrink-0">
              {Math.min(questionIndex + 1, questions.length)} / {questions.length}
            </span>
          </div>
        )}

        {stage === "intro" && (
          <Intro lesson={lesson} onStart={() => setStage("playing")} />
        )}
        {stage === "playing" && questions[questionIndex] && (
          <AnimatePresence mode="wait">
            <Question
              key={questionIndex}
              question={questions[questionIndex]}
              index={questionIndex}
              total={questions.length}
              onAnswer={onAnswer}
            />
          </AnimatePresence>
        )}
        {stage === "result" && (
          <Result
            score={Math.round((correctCount / questions.length) * 100)}
            awardedXp={complete.data?.awarded_xp ?? 0}
            passed={complete.data?.passed ?? false}
            onRetry={reset}
          />
        )}
      </div>
    </AppShell>
  );
}
