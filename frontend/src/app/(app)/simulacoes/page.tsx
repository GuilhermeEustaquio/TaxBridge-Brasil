"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Calculator, Plus } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
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
} from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtDateTime, SCENARIO_LABELS } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { Page, Simulation } from "@/lib/types";

interface SimulationRow {
  id: string;
  company_id: string;
  name: string;
  scenario: string;
  year_start: number;
  year_end: number;
  status: string;
  origin: string;
  created_at: string;
}

function SimulacoesContent() {
  const { companies, companyId, select } = useSelectedCompany();
  const { level } = useAuth();
  const queryClient = useQueryClient();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ name: "", scenario: "provavel", year_start: 2026, year_end: 2033 });
  const [error, setError] = useState("");

  useEffect(() => {
    if (searchParams.get("nova") === "1") setModalOpen(true);
  }, [searchParams]);

  const { data, isLoading } = useQuery({
    queryKey: ["simulations", companyId, page],
    queryFn: () =>
      api<Page<SimulationRow>>(`/simulations?page=${page}${companyId ? `&company_id=${companyId}` : ""}`),
  });

  const create = useMutation({
    mutationFn: () =>
      api<Simulation>("/simulations", {
        method: "POST",
        body: JSON.stringify({ company_id: companyId, ...form, name: form.name || "Simulação da Reforma" }),
      }),
    onSuccess: (simulation) => {
      queryClient.invalidateQueries({ queryKey: ["simulations"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      router.push(`/simulacoes/${simulation.id}`);
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div>
      <PageHeader
        title="Simulações"
        description="Compare o sistema atual com o modelo CBS/IBS/IS em cada ano da transição, com memória de cálculo completa."
        actions={
          <>
            <CompanySelect companies={companies} value={companyId} onChange={select} />
            {level >= 40 && (
              <Button onClick={() => setModalOpen(true)} disabled={!companyId}>
                <Plus className="h-4 w-4" /> Simular Reforma Tributária
              </Button>
            )}
          </>
        }
      />

      <Card>
        {isLoading ? (
          <Spinner />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma simulação ainda"
            description="Rode a primeira simulação para ver o impacto da reforma ano a ano."
            action={
              level >= 40 && (
                <Button onClick={() => setModalOpen(true)} disabled={!companyId}>
                  <Calculator className="h-4 w-4" /> Simular Reforma Tributária
                </Button>
              )
            }
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Simulação</Th>
                <Th>Cenário</Th>
                <Th>Período</Th>
                <Th>Origem</Th>
                <Th>Criada em</Th>
                <Th right></Th>
              </THead>
              <TBody>
                {data.items.map((simulation) => (
                  <tr key={simulation.id}>
                    <Td className="font-medium">{simulation.name}</Td>
                    <Td>
                      <Badge variant={simulation.scenario === "conservador" ? "medio" : simulation.scenario === "agressivo" ? "success" : "info"}>
                        {SCENARIO_LABELS[simulation.scenario] ?? simulation.scenario}
                      </Badge>
                    </Td>
                    <Td>
                      {simulation.year_start}–{simulation.year_end}
                    </Td>
                    <Td>{simulation.origin === "diagnostico" ? <Badge variant="brand">diagnóstico</Badge> : "manual"}</Td>
                    <Td className="text-xs text-slate-500">{fmtDateTime(simulation.created_at)}</Td>
                    <Td right>
                      <Link href={`/simulacoes/${simulation.id}`}>
                        <Button variant="secondary" size="sm">
                          Abrir
                        </Button>
                      </Link>
                    </Td>
                  </tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </Card>

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nova simulação da Reforma Tributária">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
          className="space-y-3"
        >
          <Field label="Empresa">
            <CompanySelect companies={companies} value={companyId} onChange={select} />
          </Field>
          <Field label="Nome da simulação">
            <Input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Ex.: Estudo de impacto 2026–2033"
            />
          </Field>
          <Field label="Cenário" hint="Ajustes de alíquota por cenário são configuráveis em Parâmetros.">
            <Select value={form.scenario} onChange={(event) => setForm({ ...form, scenario: event.target.value })}>
              <option value="conservador">Conservador (alíquotas maiores)</option>
              <option value="provavel">Provável (referência)</option>
              <option value="agressivo">Agressivo (alíquotas menores)</option>
            </Select>
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Ano inicial">
              <Select
                value={String(form.year_start)}
                onChange={(event) => setForm({ ...form, year_start: Number(event.target.value) })}
              >
                {Array.from({ length: 8 }, (_, index) => 2026 + index).map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Ano final">
              <Select
                value={String(form.year_end)}
                onChange={(event) => setForm({ ...form, year_end: Number(event.target.value) })}
              >
                {Array.from({ length: 8 }, (_, index) => 2026 + index).map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={create.isPending}>
              <Calculator className="h-4 w-4" /> Executar simulação
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default function SimulacoesPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <SimulacoesContent />
    </Suspense>
  );
}
