"use client";

import { Banknote } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Field, InlineAlert, Input } from "@/components/ui/primitives";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-950 via-slate-900 to-brand-900 p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Banknote className="h-6 w-6" />
          </div>
          <div>
            <p className="text-lg font-bold text-white">TaxBridge Brasil</p>
            <p className="text-[11px] uppercase tracking-widest text-slate-400">
              A ponte para a Reforma Tributária
            </p>
          </div>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-800">
          <h1 className="text-lg font-bold text-slate-900 dark:text-white">Entrar</h1>
          <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
            Acesse o painel de impacto da transição CBS/IBS/IS (2026–2033).
          </p>
          <form onSubmit={onSubmit} className="space-y-3">
            <Field label="E-mail">
              <Input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="voce@empresa.com.br"
                required
                autoFocus
              />
            </Field>
            <Field label="Senha">
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
              />
            </Field>
            {error && <InlineAlert>{error}</InlineAlert>}
            <Button type="submit" loading={loading} className="w-full">
              Entrar
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
            Ainda não tem conta?{" "}
            <Link href="/registro" className="font-semibold text-brand-600 hover:underline">
              Criar organização
            </Link>
          </p>
        </div>

        <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-4 text-xs text-slate-300">
          <p className="font-semibold text-slate-200">Ambiente de demonstração (após seed):</p>
          <p className="mt-1 font-mono text-[11px]">admin@demo.taxbridge.com.br · TaxBridge@2026</p>
        </div>
      </div>
    </div>
  );
}
