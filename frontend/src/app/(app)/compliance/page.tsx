"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus } from "lucide-react";
import { useState } from "react";
import { CompanySelect, useSelectedCompany } from "@/components/company-select";
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
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { AREA_LABELS, fmtDate, fmtPct, STATUS_LABELS } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { ComplianceSummary, ComplianceTask, Page } from "@/lib/types";

const STATUS_BADGE: Record<string, string> = {
  pendente: "neutral",
  em_andamento: "info",
  concluido: "success",
  vencido: "alto",
  critico: "critico",
};

export default function CompliancePage() {
  const { companies, companyId, select } = useSelectedCompany();
  const { level } = useAuth();
  const queryClient = useQueryClient();
  const [area, setArea] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ area: "fiscal", title: "", description: "", priority: "media", due_date: "" });
  const [message, setMessage] = useState("");

  const canWrite = level >= 40;
  const canApplyTemplate = level >= 70;

  const { data: summary } = useQuery({
    queryKey: ["compliance-summary", companyId],
    queryFn: () => api<ComplianceSummary>(`/compliance/summary?company_id=${companyId}`),
    enabled: !!companyId,
  });

  const { data: tasks, isLoading } = useQuery({
    queryKey: ["compliance-tasks", companyId, area, status, page],
    queryFn: () =>
      api<Page<ComplianceTask>>(
        `/compliance/tasks?company_id=${companyId}&page=${page}${area ? `&area=${area}` : ""}${status ? `&status=${status}` : ""}`,
      ),
    enabled: !!companyId,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["compliance-tasks"] });
    queryClient.invalidateQueries({ queryKey: ["compliance-summary"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const applyTemplate = useMutation({
    mutationFn: () => api<{ created: number }>("/compliance/apply-template", {
      method: "POST",
      body: JSON.stringify({ company_id: companyId }),
    }),
    onSuccess: (result) => {
      setMessage(`Checklist aplicado: ${result.created} tarefa(s) criada(s).`);
      invalidate();
    },
    onError: (err: Error) => setMessage(err.message),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) =>
      api(`/compliance/tasks/${id}`, { method: "PUT", body: JSON.stringify({ status: value }) }),
    onSuccess: invalidate,
  });

  const createTask = useMutation({
    mutationFn: () =>
      api("/compliance/tasks", {
        method: "POST",
        body: JSON.stringify({
          company_id: companyId,
          ...form,
          description: form.description || null,
          due_date: form.due_date || null,
        }),
      }),
    onSuccess: () => {
      setCreateOpen(false);
      setForm({ area: "fiscal", title: "", description: "", priority: "media", due_date: "" });
      invalidate();
    },
    onError: (err: Error) => setMessage(err.message),
  });

  return (
    <div>
      <PageHeader
        title="Compliance — checklist de adequação"
        description="Tarefas por área (fiscal, contábil, financeiro, jurídico, TI, vendas e compras) com prazos, responsáveis e painel de maturidade."
        actions={
          <>
            <CompanySelect companies={companies} value={companyId} onChange={select} />
            {canApplyTemplate && (
              <Button variant="secondary" onClick={() => applyTemplate.mutate()} loading={applyTemplate.isPending} disabled={!companyId}>
                <ClipboardList className="h-4 w-4" /> Aplicar checklist padrão
              </Button>
            )}
            {canWrite && (
              <Button onClick={() => setCreateOpen(true)} disabled={!companyId}>
                <Plus className="h-4 w-4" /> Nova tarefa
              </Button>
            )}
          </>
        }
      />

      {message && (
        <div className="mb-4">
          <InlineAlert tone={message.includes("aplicado") ? "success" : "error"}>{message}</InlineAlert>
        </div>
      )}

      {summary && (
        <Card
          title={`Maturidade fiscal: ${fmtPct(summary.overall_progress_pct, 0)}`}
          description={`${summary.done}/${summary.total} concluídas · ${summary.overdue} vencida(s) · ${summary.critical} crítica(s)`}
          className="mb-5"
        >
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
            {summary.by_area.map((row) => (
              <button
                key={row.area}
                onClick={() => { setArea(area === row.area ? "" : row.area); setPage(1); }}
                className={`rounded-lg border p-2 text-left transition-colors ${
                  area === row.area
                    ? "border-brand-500 bg-brand-50 dark:bg-brand-900/30"
                    : "border-slate-200 hover:border-brand-300 dark:border-slate-700"
                }`}
              >
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{AREA_LABELS[row.area]}</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white">{fmtPct(row.progress_pct, 0)}</p>
                <p className="text-[10px] text-slate-400">
                  {row.done}/{row.total} {row.overdue > 0 && <span className="text-red-500">· {row.overdue} vencida(s)</span>}
                </p>
              </button>
            ))}
          </div>
        </Card>
      )}

      <Card
        actions={
          <Select value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }} className="w-auto">
            <option value="">Todos os status</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        }
        title="Tarefas"
      >
        {!companyId ? (
          <EmptyState title="Selecione uma empresa" />
        ) : isLoading ? (
          <Spinner />
        ) : !tasks || tasks.items.length === 0 ? (
          <EmptyState
            title="Nenhuma tarefa encontrada"
            description='Use "Aplicar checklist padrão" para carregar as 21 tarefas recomendadas da Reforma.'
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Tarefa</Th>
                <Th>Área</Th>
                <Th>Prioridade</Th>
                <Th>Prazo</Th>
                <Th>Status</Th>
              </THead>
              <TBody>
                {tasks.items.map((task) => (
                  <tr key={task.id}>
                    <Td>
                      <p className="font-medium">{task.title}</p>
                      {task.description && (
                        <p className="max-w-xl text-[11px] text-slate-400">{task.description}</p>
                      )}
                    </Td>
                    <Td>
                      <Badge variant="neutral">{AREA_LABELS[task.area] ?? task.area}</Badge>
                    </Td>
                    <Td>
                      <Badge variant={task.priority === "alta" ? "alto" : task.priority === "media" ? "medio" : "baixo"}>
                        {task.priority}
                      </Badge>
                    </Td>
                    <Td className="text-xs">{fmtDate(task.due_date)}</Td>
                    <Td>
                      {canWrite ? (
                        <Select
                          value={task.status}
                          onChange={(event) => updateStatus.mutate({ id: task.id, value: event.target.value })}
                          className="w-auto py-1 text-xs"
                        >
                          {Object.entries(STATUS_LABELS).map(([value, label]) => (
                            <option key={value} value={value}>
                              {label}
                            </option>
                          ))}
                        </Select>
                      ) : (
                        <Badge variant={STATUS_BADGE[task.status]}>{STATUS_LABELS[task.status]}</Badge>
                      )}
                    </Td>
                  </tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={tasks.page} pageSize={tasks.page_size} total={tasks.total} onPage={setPage} />
          </>
        )}
      </Card>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Nova tarefa de adequação">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createTask.mutate();
          }}
          className="space-y-3"
        >
          <Field label="Título">
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </Field>
          <Field label="Descrição (opcional)">
            <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Área">
              <Select value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })}>
                {Object.entries(AREA_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Prioridade">
              <Select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                <option value="baixa">Baixa</option>
                <option value="media">Média</option>
                <option value="alta">Alta</option>
              </Select>
            </Field>
            <Field label="Prazo">
              <Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
            </Field>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createTask.isPending}>
              Criar tarefa
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
