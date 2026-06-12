"use client";

import { Banknote } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, Field, InlineAlert, Input } from "@/components/ui/primitives";
import { useAuth } from "@/lib/auth";

export default function RegistroPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ organization_name: "", name: "", email: "", password: "" });
  const [lgpd, setLgpd] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field: keyof typeof form) {
    return (event: React.ChangeEvent<HTMLInputElement>) =>
      setForm((current) => ({ ...current, [field]: event.target.value }));
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    if (!lgpd) {
      setError("É necessário aceitar a política de privacidade (LGPD).");
      return;
    }
    setLoading(true);
    try {
      await register({ ...form, lgpd_consent: lgpd });
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no cadastro");
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
          <p className="text-lg font-bold text-white">TaxBridge Brasil</p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-800">
          <h1 className="text-lg font-bold text-slate-900 dark:text-white">Criar organização</h1>
          <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
            14 dias de avaliação gratuita. Sem cartão de crédito.
          </p>
          <form onSubmit={onSubmit} className="space-y-3">
            <Field label="Nome da organização (empresa ou escritório)">
              <Input value={form.organization_name} onChange={update("organization_name")} required minLength={2} />
            </Field>
            <Field label="Seu nome">
              <Input value={form.name} onChange={update("name")} required minLength={2} />
            </Field>
            <Field label="E-mail">
              <Input type="email" value={form.email} onChange={update("email")} required />
            </Field>
            <Field label="Senha" hint="Mínimo de 8 caracteres.">
              <Input type="password" value={form.password} onChange={update("password")} required minLength={8} />
            </Field>
            <label className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
              <input
                type="checkbox"
                checked={lgpd}
                onChange={(event) => setLgpd(event.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-slate-300"
              />
              <span>
                Li e aceito a Política de Privacidade e o tratamento de dados conforme a LGPD
                (Lei 13.709/2018). Dados fiscais são tratados sob contrato como operador.
              </span>
            </label>
            {error && <InlineAlert>{error}</InlineAlert>}
            <Button type="submit" loading={loading} className="w-full">
              Criar conta
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-slate-500 dark:text-slate-400">
            Já tem conta?{" "}
            <Link href="/login" className="font-semibold text-brand-600 hover:underline">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
