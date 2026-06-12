"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Plus, Trash2, Upload } from "lucide-react";
import { useState } from "react";
import { CompanySelect, useSelectedCompany } from "@/components/company-select";
import { Modal, Tabs } from "@/components/ui/modal";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  InlineAlert,
  Input,
  PageHeader,
  Spinner,
} from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api, apiDownload } from "@/lib/api";
import { fmtBRL, fmtNumber } from "@/lib/format";
import { useAuth } from "@/lib/auth";
import type { Page, Product, Service } from "@/lib/types";

interface ImportResult {
  created: number;
  updated: number;
  errors: { line: number; error: string }[];
}

const EMPTY_PRODUCT = { sku: "", name: "", ncm: "", cfop: "", unit_price: "", unit_cost: "", monthly_volume: "" };
const EMPTY_SERVICE = { code: "", name: "", nbs: "", lc116_item: "", unit_price: "", unit_cost: "", monthly_volume: "" };

export default function CatalogoPage() {
  const { companies, companyId, select } = useSelectedCompany();
  const { level } = useAuth();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("products");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [importOpen, setImportOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [productForm, setProductForm] = useState(EMPTY_PRODUCT);
  const [serviceForm, setServiceForm] = useState(EMPTY_SERVICE);
  const [error, setError] = useState("");

  const isProducts = tab === "products";
  const resource = isProducts ? "products" : "services";
  const canWrite = level >= 60;

  const { data, isLoading } = useQuery({
    queryKey: [resource, companyId, page, search],
    queryFn: () =>
      api<Page<Product & Service>>(
        `/${resource}?company_id=${companyId}&page=${page}&search=${encodeURIComponent(search)}`,
      ),
    enabled: !!companyId,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["products"] });
    queryClient.invalidateQueries({ queryKey: ["services"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const importCsv = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append("company_id", companyId);
      formData.append("file", file!);
      return api<ImportResult>(`/${resource}/import-csv`, { method: "POST", body: formData });
    },
    onSuccess: (result) => {
      setImportResult(result);
      setFile(null);
      invalidate();
    },
    onError: (err: Error) => setError(err.message),
  });

  const createItem = useMutation({
    mutationFn: () => {
      const payload = isProducts
        ? { company_id: companyId, ...productForm, cfop: productForm.cfop || null }
        : { company_id: companyId, ...serviceForm, nbs: serviceForm.nbs || null, lc116_item: serviceForm.lc116_item || null };
      return api(`/${resource}`, { method: "POST", body: JSON.stringify(payload) });
    },
    onSuccess: () => {
      setCreateOpen(false);
      setProductForm(EMPTY_PRODUCT);
      setServiceForm(EMPTY_SERVICE);
      setError("");
      invalidate();
    },
    onError: (err: Error) => setError(err.message),
  });

  const removeItem = useMutation({
    mutationFn: (id: string) => api(`/${resource}/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });

  return (
    <div>
      <PageHeader
        title="Produtos e serviços"
        description="Catálogo com NCM/NBS, CFOP, preço, custo e volume — base do motor tributário."
        actions={
          <>
            <CompanySelect companies={companies} value={companyId} onChange={select} />
            {canWrite && (
              <>
                <Button variant="secondary" onClick={() => { setImportOpen(true); setImportResult(null); setError(""); }}>
                  <Upload className="h-4 w-4" /> Importar CSV
                </Button>
                <Button onClick={() => { setCreateOpen(true); setError(""); }}>
                  <Plus className="h-4 w-4" /> Novo {isProducts ? "produto" : "serviço"}
                </Button>
              </>
            )}
          </>
        }
      />

      <Tabs
        tabs={[
          { id: "products", label: "Produtos" },
          { id: "services", label: "Serviços" },
        ]}
        active={tab}
        onChange={(id) => {
          setTab(id);
          setPage(1);
          setSearch("");
        }}
      />

      <Card>
        <div className="mb-4 max-w-xs">
          <Input
            placeholder={isProducts ? "Buscar por nome, SKU ou NCM..." : "Buscar por nome, código ou NBS..."}
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>
        {!companyId ? (
          <EmptyState title="Cadastre uma empresa primeiro" description="O catálogo pertence a uma empresa." />
        ) : isLoading ? (
          <Spinner />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title={`Nenhum ${isProducts ? "produto" : "serviço"} cadastrado`}
            description="Importe via CSV (modelo disponível) ou cadastre manualmente."
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>{isProducts ? "SKU" : "Código"}</Th>
                <Th>Nome</Th>
                <Th>{isProducts ? "NCM" : "NBS / LC 116"}</Th>
                <Th right>Preço</Th>
                <Th right>Custo</Th>
                <Th right>Volume/mês</Th>
                {canWrite && <Th right>Ações</Th>}
              </THead>
              <TBody>
                {data.items.map((item) => (
                  <tr key={item.id}>
                    <Td className="font-mono text-xs">{isProducts ? item.sku : item.code}</Td>
                    <Td>
                      <span className="font-medium">{item.name}</span>{" "}
                      {isProducts && item.is_selective && <Badge variant="alto">IS</Badge>}
                    </Td>
                    <Td className="font-mono text-xs">
                      {isProducts ? item.ncm : `${item.nbs ?? "—"}${item.lc116_item ? ` / ${item.lc116_item}` : ""}`}
                    </Td>
                    <Td right>{fmtBRL(item.unit_price)}</Td>
                    <Td right>{fmtBRL(item.unit_cost)}</Td>
                    <Td right>{fmtNumber(item.monthly_volume)}</Td>
                    {canWrite && (
                      <Td right>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (confirm(`Excluir ${item.name}?`)) removeItem.mutate(item.id);
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-500" />
                        </Button>
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

      {/* Modal importação CSV */}
      <Modal open={importOpen} onClose={() => setImportOpen(false)} title={`Importar ${isProducts ? "produtos" : "serviços"} via CSV`}>
        <div className="space-y-3">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Separador “;” ou “,” · decimal com vírgula aceito · upsert por {isProducts ? "SKU" : "código"} ·
            linhas inválidas são reportadas sem interromper o lote.
          </p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => apiDownload(`/${resource}/csv-template`, `modelo-${resource}.csv`)}
          >
            <Download className="h-3.5 w-3.5" /> Baixar modelo CSV
          </Button>
          <Input type="file" accept=".csv" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          {error && <InlineAlert>{error}</InlineAlert>}
          {importResult && (
            <InlineAlert tone={importResult.errors.length ? "info" : "success"}>
              <p>
                <b>{importResult.created}</b> criado(s) · <b>{importResult.updated}</b> atualizado(s) ·{" "}
                <b>{importResult.errors.length}</b> erro(s)
              </p>
              {importResult.errors.slice(0, 5).map((err) => (
                <p key={err.line} className="mt-1 font-mono text-[11px]">
                  Linha {err.line}: {err.error}
                </p>
              ))}
            </InlineAlert>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setImportOpen(false)}>
              Fechar
            </Button>
            <Button onClick={() => importCsv.mutate()} disabled={!file} loading={importCsv.isPending}>
              <Upload className="h-4 w-4" /> Importar
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal criação manual */}
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title={`Novo ${isProducts ? "produto" : "serviço"}`}>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            createItem.mutate();
          }}
          className="space-y-3"
        >
          {isProducts ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Field label="SKU">
                  <Input value={productForm.sku} onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })} required />
                </Field>
                <Field label="NCM (8 dígitos)">
                  <Input value={productForm.ncm} onChange={(e) => setProductForm({ ...productForm, ncm: e.target.value })} required />
                </Field>
              </div>
              <Field label="Nome">
                <Input value={productForm.name} onChange={(e) => setProductForm({ ...productForm, name: e.target.value })} required />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="CFOP (opcional)">
                  <Input value={productForm.cfop} onChange={(e) => setProductForm({ ...productForm, cfop: e.target.value })} />
                </Field>
                <Field label="Preço unitário (R$)">
                  <Input type="number" step="0.01" min="0" value={productForm.unit_price}
                         onChange={(e) => setProductForm({ ...productForm, unit_price: e.target.value })} required />
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Custo unitário (R$)">
                  <Input type="number" step="0.01" min="0" value={productForm.unit_cost}
                         onChange={(e) => setProductForm({ ...productForm, unit_cost: e.target.value })} />
                </Field>
                <Field label="Volume mensal (un.)">
                  <Input type="number" step="1" min="0" value={productForm.monthly_volume}
                         onChange={(e) => setProductForm({ ...productForm, monthly_volume: e.target.value })} />
                </Field>
              </div>
            </>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Código">
                  <Input value={serviceForm.code} onChange={(e) => setServiceForm({ ...serviceForm, code: e.target.value })} required />
                </Field>
                <Field label="NBS (opcional)">
                  <Input value={serviceForm.nbs} onChange={(e) => setServiceForm({ ...serviceForm, nbs: e.target.value })} />
                </Field>
              </div>
              <Field label="Nome">
                <Input value={serviceForm.name} onChange={(e) => setServiceForm({ ...serviceForm, name: e.target.value })} required />
              </Field>
              <div className="grid grid-cols-3 gap-3">
                <Field label="Item LC 116">
                  <Input value={serviceForm.lc116_item} onChange={(e) => setServiceForm({ ...serviceForm, lc116_item: e.target.value })} />
                </Field>
                <Field label="Preço (R$)">
                  <Input type="number" step="0.01" min="0" value={serviceForm.unit_price}
                         onChange={(e) => setServiceForm({ ...serviceForm, unit_price: e.target.value })} required />
                </Field>
                <Field label="Volume mensal">
                  <Input type="number" step="1" min="0" value={serviceForm.monthly_volume}
                         onChange={(e) => setServiceForm({ ...serviceForm, monthly_volume: e.target.value })} />
                </Field>
              </div>
            </>
          )}
          {error && <InlineAlert>{error}</InlineAlert>}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={createItem.isPending}>
              Cadastrar
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
