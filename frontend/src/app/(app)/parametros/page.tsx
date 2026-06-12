"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Info, Save } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  Field,
  InlineAlert,
  Input,
  PageHeader,
  Spinner,
} from "@/components/ui/primitives";
import { Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Assumptions, Organization, TransitionYear } from "@/lib/types";

export default function ParametrosPage() {
  const queryClient = useQueryClient();
  const { organization, reload, level } = useAuth();
  const [assumptions, setAssumptions] = useState<Assumptions | null>(null);
  const [message, setMessage] = useState("");
  const [yearEdits, setYearEdits] = useState<Record<number, Partial<TransitionYear>>>({});

  const canEdit = level >= 70;

  useEffect(() => {
    if (organization) setAssumptions(structuredClone(organization.assumptions));
  }, [organization]);

  const { data: years, isLoading } = useQuery({
    queryKey: ["transition-years"],
    queryFn: () => api<TransitionYear[]>("/transition-years"),
  });

  const saveAssumptions = useMutation({
    mutationFn: () =>
      api<Organization>("/organizations/assumptions", { method: "PUT", body: JSON.stringify(assumptions) }),
    onSuccess: async () => {
      setMessage("Premissas atualizadas — novas simulações usarão os novos valores.");
      await reload();
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err: Error) => setMessage(err.message),
  });

  const saveYear = useMutation({
    mutationFn: (year: number) =>
      api(`/transition-years/${year}`, { method: "PUT", body: JSON.stringify(yearEdits[year] ?? {}) }),
    onSuccess: (_, year) => {
      setMessage(`Fatores de ${year} atualizados.`);
      setYearEdits((current) => {
        const next = { ...current };
        delete next[year];
        return next;
      });
      queryClient.invalidateQueries({ queryKey: ["transition-years"] });
    },
    onError: (err: Error) => setMessage(err.message),
  });

  function setField(field: keyof Assumptions, value: string | boolean | number) {
    if (!assumptions) return;
    setAssumptions({ ...assumptions, [field]: value });
  }

  function setScenario(scenario: string, value: string) {
    if (!assumptions) return;
    setAssumptions({
      ...assumptions,
      scenario_adjustments: { ...assumptions.scenario_adjustments, [scenario]: { rate_delta_pp: value } },
    });
  }

  function editYear(year: number, field: keyof TransitionYear, value: string | boolean) {
    setYearEdits((current) => ({ ...current, [year]: { ...current[year], [field]: value } }));
  }

  if (!assumptions) return <Spinner />;

  const numberField = (
    label: string,
    field: keyof Assumptions,
    hint?: string,
    step = "0.01",
  ) => (
    <Field label={label} hint={hint}>
      <Input
        type="number"
        step={step}
        value={String(assumptions[field] ?? "")}
        onChange={(event) => setField(field, event.target.value)}
        disabled={!canEdit}
      />
    </Field>
  );

  return (
    <div>
      <PageHeader
        title="Parâmetros e premissas"
        description="Incertezas legislativas viram premissas configuráveis: ajuste alíquotas de referência, fatores de transição e hipóteses sem alterar código."
      />

      <div className="mb-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-200">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          Os valores abaixo são <b>estimativas</b> (alíquota de referência CBS/IBS, alíquotas do IS e split payment
          dependem de regulamentação). Toda simulação grava o snapshot das premissas usadas — relatórios sempre as declaram.
        </p>
      </div>

      {message && (
        <div className="mb-4">
          <InlineAlert tone={message.includes("atualizad") ? "success" : "error"}>{message}</InlineAlert>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-2">
        <Card
          title="Premissas do motor"
          description="Aplicadas como padrão em todas as simulações da organização."
          actions={
            canEdit && (
              <Button size="sm" onClick={() => saveAssumptions.mutate()} loading={saveAssumptions.isPending}>
                <Save className="h-3.5 w-3.5" /> Salvar premissas
              </Button>
            )
          }
        >
          <div className="grid grid-cols-2 gap-3">
            {numberField("Alíquota de referência CBS (%)", "cbs_reference_rate", "Estimativa Min. Fazenda: 8,8")}
            {numberField("Alíquota de referência IBS (%)", "ibs_reference_rate", "Estimativa Min. Fazenda: 17,7")}
            {numberField("Insumos creditáveis (fração do preço)", "input_cost_creditable_ratio", "0–1 · ex.: 0,60")}
            {numberField("Eficiência de créditos — atual", "current_credit_efficiency", "0–1")}
            {numberField("Eficiência de créditos — CBS/IBS", "future_credit_efficiency", "0–1 (crédito amplo)")}
            {numberField("Alíquota efetiva Simples (%)", "simples_effective_rate")}
            {numberField("Dias de antecipação (split payment)", "split_payment_float_days", undefined, "1")}
            {numberField("Custo de capital anual (fração)", "cost_of_capital_annual", "ex.: 0,12 = 12% a.a.")}
          </div>
          <label className="mt-3 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={assumptions.split_payment_enabled}
              onChange={(event) => setField("split_payment_enabled", event.target.checked)}
              disabled={!canEdit}
              className="h-4 w-4 rounded border-slate-300"
            />
            Considerar impacto de caixa do split payment nas simulações
          </label>

          <div className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-700">
            <p className="mb-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
              Ajuste por cenário (p.p. sobre CBS+IBS de referência)
            </p>
            <div className="grid grid-cols-3 gap-3">
              {(["conservador", "provavel", "agressivo"] as const).map((scenario) => (
                <Field key={scenario} label={scenario.charAt(0).toUpperCase() + scenario.slice(1)}>
                  <Input
                    type="number"
                    step="0.1"
                    value={String(assumptions.scenario_adjustments?.[scenario]?.rate_delta_pp ?? 0)}
                    onChange={(event) => setScenario(scenario, event.target.value)}
                    disabled={!canEdit}
                  />
                </Field>
              ))}
            </div>
          </div>
        </Card>

        <Card
          title="Anos de transição (2026–2033)"
          description="Fatores aplicados pelo motor em cada ano — calendário da EC 132/2023 + LC 214/2025, editável conforme a regulamentação evoluir."
        >
          {isLoading || !years ? (
            <Spinner />
          ) : (
            <Table>
              <THead>
                <Th>Ano</Th>
                <Th right>CBS (fator / override %)</Th>
                <Th right>IBS (fator / override %)</Th>
                <Th right>ICMS+ISS restante</Th>
                <Th right>PIS/Cofins</Th>
                <Th>IS</Th>
                {canEdit && <Th right></Th>}
              </THead>
              <TBody>
                {years.map((year) => {
                  const edit = yearEdits[year.year] ?? {};
                  return (
                    <tr key={year.year}>
                      <Td>
                        <span className="font-semibold">{year.year}</span>
                        {year.test_year_compensable && (
                          <span className="ml-1">
                            <Badge variant="info">teste</Badge>
                          </span>
                        )}
                      </Td>
                      <Td right>
                        <div className="flex justify-end gap-1">
                          <Input
                            className="w-16 px-2 py-1 text-right text-xs"
                            value={String(edit.cbs_factor ?? year.cbs_factor)}
                            onChange={(e) => editYear(year.year, "cbs_factor", e.target.value)}
                            disabled={!canEdit}
                          />
                          <Input
                            className="w-16 px-2 py-1 text-right text-xs"
                            placeholder="—"
                            value={edit.cbs_rate_override ?? year.cbs_rate_override ?? ""}
                            onChange={(e) => editYear(year.year, "cbs_rate_override", e.target.value)}
                            disabled={!canEdit}
                          />
                        </div>
                      </Td>
                      <Td right>
                        <div className="flex justify-end gap-1">
                          <Input
                            className="w-16 px-2 py-1 text-right text-xs"
                            value={String(edit.ibs_factor ?? year.ibs_factor)}
                            onChange={(e) => editYear(year.year, "ibs_factor", e.target.value)}
                            disabled={!canEdit}
                          />
                          <Input
                            className="w-16 px-2 py-1 text-right text-xs"
                            placeholder="—"
                            value={edit.ibs_rate_override ?? year.ibs_rate_override ?? ""}
                            onChange={(e) => editYear(year.year, "ibs_rate_override", e.target.value)}
                            disabled={!canEdit}
                          />
                        </div>
                      </Td>
                      <Td right>
                        <Input
                          className="w-16 px-2 py-1 text-right text-xs"
                          value={String(edit.legacy_icms_iss_factor ?? year.legacy_icms_iss_factor)}
                          onChange={(e) => editYear(year.year, "legacy_icms_iss_factor", e.target.value)}
                          disabled={!canEdit}
                        />
                      </Td>
                      <Td right>
                        <Input
                          className="w-16 px-2 py-1 text-right text-xs"
                          value={String(edit.pis_cofins_factor ?? year.pis_cofins_factor)}
                          onChange={(e) => editYear(year.year, "pis_cofins_factor", e.target.value)}
                          disabled={!canEdit}
                        />
                      </Td>
                      <Td>{year.selective_active ? <Badge variant="alto">ativo</Badge> : "—"}</Td>
                      {canEdit && (
                        <Td right>
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={!yearEdits[year.year]}
                            loading={saveYear.isPending && saveYear.variables === year.year}
                            onClick={() => saveYear.mutate(year.year)}
                          >
                            <Save className="h-3.5 w-3.5" />
                          </Button>
                        </Td>
                      )}
                    </tr>
                  );
                })}
              </TBody>
            </Table>
          )}
          <p className="mt-3 text-[11px] text-slate-400">
            Fatores 0–1 multiplicam a alíquota de referência; override em % fixa a alíquota do ano (ex.: 0,9% CBS no
            ano-teste 2026). Alterações são auditadas.
          </p>
        </Card>
      </div>
    </div>
  );
}
