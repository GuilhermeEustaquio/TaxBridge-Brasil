const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const brlCompact = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});
const number = new Intl.NumberFormat("pt-BR");

export function fmtBRL(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return brl.format(value);
}

export function fmtBRLCompact(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return brlCompact.format(value);
}

export function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return number.format(value);
}

export function fmtPct(value: number | string | null | undefined, digits = 2): string {
  if (value === null || value === undefined || value === "") return "—";
  return `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: digits })}%`;
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("pt-BR");
}

export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export const SCENARIO_LABELS: Record<string, string> = {
  conservador: "Conservador",
  provavel: "Provável",
  agressivo: "Agressivo",
};

export const AREA_LABELS: Record<string, string> = {
  fiscal: "Fiscal",
  contabil: "Contábil",
  financeiro: "Financeiro",
  juridico: "Jurídico",
  ti: "TI",
  vendas: "Vendas",
  compras: "Compras",
};

export const STATUS_LABELS: Record<string, string> = {
  pendente: "Pendente",
  em_andamento: "Em andamento",
  concluido: "Concluído",
  vencido: "Vencido",
  critico: "Crítico",
};

export const REGIME_LABELS: Record<string, string> = {
  simples: "Simples Nacional",
  presumido: "Lucro Presumido",
  real: "Lucro Real",
};

export const IMPACT_LABELS: Record<string, string> = {
  baixo: "Baixo",
  medio: "Médio",
  alto: "Alto",
  critico: "Crítico",
};

export const UFS = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
  "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];
