"use client";

import { useQuery } from "@tanstack/react-query";
import { FileBarChart } from "lucide-react";
import { useState } from "react";
import { Badge, Card, EmptyState, PageHeader, Spinner } from "@/components/ui/primitives";
import { Pagination, Table, TBody, Td, Th, THead } from "@/components/ui/table";
import { api } from "@/lib/api";
import { fmtDateTime } from "@/lib/format";
import type { Page, Report } from "@/lib/types";

export default function RelatoriosPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useQuery({
    queryKey: ["reports", page],
    queryFn: () => api<Page<Report>>(`/reports?page=${page}`),
  });

  return (
    <div>
      <PageHeader
        title="Relatórios gerados"
        description="Histórico de exportações (PDF, XLSX, CSV) com as premissas declaradas em cada relatório."
      />
      <Card>
        {isLoading ? (
          <Spinner />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="Nenhum relatório gerado"
            description="Exporte uma simulação em PDF, XLSX ou CSV — cada exportação fica registrada aqui com suas premissas."
          />
        ) : (
          <>
            <Table>
              <THead>
                <Th>Tipo</Th>
                <Th>Formato</Th>
                <Th>Premissas registradas</Th>
                <Th>Gerado em</Th>
              </THead>
              <TBody>
                {data.items.map((report) => (
                  <tr key={report.id}>
                    <Td>
                      <div className="flex items-center gap-2">
                        <FileBarChart className="h-4 w-4 text-slate-400" />
                        <span className="font-medium">
                          {report.report_type === "impacto_executivo" ? "Impacto executivo (diretoria)" : report.report_type}
                        </span>
                      </div>
                    </Td>
                    <Td>
                      <Badge variant={report.format === "pdf" ? "critico" : report.format === "xlsx" ? "success" : "neutral"}>
                        {report.format.toUpperCase()}
                      </Badge>
                    </Td>
                    <Td className="text-xs text-slate-500">
                      CBS ref. {String(report.premises?.cbs_reference_rate ?? "—")}% · IBS ref.{" "}
                      {String(report.premises?.ibs_reference_rate ?? "—")}% ·{" "}
                      {Object.keys(report.premises ?? {}).length} premissas no snapshot
                    </Td>
                    <Td className="text-xs">{fmtDateTime(report.created_at)}</Td>
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
