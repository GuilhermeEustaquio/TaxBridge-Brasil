"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  Calculator,
  CheckCircle2,
  Download,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { CompanySelect, useSelectedCompany } from "@/components/company-select";
import { BurdenByYearChart, CompositionChart } from "@/components/charts/charts";
import { Badge, Button, Card, EmptyState, InlineAlert, PageHeader, Spinner, Stat } from "@/components/ui/primitives";
import { Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api, apiDownload } from "@/lib/api";
import { fmtBRL, fmtPct, SCENARIO_LABELS } from "@/lib/format";
import type { Dashboard, Simulation } from "@/lib/types";

function OnboardingCard({ onboarding }: { onboarding: Dashboard["onboarding"] }) {
  const steps = [
    { done: onboarding.has_company, label: "Cadastre sua empresa", href: "/empresas" },
    { done: onboarding.has_items, label: "Importe produtos e serviços (CSV)", href: "/catalogo" },
    { done: onboarding.has_rules, label: "Parametrize as regras CBS/IBS/IS", href: "/regras" },
    { done: onboarding.has_simulation, label: "Rode o primeiro diagnóstico", href: "/simulacoes" },
  ];
  const remaining = steps.filter((step) => !step.done).length;
  if (remaining === 0) return null;
  return (
    <Card
      title="Primeiros passos"
      description={`Complete ${remaining} etapa(s) para ver o impacto da reforma na sua empresa.`}
      className="border-brand-200 bg-brand-50/60 dark:border-brand-800 dark:bg-brand-900/20"
    >
      <ol className="space-y-2">
        {steps.map((step) => (
          <li key={step.label} className="flex items-center gap-2 text-sm">
            <CheckCircle2
              className={step.done ? "h-4 w-4 text-emerald-500" : "h-4 w-4 text-slate-300 dark:text-slate-600"}
            />
            <Link
              href={step.href}
              className={
                step.done
                  ? "text-slate-400 line-through"
                  : "font-medium text-slate-700 hover:text-brand-600 dark:text-slate-200"
              }
            >
              {step.label}
            </Link>
            {!step.done && <ArrowRight className="h-3 w-3 text-slate-400" />}
          </li>
        ))}
      </ol>
    </Card>
  );
}

export default function DashboardPage() {
  const { companies, companyId, select, isLoading: loadingCompanies } = useSelectedCompany();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", companyId],
    queryFn: () => api<Dashboard>(`/dashboard${companyId ? `?company_id=${companyId}` : ""}`),
    enabled: !loadingCompanies,
  });

  const diagnostic = useMutation({
    mutationFn: () => api<Simulation>(`/companies/${companyId}/diagnostico`, { method: "POST" }),
    onSuccess: () => {
      setFeedback("Diagnóstico concluído! Os números abaixo já refletem a nova simulação.");
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["simulations"] });
    },
    onError: (error: Error) => setFeedback(error.message),
  });

  const simulation = data?.latest_simulation;
  const summary = simulation?.summary;
  const totals = summary?.totals;
  const finalYear = summary?.years?.at(-1);
  const deltaPositive = (totals?.delta_final_year ?? 0) > 0;

  return (
    <div>
      <PageHeader
        title="Dashboard de impacto"
        description="Quanto a Reforma Tributária vai impactar sua empresa, ano a ano, até 2033."
        actions={
          <>
            <CompanySelect companies={companies} value={companyId} onChange={select} />
            <Button
              variant="secondary"
              onClick={() => diagnostic.mutate()}
              loading={diagnostic.isPending}
              disabled={!companyId}
            >
              <Stethoscope className="h-4 w-4" /> Gerar diagnóstico da empresa
            </Button>
            <Link href="/simulacoes?nova=1">
              <Button>
                <Calculator className="h-4 w-4" /> Simular Reforma Tributária
              </Button>
            </Link>
          </>
        }
      />

      {feedback && (
        <div className="mb-4">
          <InlineAlert tone={feedback.includes("concluído") ? "success" : "error"}>{feedback}</InlineAlert>
        </div>
      )}

      {isLoading || loadingCompanies ? (
        <Spinner />
      ) : !data ? (
        <EmptyState title="Não foi possível carregar o dashboard" />
      ) : (
        <div className="space-y-5">
          <OnboardingCard onboarding={data.onboarding} />

          {!simulation ? (
            <EmptyState
              title="Nenhuma simulação ainda"
              description='Clique em "Gerar diagnóstico da empresa" para calcular o impacto da reforma com um clique.'
              action={
                <Button onClick={() => diagnostic.mutate()} loading={diagnostic.isPending} disabled={!companyId}>
                  <Stethoscope className="h-4 w-4" /> Gerar diagnóstico da empresa
                </Button>
              }
            />
          ) : (
            <>
              {/* KPIs */}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Stat
                  label={`Δ carga anual em ${totals?.final_year ?? 2033}`}
                  value={fmtBRL(Math.abs(totals?.delta_final_year ?? 0))}
                  sub={deltaPositive ? "aumento estimado vs sistema atual" : "redução estimada vs sistema atual"}
                  tone={deltaPositive ? "negative" : "positive"}
                  icon={deltaPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                />
                <Stat
                  label="Impacto sobre a receita"
                  value={fmtPct(Math.abs(totals?.delta_pct_revenue_final_year ?? 0))}
                  sub={`cenário ${SCENARIO_LABELS[simulation.scenario] ?? simulation.scenario}`}
                  tone={deltaPositive ? "negative" : "positive"}
                />
                <Stat
                  label={`Créditos estimados (${finalYear?.year ?? "—"})`}
                  value={fmtBRL(finalYear?.credits_future ?? 0)}
                  sub="crédito amplo CBS/IBS + legados"
                  tone="brand"
                  icon={<Wallet className="h-4 w-4" />}
                />
                <Stat
                  label="Custo de caixa (split payment)"
                  value={fmtBRL(finalYear?.cash_flow_impact ?? 0)}
                  sub="custo financeiro anual estimado"
                  icon={<AlertTriangle className="h-4 w-4" />}
                />
              </div>

              {/* Gráficos */}
              <div className="grid gap-5 xl:grid-cols-2">
                <Card
                  title="Carga tributária líquida por ano"
                  description="Sistema atual × sistema da reforma (linha do tempo da transição 2026–2033)"
                >
                  <BurdenByYearChart years={summary?.years ?? []} />
                </Card>
                <Card
                  title="Composição da carga futura"
                  description="CBS, IBS, Imposto Seletivo e tributos legados remanescentes"
                >
                  <CompositionChart years={summary?.years ?? []} />
                </Card>
              </div>

              <div className="grid gap-5 xl:grid-cols-3">
                {/* Alertas */}
                <Card title="Alertas de risco" className="xl:col-span-1">
                  {data.alerts.length === 0 ? (
                    <p className="text-sm text-slate-500">Nenhum alerta no momento. 🎉</p>
                  ) : (
                    <ul className="space-y-3">
                      {data.alerts.map((alert, index) => (
                        <li key={index} className="flex gap-2">
                          <Badge variant={alert.level}>{alert.level.toUpperCase()}</Badge>
                          <div>
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{alert.title}</p>
                            <p className="text-[11px] text-slate-500 dark:text-slate-400">{alert.detail}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                {/* Top itens */}
                <Card
                  title={`Itens mais impactados em ${totals?.final_year ?? 2033}`}
                  className="xl:col-span-2"
                  actions={
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        apiDownload(`/simulations/${simulation.id}/export.pdf`, "taxbridge-relatorio-diretoria.pdf")
                      }
                    >
                      <Download className="h-3.5 w-3.5" /> Exportar relatório para diretoria
                    </Button>
                  }
                >
                  <Table>
                    <THead>
                      <Th>Item</Th>
                      <Th right>Δ carga</Th>
                      <Th right>Margem atual → futura</Th>
                      <Th right>Preço de equilíbrio</Th>
                    </THead>
                    <TBody>
                      {(summary?.top_items ?? []).slice(0, 6).map((item) => (
                        <tr key={item.item_name}>
                          <Td>
                            <span className="font-medium">{item.item_name}</span>{" "}
                            <Badge variant="neutral">{item.item_kind === "product" ? "Produto" : "Serviço"}</Badge>
                          </Td>
                          <Td right className={item.delta_net > 0 ? "text-red-600" : "text-emerald-600"}>
                            {fmtBRL(item.delta_net)}
                          </Td>
                          <Td right>
                            {fmtPct(item.margin_current_pct)} → {fmtPct(item.margin_future_pct)}
                          </Td>
                          <Td right>{fmtBRL(item.breakeven_price)}</Td>
                        </tr>
                      ))}
                    </TBody>
                  </Table>
                </Card>
              </div>

              {/* Compliance */}
              <Card
                title="Maturidade do checklist de adequação"
                description={`${data.compliance.done}/${data.compliance.total} tarefas concluídas · ${data.compliance.overdue} vencida(s)`}
                actions={
                  <Link href="/compliance">
                    <Button variant="ghost" size="sm">
                      Abrir checklist <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                }
              >
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {data.compliance.by_area.map((area) => (
                    <div key={area.area}>
                      <div className="mb-1 flex justify-between text-xs">
                        <span className="font-medium capitalize text-slate-600 dark:text-slate-300">{area.area}</span>
                        <span className="text-slate-400">{fmtPct(area.progress_pct, 0)}</span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-700">
                        <div
                          className="h-2 rounded-full bg-brand-600 transition-all"
                          style={{ width: `${area.progress_pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}
