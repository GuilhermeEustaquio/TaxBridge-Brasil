"use client";

import clsx from "clsx";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./primitives";

export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={clsx("overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700", className)}>
      <table className="w-full min-w-[640px] divide-y divide-slate-200 text-sm dark:divide-slate-700">
        {children}
      </table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-50 dark:bg-slate-800">
      <tr>{children}</tr>
    </thead>
  );
}

export function Th({ children, right }: { children?: React.ReactNode; right?: boolean }) {
  return (
    <th
      className={clsx(
        "px-3 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400",
        right ? "text-right" : "text-left",
      )}
    >
      {children}
    </th>
  );
}

export function TBody({ children }: { children: React.ReactNode }) {
  return (
    <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-700/60 dark:bg-slate-800/40">
      {children}
    </tbody>
  );
}

export function Td({
  children,
  right,
  className,
  colSpan,
}: {
  children?: React.ReactNode;
  right?: boolean;
  className?: string;
  colSpan?: number;
}) {
  return (
    <td
      colSpan={colSpan}
      className={clsx(
        "px-3 py-2.5 text-slate-700 dark:text-slate-200",
        right && "text-right tabular-nums",
        className,
      )}
    >
      {children}
    </td>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onPage,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <div className="mt-3 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
      <span>
        Página {page} de {pages} · {total} registro(s)
      </span>
      <div className="flex gap-1">
        <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          <ChevronLeft className="h-3.5 w-3.5" /> Anterior
        </Button>
        <Button variant="secondary" size="sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>
          Próxima <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
