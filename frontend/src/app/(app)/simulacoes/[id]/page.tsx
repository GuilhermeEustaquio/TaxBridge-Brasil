"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download, FileSpreadsheet, FileText, Microscope } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { BurdenByYearChart, CashFlowChart, CompositionChart } from "@/components/charts/charts";
import { Modal } from "@/components/ui/modal";
import { Badge, Button, Card, InlineAlert, PageHeader, Select, Spinner } from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api, apiDownload } from "@/lib/api";
import { fmtBRL, fmtDateTime, fmtPct, SCENARIO_LABELS } from "@/lib/format";
import type { Page, Simulation, SimulationItem } from "@/lib/types";

function MemoryModal({ item, onClose }: { item: SimulationItem | null; onClose: () => void }) {
  const memory = item?.calc_memory;
  return (
    <Modal open={!!item} onClose={onClose} title={`Memória de cálculo — ${item?.item_name ?? ""} (${item?.year ?? ""})`} wide>
      {memory && (
        <div className="space-y-4 text-sm">
          <div>
            <p className="text-xs font-semibold uppercase text-slate-400">Regra aplicada</p>
            <p className="font-medium">{memory.regra?.nome}</p>
            {memory.regra?.base_legal && <p className="text-xs text-slate-500">{memory.regra.base_legal}</p>}
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold uppercase text-slate-400">Fórmulas</p>
            <div className="space-y-1 rounded-lg bg-slate-50 p-3 font-mono text-[11px] leading-relaxed dark:bg-slate-900">
              {(memory.formulas ?? []).map((formula, index) => (
                <p key={index}>{formula}</p>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold uppercase text-slate-400">Premissas utilizadas</p>
            <ul className="space-y-1">
              {(memory.premissas ?? []).map((premise, index) => (
                <li key={index} className="flex flex-wrap items-center gap-2 text-xs">
                  <code className="rounded bg-slate-100 px-1.5 py-0.5 dark:bg-slate-700">{premise.chave}</code>
                  <span className="font-semibold">{String(premise.valor)}</span>
                  {premise.configuravel && <Badge variant="info">configurável</Badge>}
                  <span className="text-slate-500">{premise.descricao}</span>
                </li>
              ))}
            </ul>
          </div>
          {(memory.avisos ?? []).length > 0 && (
            <div className="space-y-1">
              {(memory.avisos ?? []).map((warning, index) => (
                <InlineAlert key={index} tone="info">
                  {warning}
                </InlineAlert>
              ))}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}

export default function SimulacaoDetalhePage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [year, setYear] = useState<string>("");
  const [page, setPage] = useState(1);
  const [memoryItem, setMemoryItem] = useState<SimulationItem | null>(null);

  const { data: simulation, isLoading } = useQuery({
    queryKey: ["simulation", id],
    queryFn: () => api<Simulation>(`/simulations/${id}`),
  });

  const { data: items } = useQuery({
    queryKey: ["simulation-items", id, year, page],
    queryFn: () =>
      api<Page<SimulationItem>>(`/simulations/${id}/items?page=${page}${year ? `&year=${year}` : ""}`),
    enabled: !!simulation,
  });

  if (isLoading || !simulation) return <Spinner />;

  const summary = simulation.summary;
  const yearOptions = summary.years.map((y) => y.year);

  return (
    <div>
      <PageHeader
        title={simulation.name}
        description={`Cenário ${SCENARIO_LABELS[simulation.scenario]} · ${simulation.year_start}–${simulation.year_end} · criada em ${fmtDateTime(simulation.created_at)}`}
        actions={
          <>
            <Link href="/simulacoes">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4" /> Voltar
              </Button>
            </Link>
            <Button
              variant="secondary"
              onClick={() => apiDownload(`/simulations/${id}/export.xlsx`, `taxbridge-simulacao.xlsx`)}
            >
              <FileSpreadsheet className="h-4 w-4" /> XLSX
            </Button>
            <Button
              variant="secondary"
              onClick={() => apiDownload(`/simulations/${id}/export.csv`, `taxbridge-simulacao.csv`)}
            >
              <Download className="h-4 w-4" /> CSV
            </Button>
            <Button onClick={() => apiDownload(`/simulations/${id}/export.pdf`, `taxbridge-relatorio-diretoria.pdf`)}>
              <FileText className="h-4 w-4" /> Exportar relatório para diretoria
            </Button>
          </>
        }
      />

      {summary.items_without_rule.length > 0 && (
        <div className="mb-4">
          <InlineAlert>
            <b>{summary.items_without_rule.length} item(ns) sem regra tributária</b> (não calculados):{" "}
            {summary.items_without_rule.map((item) => item.name).join(", ")} — cadastre regras em “Regras Tributárias”.
          </InlineAlert>
        </div>
      )}

      <div className="grid gap-5 xl:grid-cols-2">
        <Card title="Carga líquida por ano — atual × futura">
          <BurdenByYearChart years={summary.years} />
        </Card>
        <Card title="Composição da carga futura">
          <CompositionChart years={summary.years} />
        </Card>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-3">
        <Card title="Créditos e impacto de caixa" className="xl:col-span-1">
          <CashFlowChart years={summary.years} />
        </Card>
        <Card title="Resumo por ano" className="xl:col-span-2">
          <Table>
            <THead>
              <Th>Ano</Th>
              <Th right>Carga atual</Th>
              <Th right>Carga futura</Th>
              <Th right>Δ</Th>
              <Th right>Δ % receita</Th>
              <Th right>Caixa (split)</Th>
            </THead>
            <TBody>
              {summary.years.map((row) => (
                <tr key={row.year}>
                  <Td className="font-semibold">{row.year}</Td>
                  <Td right>{fmtBRL(row.current_total)}</Td>
                  <Td right>{fmtBRL(row.future_total)}</Td>
                  <Td right className={row.delta > 0 ? "text-red-600" : "text-emerald-600"}>
                    {fmtBRL(row.delta)}
                  </Td>
                  <Td right>{fmtPct(row.delta_pct_revenue)}</Td>
                  <Td right>{fmtBRL(row.cash_flow_impact)}</Td>
                </tr>
              ))}
            </TBody>
          </Table>
        </Card>
      </div>

      <Card
        title="Itens da simulação"
        description="Cada número é rastreável: abra a memória de cálculo para ver regra, fórmulas e premissas."
        className="mt-5"
        actions={
          <Select value={year} onChange={(event) => { setYear(event.target.value); setPage(1); }} className="w-auto">
            <option value="">Todos os anos</option>
            {yearOptions.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </Select>
        }
      >
        <Table>
          <THead>
            <Th>Item</Th>
            <Th>Ano</Th>
            <Th right>Receita</Th>
            <Th right>Carga atual</Th>
            <Th right>CBS+IBS+IS</Th>
            <Th right>Carga futura</Th>
            <Th right>Δ</Th>
            <Th right>Margem</Th>
            <Th right>Preço equil.</Th>
            <Th right>Memória</Th>
          </THead>
          <TBody>
            {(items?.items ?? []).map((item) => (
              <tr key={item.id}>
                <Td>
                  <span className="font-medium">{item.item_name}</span>{" "}
                  <Badge variant="neutral">{item.item_kind === "product" ? "P" : "S"}</Badge>
                </Td>
                <Td>{item.year}</Td>
                <Td right>{fmtBRL(item.annual_revenue)}</Td>
                <Td right>{fmtBRL(item.current_net_burden)}</Td>
                <Td right>{fmtBRL(item.future_cbs + item.future_ibs + item.future_is)}</Td>
                <Td right>{fmtBRL(item.future_net_burden)}</Td>
                <Td right className={item.delta_net > 0 ? "text-red-600" : "text-emerald-600"}>
                  {fmtBRL(item.delta_net)}
                </Td>
                <Td right className="text-xs">
                  {fmtPct(item.margin_current_pct)} → {fmtPct(item.margin_future_pct)}
                </Td>
                <Td right>{fmtBRL(item.breakeven_price)}</Td>
                <Td right>
                  <Button variant="ghost" size="sm" onClick={() => setMemoryItem(item)} title="Memória de cálculo">
                    <Microscope className="h-4 w-4" />
                  </Button>
                </Td>
              </tr>
            ))}
          </TBody>
        </Table>
        {items && <Pagination page={items.page} pageSize={items.page_size} total={items.total} onPage={setPage} />}
      </Card>

      <MemoryModal item={memoryItem} onClose={() => setMemoryItem(null)} />
    </div>
  );
}
