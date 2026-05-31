/**
 * Home — contextual landing.
 *
 * Pulls phases and picks the first not-yet-completed lesson as a "Continue
 * de onde parou" CTA. Falls back to "Começar do início" when the catalog
 * hasn't been touched, or "Tudo concluído" when every lesson is done.
 */

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BookCheck, BookOpen, Search } from "lucide-react";

import { AppShell } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { usePhases } from "@/lib/hooks/useLearning";

const Welcome = ({ name }) => (
  <Card className="overflow-hidden border-border/70">
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
      className="bg-gradient-to-br from-primary/20 via-accent/10 to-transparent p-8 space-y-4"
    >
      <p className="text-xs font-bold uppercase tracking-wider text-primary">
        Bem-vindo de volta
      </p>
      <h2 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
        Olá, <span className="text-primary">{name}</span> 👋
      </h2>
      <p className="text-muted-foreground max-w-xl">
        Pronto(a) para a próxima lição? Vamos manter sua sequência viva.
      </p>
    </motion.div>
  </Card>
);

const ContinueCardSkeleton = () => (
  <Card><CardContent className="p-8 space-y-3">
    <Skeleton className="h-4 w-32" />
    <Skeleton className="h-7 w-64" />
    <Skeleton className="h-10 w-40 mt-4" />
  </CardContent></Card>
);

const findNext = (phases) => {
  for (const phase of phases) {
    for (const lesson of phase.lessons) {
      if (!lesson.completed) return { phase, lesson };
    }
  }
  return null;
};

const ContinueCard = ({ next }) => {
  if (!next) {
    return (
      <Card className="ring-2 ring-primary shadow-glow overflow-hidden">
        <CardContent className="p-8 text-center space-y-3">
          <BookCheck className="w-12 h-12 mx-auto text-primary" strokeWidth={2.5} />
          <h3 className="text-2xl font-black">Você concluiu tudo!</h3>
          <p className="text-muted-foreground">Mais conteúdo vem em breve. Enquanto isso, revise no dicionário.</p>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card className="overflow-hidden border-border/70">
      <div className="bg-gradient-to-br from-primary/20 via-accent/10 to-transparent p-8 space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-primary">
          <BookOpen className="w-4 h-4" strokeWidth={2.5} />
          Fase {next.phase.order} — {next.phase.title}
        </div>
        <h3 className="text-2xl sm:text-3xl font-black">Continue: {next.lesson.title}</h3>
        <Button asChild variant="glow3d" size="lg" className="font-bold uppercase tracking-wider px-8" data-testid="continue-cta">
          <Link to={`/lesson/${next.lesson.id}`}>
            Continuar <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </Button>
      </div>
    </Card>
  );
};

const PreviewCard = ({ icon: Icon, color, title, description, to }) => (
  <Card className="border-2 border-border/60 hover:border-primary/60 transition-all hover:-translate-y-1 cursor-pointer">
    <Link to={to} className="block">
      <CardHeader>
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center mb-3"
          style={{ background: `${color}22`, color }}
        >
          <Icon className="w-6 h-6" strokeWidth={2.5} />
        </div>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Link>
  </Card>
);

export default function Home() {
  const { user } = useAuth();
  const { data: phases, isLoading } = usePhases();
  const next = phases ? findNext(phases) : null;

  return (
    <AppShell title="Início">
      <div className="space-y-8">
        <Welcome name={user?.name?.split(" ")[0]} />
        {isLoading ? <ContinueCardSkeleton /> : <ContinueCard next={next} />}
        <div className="grid sm:grid-cols-2 gap-4">
          <PreviewCard
            icon={BookOpen} color="#0446b0"
            title="Caminho completo"
            description="Veja todas as fases e lições disponíveis no seu currículo."
            to="/lessons"
          />
          <PreviewCard
            icon={Search} color="#0446b0"
            title="Dicionário de sinais"
            description="Busque por termo em português e veja a representação do sinal."
            to="/dictionary"
          />
        </div>
      </div>
    </AppShell>
  );
}
