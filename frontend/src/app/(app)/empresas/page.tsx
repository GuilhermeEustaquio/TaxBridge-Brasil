"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Plus, Trash2 } from "lucide-react";
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
import { REGIME_LABELS, UFS } from "@/lib/format";
import type { Company, Page } from "@/lib/types";
import { useAuth } from "@/lib/auth";

const EMPTY_COMPANY = {
  legal_name: "",
  trade_name: "",
  cnpj: "",
  tax_regime: "real",
  segment: "",
  uf: "SP",
  municipality: "",
};

export default function EmpresasPage() {
  const queryClient = useQueryClient();
  const { level } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [branchFor, setBranchFor] = useState<Company | null>(null);
  const [form, setForm] = useState(EMPTY_COMPANY);
  const [branchForm, setBranchForm] = useState({ name: "", cnpj: "", uf: "SP", municipality: "" });
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["companies", page, search],
    queryFn: () => api<Page<Company>>(`/companies?page=${page}&search=${encodeURIComponent(search)}`),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["companies"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const createCompany = useMutation({
    mutationFn: () =>
      api<Company>("/companies", {
        method: "POST",
        body: JSON.stringify({ ...form, trade_name: form.trade_name || null, segment: form.segment || null }),
      }),
    onSuccess: () => {
      setModalOpen(false);
      setForm(EMPTY_COMPANY);
      setError("");
      invalidate();
    },
    onError: (err: Error) => setError(err.message),
  });

  const createBranch = useMutation({
    mutationFn: () =>
      api(`/companies/${branchFor?.id}/branches`, {
        method: "POST",
        body: JSON.stringify({ ...branchForm, cnpj: branchForm.cnpj || null, municipality: branchForm.municipality || null }),
      }),
    onSuccess: () => {
      setBranchFor(null);
      setBranchForm({ name: "", cnpj: "", uf: "SP", municipality: "" });
      setError("");
      invalidate();
    },
    onError: (err: Error) => setError(err.message),
  });

  const removeCompany = useMutation({
    mutationFn: (id: string) => api(`/companies/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  const canWrite = level >= 60;
  const canDelete = level >= 90;

  return (
    <div>
      <PageHeader
        title="Empresas e filiais"
        description="Cadastro multiempresa com CNPJ, regime tributário, segmento e localização."
        actions={
          canWrite && (
            <Button onClick={() => setModalOpen(true)}>
              <Plus className="h-4 w-4" /> Nova empresa
            </Button>
          )
        }
      />

      <Card>
        <div className="mb-4 max-w-xs">
          <Input
            placeholder="Buscar por razão social ou CNPJ..."
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
            title="Nenhuma empresa cadastrada"
            description="Cadastre a primeira empresa para começar as simulações."
            action={
              canWrite && (
                <Button onClick={() => setModalOpen(true)}>
                  <Plus className="h-4 w-4" /> Nova empresa
                </Button>
              )
            }
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Empresa</Th>
                <Th>CNPJ</Th>
                <Th>Regime</Th>
                <Th>UF / Município</Th>
                <Th>Filiais</Th>
                <Th right>Ações</Th>
              </THead>
              <TBody>
                {data.items.map((company) => (
                  <tr key={company.id}>
                    <Td>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        <div>
                          <p className="font-medium">{company.legal_name}</p>
                          {company.segment && <p className="text-[11px] text-slate-400">{company.segment}</p>}
                        </div>
                      </div>
                    </Td>
                    <Td className="font-mono text-xs">{company.cnpj}</Td>
                    <Td>
                      <Badge variant={company.tax_regime === "simples" ? "medio" : "info"}>
                        {REGIME_LABELS[company.tax_regime] ?? company.tax_regime}
                      </Badge>
                    </Td>
                    <Td>
                      {company.uf}
                      {company.municipality ? ` · ${company.municipality}` : ""}
                    </Td>
                    <Td>{company.branches.length}</Td>
                    <Td right>
                      <div className="flex justify-end gap-1">
                        {canWrite && (
                          <Button variant="ghost" size="sm" onClick={() => setBranchFor(company)}>
                            + Filial
                          </Button>
                        )}
                        {canDelete && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              if (confirm(`Excluir ${company.legal_name}?`)) removeCompany.mutate(company.id);
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </Td>
                  </tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </Card>

      {/* Modal nova empresa */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Nova empresa">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createCompany.mutate();
          }}
          className="space-y-3"
        >
          <Field label="Razão social">
            <Input value={form.legal_name} onChange={(e) => setForm({ ...form, legal_name: e.target.value })} required />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Nome fantasia (opcional)">
              <Input value={form.trade_name} onChange={(e) => setForm({ ...form, trade_name: e.target.value })} />
            </Field>
            <Field label="CNPJ">
              <Input
                value={form.cnpj}
                onChange={(e) => setForm({ ...form, cnpj: e.target.value })}
                placeholder="00.000.000/0000-00"
                required
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Regime tributário">
              <Select value={form.tax_regime} onChange={(e) => setForm({ ...form, tax_regime: e.target.value })}>
                <option value="real">Lucro Real</option>
                <option value="presumido">Lucro Presumido</option>
                <option value="simples">Simples Nacional</option>
              </Select>
            </Field>
            <Field label="Segmento (opcional)">
              <Input value={form.segment} onChange={(e) => setForm({ ...form, segment: e.target.value })} />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label="UF">
              <Select value={form.uf} onChange={(e) => setForm({ ...form, uf: e.target.value })}>
                {UFS.map((uf) => (
                  <option key={uf}>{uf}</option>
                ))}
              </Select>
            </Field>
            <Field label="Município (opcional)">
              <Input value={form.municipality} onChange={(e) => setForm({ ...form, municipality: e.target.value })} />
            </Field>
          </div>
          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createCompany.isPending}>
              Cadastrar
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal nova filial */}
      <Modal open={!!branchFor} onClose={() => setBranchFor(null)} title={`Nova filial — ${branchFor?.legal_name ?? ""}`}>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createBranch.mutate();
          }}
          className="space-y-3"
        >
          <Field label="Nome da filial">
            <Input value={branchForm.name} onChange={(e) => setBranchForm({ ...branchForm, name: e.target.value })} required />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="CNPJ (opcional)">
              <Input value={branchForm.cnpj} onChange={(e) => setBranchForm({ ...branchForm, cnpj: e.target.value })} />
            </Field>
            <Field label="UF">
              <Select value={branchForm.uf} onChange={(e) => setBranchForm({ ...branchForm, uf: e.target.value })}>
                {UFS.map((uf) => (
                  <option key={uf}>{uf}</option>
                ))}
              </Select>
            </Field>
          </div>
          <Field label="Município (opcional)">
            <Input
              value={branchForm.municipality}
              onChange={(e) => setBranchForm({ ...branchForm, municipality: e.target.value })}
            />
          </Field>
          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setBranchFor(null)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createBranch.isPending}>
              Adicionar filial
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
