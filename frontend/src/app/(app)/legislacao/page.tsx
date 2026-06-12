"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Gavel, Plus } from "lucide-react";
import { useState } from "react";
import { Modal } from "@/components/ui/modal";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  InlineAlert,
  Input,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from "@/components/ui/primitives";
import { Pagination } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtDate, IMPACT_LABELS } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { LegalUpdate, Page } from "@/lib/types";

const NORM_LABELS: Record<string, string> = {
  lei: "Lei",
  lc: "Lei Complementar",
  decreto: "Decreto",
  nota_tecnica: "Nota Técnica",
  portaria: "Portaria",
  outro: "Outro",
};

const EMPTY = {
  norm_type: "lc",
  reference: "",
  title: "",
  summary: "",
  impact: "medio",
  source_url: "",
  published_at: "",
};

export default function LegislacaoPage() {
  const queryClient = useQueryClient();
  const { level } = useAuth();
  const [impact, setImpact] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["legal-updates", impact, page],
    queryFn: () => api<Page<LegalUpdate>>(`/legal-updates?page=${page}${impact ? `&impact=${impact}` : ""}`),
  });

  const create = useMutation({
    mutationFn: () =>
      api("/legal-updates", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          summary: form.summary || null,
          source_url: form.source_url || null,
          published_at: form.published_at || null,
        }),
      }),
    onSuccess: () => {
      setCreateOpen(false);
      setForm(EMPTY);
      setError("");
      queryClient.invalidateQueries({ queryKey: ["legal-updates"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div>
      <PageHeader
        title="Monitor legislativo"
        description="Normas da Reforma classificadas por impacto. Feed automático com resumo por IA chega na fase 6 do roadmap."
        actions={
          <>
            <Select value={impact} onChange={(event) => { setImpact(event.target.value); setPage(1); }} className="w-auto">
              <option value="">Todos os impactos</option>
              {Object.entries(IMPACT_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
            {level >= 60 && (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4" /> Cadastrar norma
              </Button>
            )}
          </>
        }
      />

      <div className="mb-4">
        <InlineAlert tone="info">
          As informações deste monitor são de <b>apoio</b> e não substituem parecer jurídico ou contábil profissional.
        </InlineAlert>
      </div>

      {isLoading ? (
        <Spinner />
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="Nenhuma norma cadastrada" description="Cadastre leis, decretos e notas técnicas relevantes." />
      ) : (
        <>
          <div className="space-y-3">
            {data.items.map((update) => (
              <Card key={update.id}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-lg bg-slate-100 p-2 dark:bg-slate-700">
                      <Gavel className="h-4 w-4 text-slate-500 dark:text-slate-300" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-800 dark:text-slate-100">{update.reference}</span>
                        <Badge variant="neutral">{NORM_LABELS[update.norm_type] ?? update.norm_type}</Badge>
                        <Badge variant={update.impact}>Impacto {IMPACT_LABELS[update.impact]}</Badge>
                        {update.published_at && (
                          <span className="text-[11px] text-slate-400">{fmtDate(update.published_at)}</span>
                        )}
                      </div>
                      <p className="mt-1 text-sm font-medium text-slate-700 dark:text-slate-200">{update.title}</p>
                      {update.summary && <p className="mt-1 max-w-3xl text-xs text-slate-500">{update.summary}</p>}
                    </div>
                  </div>
                  {update.source_url && (
                    <a
                      href={update.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline"
                    >
                      Fonte oficial <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
        </>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Cadastrar norma / atualização legal">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
          className="space-y-3"
        >
          <div className="grid grid-cols-2 gap-3">
            <Field label="Tipo">
              <Select value={form.norm_type} onChange={(e) => setForm({ ...form, norm_type: e.target.value })}>
                {Object.entries(NORM_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Referência" hint="Ex.: LC 214/2025">
              <Input value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} required />
            </Field>
          </div>
          <Field label="Título">
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </Field>
          <Field label="Resumo (opcional)">
            <Textarea value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Impacto">
              <Select value={form.impact} onChange={(e) => setForm({ ...form, impact: e.target.value })}>
                {Object.entries(IMPACT_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Publicação">
              <Input type="date" value={form.published_at} onChange={(e) => setForm({ ...form, published_at: e.target.value })} />
            </Field>
            <Field label="URL da fonte">
              <Input value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} />
            </Field>
          </div>
          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={create.isPending}>
              Cadastrar
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
