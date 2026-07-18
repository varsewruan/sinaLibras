import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/context/AuthContext";
import { AuthField, AuthLayout, authInputClass } from "@/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setPending(true);
    try {
      await login({ email, password });
      const next = location.state?.from || "/";
      navigate(next, { replace: true });
    } catch (err) {
      const message = err?.response?.data?.detail?.message ?? "Falha ao entrar.";
      setError(message);
      toast.error(message);
    } finally {
      setPending(false);
    }
  };

  return (
    <AuthLayout
      subtitle="Entre para continuar sua jornada"
      title="Entrar"
      footer={
        <>
          Não tem conta?{" "}
          <Link to="/register" className="font-bold text-primary hover:underline">
            Criar conta
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <AuthField id="email" label="E-mail">
          <Input
            id="email" type="email" required autoComplete="email"
            className={authInputClass}
            value={email} onChange={(e) => setEmail(e.target.value)}
            data-testid="login-email"
          />
        </AuthField>

        <AuthField id="password" label="Senha">
          <Input
            id="password" type="password" required autoComplete="current-password"
            className={authInputClass}
            value={password} onChange={(e) => setPassword(e.target.value)}
            data-testid="login-password"
          />
        </AuthField>

        {error && (
          <p
            role="alert" aria-live="polite"
            className="rounded-lg bg-destructive/15 px-3 py-2 text-sm font-bold text-[#ffb4b4] ring-1 ring-destructive/40"
            data-testid="login-error"
          >
            {error}
          </p>
        )}

        {/* The only action on the screen, so it gets the yellow. */}
        <Button
          type="submit" disabled={pending}
          variant="yellow3d"
          className="h-12 w-full text-base font-black uppercase tracking-wider"
          data-testid="login-submit"
        >
          {pending ? <Loader2 className="h-5 w-5 animate-spin" /> : "Entrar"}
        </Button>
      </form>
    </AuthLayout>
  );
}
