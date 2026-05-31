import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

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
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="w-full max-w-md"
      >
        <Card className="border-border shadow-2xl">
          <CardHeader className="text-center space-y-2">
            <CardTitle className="text-3xl font-black tracking-tight">
              Bem-vindo(a)!
            </CardTitle>
            <CardDescription>Crie sua conta em segundos</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <div className="space-y-1.5">
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name" type="text" required autoComplete="name"
                  value={name} onChange={(e) => setName(e.target.value)}
                  data-testid="register-name"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email" type="email" required autoComplete="email"
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  data-testid="register-email"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password" type="password" required minLength={8} autoComplete="new-password"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  data-testid="register-password"
                />
                <p className="text-xs text-muted-foreground">Mínimo de 8 caracteres.</p>
              </div>

              {error && (
                <p
                  role="alert" aria-live="polite"
                  className="text-sm text-destructive font-medium"
                  data-testid="register-error"
                >
                  {error}
                </p>
              )}

              <Button
                type="submit" disabled={pending}
                className="w-full font-bold uppercase tracking-wider"
                data-testid="register-submit"
              >
                {pending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Criar conta"}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              Já tem conta?{" "}
              <Link to="/login" className="text-primary font-bold hover:underline">
                Entrar
              </Link>
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
