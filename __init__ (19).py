"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtBRL, fmtBRLCompact } from "@/lib/format";
import type { YearSummary } from "@/lib/types";

const tooltipStyle = {
  backgroundColor: "rgb(15 23 42 / 0.95)",
  border: "none",
  borderRadius: 8,
  fontSize: 12,
  color: "#fff",
};

export function BurdenByYearChart({ years }: { years: YearSummary[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={years} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-slate-200 dark:text-slate-700" />
        <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis tickFormatter={(v: number) => fmtBRLCompact(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" width={70} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value: number, name: string) => [fmtBRL(value), name]}
          labelFormatter={(label) => `Ano ${label}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="current_total" name="Carga atual" fill="#94a3b8" radius={[3, 3, 0, 0]} />
        <Bar dataKey="future_total" name="Carga futura (reforma)" fill="#2563eb" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CompositionChart({ years }: { years: YearSummary[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={years} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-slate-200 dark:text-slate-700" />
        <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis tickFormatter={(v: number) => fmtBRLCompact(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" width={70} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value: number, name: string) => [fmtBRL(value), name]}
          labelFormatter={(label) => `Ano ${label}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="cbs" name="CBS" stackId="reforma" fill="#2563eb" />
        <Bar dataKey="ibs" name="IBS" stackId="reforma" fill="#0ea5e9" />
        <Bar dataKey="is" name="Imposto Seletivo" stackId="reforma" fill="#f59e0b" />
        <Bar dataKey="legacy" name="Tributos legados" stackId="reforma" fill="#94a3b8" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CashFlowChart({ years }: { years: YearSummary[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={years} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-slate-200 dark:text-slate-700" />
        <XAxis dataKey="year" tick={{ fontSize: 11 }} stroke="#94a3b8" />
        <YAxis tickFormatter={(v: number) => fmtBRLCompact(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" width={70} />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value: number, name: string) => [fmtBRL(value), name]}
          labelFormatter={(label) => `Ano ${label}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="credits_future" name="Créditos estimados" stroke="#059669" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="cash_flow_impact" name="Custo de caixa (split payment)" stroke="#dc2626" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
