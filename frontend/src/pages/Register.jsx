import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/context/AuthContext";
import { AuthField, AuthLayout, authInputClass } from "@/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setPending(true);
    try {
      await register({ email, name, password });
      navigate("/", { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      // 422 from FastAPI is an array of validation errors; everything else is { code, message }.
      const message = Array.isArray(detail)
        ? detail[0]?.msg ?? "Dados inválidos."
        : detail?.message ?? "Falha ao criar conta.";
      setError(message);
      toast.error(message);
    } finally {
      setPending(false);
    }
  };

  return (
    <AuthLayout
      subtitle="Crie sua conta em segundos"
      title="Criar conta"
      footer={
        <>
          Já tem conta?{" "}
          <Link to="/login" className="font-bold text-primary hover:underline">
            Entrar
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <AuthField id="name" label="Nome">
          <Input
            id="name" type="text" required autoComplete="name"
            className={authInputClass}
            value={name} onChange={(e) => setName(e.target.value)}
            data-testid="register-name"
          />
        </AuthField>

        <AuthField id="email" label="E-mail">
          <Input
            id="email" type="email" required autoComplete="email"
            className={authInputClass}
            value={email} onChange={(e) => setEmail(e.target.value)}
            data-testid="register-email"
          />
        </AuthField>

        <AuthField id="password" label="Senha" hint="Mínimo de 8 caracteres.">
          <Input
            id="password" type="password" required minLength={8} autoComplete="new-password"
            className={authInputClass}
            value={password} onChange={(e) => setPassword(e.target.value)}
            data-testid="register-password"
          />
        </AuthField>

        {error && (
          <p
            role="alert" aria-live="polite"
            className="rounded-lg bg-destructive/15 px-3 py-2 text-sm font-bold text-[#ffb4b4] ring-1 ring-destructive/40"
            data-testid="register-error"
          >
            {error}
          </p>
        )}

        {/* The only action on the screen, so it gets the yellow. */}
        <Button
          type="submit" disabled={pending}
          variant="yellow3d"
          className="h-12 w-full text-base font-black uppercase tracking-wider"
          data-testid="register-submit"
        >
          {pending ? <Loader2 className="h-5 w-5 animate-spin" /> : "Criar conta"}
        </Button>
      </form>
    </AuthLayout>
  );
}
