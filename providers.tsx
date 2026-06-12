"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
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
} from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtPct } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { Page, TaxRule } from "@/lib/types";

const EMPTY_RULE = {
  name: "",
  item_kind: "product",
  ncm_pattern: "",
  nbs_pattern: "",
  cfop: "",
  uf_origin: "",
  uf_dest: "",
  tax_regime: "",
  priority: "0",
  icms_rate: "0",
  iss_rate: "0",
  pis_rate: "0",
  cofins_rate: "0",
  ipi_rate: "0",
  cbs_rate: "",
  ibs_rate: "",
  is_rate: "0",
  cbs_reduction_pct: "0",
  ibs_reduction_pct: "0",
  credit_allowed: true,
  legal_basis: "",
};

type RuleForm = typeof EMPTY_RULE;

function ruleToForm(rule: TaxRule): RuleForm {
  return {
    name: rule.name,
    item_kind: rule.item_kind,
    ncm_pattern: rule.ncm_pattern ?? "",
    nbs_pattern: rule.nbs_pattern ?? "",
    cfop: rule.cfop ?? "",
    uf_origin: rule.uf_origin ?? "",
    uf_dest: rule.uf_dest ?? "",
    tax_regime: rule.tax_regime ?? "",
    priority: String(rule.priority),
    icms_rate: String(rule.icms_rate),
    iss_rate: String(rule.iss_rate),
    pis_rate: String(rule.pis_rate),
    cofins_rate: String(rule.cofins_rate),
    ipi_rate: String(rule.ipi_rate),
    cbs_rate: rule.cbs_rate === null ? "" : String(rule.cbs_rate),
    ibs_rate: rule.ibs_rate === null ? "" : String(rule.ibs_rate),
    is_rate: String(rule.is_rate),
    cbs_reduction_pct: String(rule.cbs_reduction_pct),
    ibs_reduction_pct: String(rule.ibs_reduction_pct),
    credit_allowed: rule.credit_allowed,
    legal_basis: rule.legal_basis ?? "",
  };
}

function formToPayload(form: RuleForm) {
  const orNull = (value: string) => (value.trim() === "" ? null : value.trim());
  return {
    name: form.name,
    item_kind: form.item_kind,
    ncm_pattern: orNull(form.ncm_pattern),
    nbs_pattern: orNull(form.nbs_pattern),
    cfop: orNull(form.cfop),
    uf_origin: orNull(form.uf_origin),
    uf_dest: orNull(form.uf_dest),
    tax_regime: orNull(form.tax_regime),
    priority: Number(form.priority || 0),
    icms_rate: form.icms_rate || "0",
    iss_rate: form.iss_rate || "0",
    pis_rate: form.pis_rate || "0",
    cofins_rate: form.cofins_rate || "0",
    ipi_rate: form.ipi_rate || "0",
    cbs_rate: orNull(form.cbs_rate),
    ibs_rate: orNull(form.ibs_rate),
    is_rate: form.is_rate || "0",
    cbs_reduction_pct: form.cbs_reduction_pct || "0",
    ibs_reduction_pct: form.ibs_reduction_pct || "0",
    credit_allowed: form.credit_allowed,
    legal_basis: orNull(form.legal_basis),
  };
}

export default function RegrasPage() {
  const queryClient = useQueryClient();
  const { level } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<TaxRule | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<RuleForm>(EMPTY_RULE);
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["tax-rules", page, search],
    queryFn: () => api<Page<TaxRule>>(`/tax-rules?page=${page}&search=${encodeURIComponent(search)}`),
  });

  const canWrite = level >= 60;

  const save = useMutation({
    mutationFn: () =>
      editing
        ? api(`/tax-rules/${editing.id}`, { method: "PUT", body: JSON.stringify(formToPayload(form)) })
        : api("/tax-rules", { method: "POST", body: JSON.stringify(formToPayload(form)) }),
    onSuccess: () => {
      setModalOpen(false);
      setEditing(null);
      setForm(EMPTY_RULE);
      setError("");
      queryClient.invalidateQueries({ queryKey: ["tax-rules"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api(`/tax-rules/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tax-rules"] }),
  });

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_RULE);
    setError("");
    setModalOpen(true);
  }

  function openEdit(rule: TaxRule) {
    setEditing(rule);
    setForm(ruleToForm(rule));
    setError("");
    setModalOpen(true);
  }

  const set = (field: keyof RuleForm) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [field]: event.target.value });

  return (
    <div>
      <PageHeader
        title="Regras tributárias"
        description="Regras parametrizáveis por NCM/NBS/CFOP/UF: alíquotas atuais, CBS/IBS/IS, reduções e exceções. Nada é hardcoded — tudo editável aqui."
        actions={
          canWrite && (
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> Nova regra
            </Button>
          )
        }
      />

      <Card>
        <div className="mb-4 max-w-xs">
          <Input
            placeholder="Buscar regra..."
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>
        {isLoading ? (
          <Spinner />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma regra cadastrada"
            description="Sem regras o motor não calcula: itens sem regra geram alerta de divergência de parametrização."
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Regra</Th>
                <Th>Escopo</Th>
                <Th right>Atual (ICMS/ISS · PIS · Cofins)</Th>
                <Th right>Futuro (CBS · IBS · IS)</Th>
                <Th right>Reduções</Th>
                <Th>Prior.</Th>
                {canWrite && <Th right>Ações</Th>}
              </THead>
              <TBody>
                {data.items.map((rule) => (
                  <tr key={rule.id}>
                    <Td>
                      <p className="font-medium">{rule.name}</p>
                      {rule.legal_basis && <p className="text-[11px] text-slate-400">{rule.legal_basis}</p>}
                    </Td>
                    <Td>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant="neutral">
                          {rule.item_kind === "any" ? "Qualquer" : rule.item_kind === "product" ? "Produto" : "Serviço"}
                        </Badge>
                        {rule.ncm_pattern && <Badge variant="info">NCM {rule.ncm_pattern}</Badge>}
                        {rule.nbs_pattern && <Badge variant="info">NBS {rule.nbs_pattern}</Badge>}
                        {rule.tax_regime && <Badge variant="medio">{rule.tax_regime}</Badge>}
                        {rule.uf_dest && <Badge variant="neutral">→ {rule.uf_dest}</Badge>}
                      </div>
                    </Td>
                    <Td right className="text-xs tabular-nums">
                      {fmtPct(rule.item_kind === "service" ? rule.iss_rate : rule.icms_rate, 2)} · {fmtPct(rule.pis_rate)} ·{" "}
                      {fmtPct(rule.cofins_rate)}
                    </Td>
                    <Td right className="text-xs tabular-nums">
                      {rule.cbs_rate === null ? "ref." : fmtPct(rule.cbs_rate)} ·{" "}
                      {rule.ibs_rate === null ? "ref." : fmtPct(rule.ibs_rate)} ·{" "}
                      {rule.is_rate > 0 ? <Badge variant="alto">IS {fmtPct(rule.is_rate)}</Badge> : "—"}
                    </Td>
                    <Td right className="text-xs">
                      {rule.cbs_reduction_pct > 0 || rule.ibs_reduction_pct > 0 ? (
                        <Badge variant="success">
                          −{fmtPct(rule.cbs_reduction_pct, 0)} / −{fmtPct(rule.ibs_reduction_pct, 0)}
                        </Badge>
                      ) : (
                        "—"
                      )}
                    </Td>
                    <Td>{rule.priority}</Td>
                    {canWrite && (
                      <Td right>
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => openEdit(rule)}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Desativar a regra "${rule.name}"?`)) remove.mutate(rule.id);
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5 text-red-500" />
                          </Button>
                        </div>
                      </Td>
                    )}
                  </tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={editing ? "Editar regra" : "Nova regra tributária"} wide>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Nome da regra" className="sm:col-span-2">
              <Input value={form.name} onChange={set("name")} required />
            </Field>
            <Field label="Prioridade (desempate)">
              <Input type="number" min={0} max={1000} value={form.priority} onChange={set("priority")} />
            </Field>
          </div>

          <fieldset className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <legend className="px-1 text-xs font-semibold text-slate-500">Critérios de casamento (vazio = qualquer)</legend>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Tipo de item">
                <Select value={form.item_kind} onChange={set("item_kind")}>
                  <option value="product">Produto</option>
                  <option value="service">Serviço</option>
                  <option value="any">Qualquer</option>
                </Select>
              </Field>
              <Field label="NCM (aceita prefixo*)" hint="Ex.: 2202* para bebidas">
                <Input value={form.ncm_pattern} onChange={set("ncm_pattern")} />
              </Field>
              <Field label="NBS (aceita prefixo*)">
                <Input value={form.nbs_pattern} onChange={set("nbs_pattern")} />
              </Field>
              <Field label="CFOP">
                <Input value={form.cfop} onChange={set("cfop")} />
              </Field>
              <Field label="UF origem">
                <Input value={form.uf_origin} onChange={set("uf_origin")} maxLength={2} />
              </Field>
              <Field label="UF destino">
                <Input value={form.uf_dest} onChange={set("uf_dest")} maxLength={2} />
              </Field>
              <Field label="Regime tributário">
                <Select value={form.tax_regime} onChange={set("tax_regime")}>
                  <option value="">Qualquer</option>
                  <option value="real">Lucro Real</option>
                  <option value="presumido">Lucro Presumido</option>
                  <option value="simples">Simples Nacional</option>
                </Select>
              </Field>
            </div>
          </fieldset>

          <fieldset className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <legend className="px-1 text-xs font-semibold text-slate-500">Sistema atual (alíquotas em %)</legend>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              <Field label="ICMS">
                <Input type="number" step="0.01" min="0" value={form.icms_rate} onChange={set("icms_rate")} />
              </Field>
              <Field label="ISS">
                <Input type="number" step="0.01" min="0" value={form.iss_rate} onChange={set("iss_rate")} />
              </Field>
              <Field label="PIS">
                <Input type="number" step="0.01" min="0" value={form.pis_rate} onChange={set("pis_rate")} />
              </Field>
              <Field label="Cofins">
                <Input type="number" step="0.01" min="0" value={form.cofins_rate} onChange={set("cofins_rate")} />
              </Field>
              <Field label="IPI">
                <Input type="number" step="0.01" min="0" value={form.ipi_rate} onChange={set("ipi_rate")} />
              </Field>
            </div>
          </fieldset>

          <fieldset className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <legend className="px-1 text-xs font-semibold text-slate-500">
              Sistema futuro — vazio em CBS/IBS usa a alíquota de referência das premissas
            </legend>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              <Field label="CBS (%)" hint="vazio = referência">
                <Input type="number" step="0.01" min="0" value={form.cbs_rate} onChange={set("cbs_rate")} />
              </Field>
              <Field label="IBS (%)" hint="vazio = referência">
                <Input type="number" step="0.01" min="0" value={form.ibs_rate} onChange={set("ibs_rate")} />
              </Field>
              <Field label="Imposto Seletivo (%)" hint="premissa até regulamentação">
                <Input type="number" step="0.01" min="0" value={form.is_rate} onChange={set("is_rate")} />
              </Field>
              <Field label="Redução CBS (%)" hint="ex.: 100 cesta básica">
                <Input type="number" step="0.01" min="0" max="100" value={form.cbs_reduction_pct} onChange={set("cbs_reduction_pct")} />
              </Field>
              <Field label="Redução IBS (%)">
                <Input type="number" step="0.01" min="0" max="100" value={form.ibs_reduction_pct} onChange={set("ibs_reduction_pct")} />
              </Field>
            </div>
            <label className="mt-3 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
              <input
                type="checkbox"
                checked={form.credit_allowed}
                onChange={(event) => setForm({ ...form, credit_allowed: event.target.checked })}
                className="h-4 w-4 rounded border-slate-300"
              />
              Operação com direito a crédito (CBS/IBS e legados)
            </label>
          </fieldset>

          <Field label="Base legal / referência normativa" hint="Ex.: LC 214/2025, Anexo I — aparece na memória de cálculo e nos relatórios">
            <Input value={form.legal_basis} onChange={set("legal_basis")} />
          </Field>

          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={save.isPending}>
              {editing ? "Salvar alterações" : "Criar regra"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
