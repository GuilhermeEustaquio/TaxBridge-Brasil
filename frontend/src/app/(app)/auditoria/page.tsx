"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Badge, Card, EmptyState, Input, PageHeader, Spinner } from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";
import type { AuditLog, Page } from "@/lib/types";

function actionVariant(action: string): string {
  if (action.includes("delete") || action.includes("revoke")) return "critico";
  if (action.includes("create") || action.includes("register")) return "success";
  if (action.includes("update")) return "info";
  if (action.startsWith("auth.")) return "neutral";
  return "medio";
}

export default function AuditoriaPage() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", action, page],
    queryFn: () =>
      api<Page<AuditLog>>(`/audit-logs?page=${page}${action ? `&action=${encodeURIComponent(action)}` : ""}`),
  });

  return (
    <div>
      <PageHeader
        title="Logs de auditoria"
        description="Trilha imutável de todas as ações: usuário, IP, entidade e metadados (requisito LGPD)."
      />
      <Card>
        <div className="mb-4 max-w-xs">
          <Input
            placeholder="Filtrar por ação (ex.: simulation, login)..."
            value={action}
            onChange={(event) => {
              setAction(event.target.value);
              setPage(1);
            }}
          />
        </div>
        {isLoading ? (
          <Spinner />
        ) : !data || data.items.length === 0 ? (
          <EmptyState title="Nenhum registro encontrado" />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Ação</Th>
                <Th>Entidade</Th>
                <Th>Metadados</Th>
                <Th>IP</Th>
                <Th>Data/hora</Th>
              </THead>
              <TBody>
                {data.items.map((log) => (
                  <tr key={log.id}>
                    <Td>
                      <Badge variant={actionVariant(log.action)}>{log.action}</Badge>
                    </Td>
                    <Td className="text-xs">
                      {log.entity_type ?? "—"}
                      {log.entity_id && (
                        <span className="ml-1 font-mono text-[10px] text-slate-400">{log.entity_id.slice(0, 8)}…</span>
                      )}
                    </Td>
                    <Td className="max-w-xs truncate font-mono text-[11px] text-slate-500">
                      {Object.keys(log.extra ?? {}).length > 0 ? JSON.stringify(log.extra) : "—"}
                    </Td>
                    <Td className="font-mono text-xs">{log.ip_address ?? "—"}</Td>
                    <Td className="text-xs">{fmtDateTime(log.created_at)}</Td>
                  </tr>
                ))}
              </TBody>
            </Table>
            <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPage={setPage} />
          </>
        )}
      </Card>
    </div>
  );
}
