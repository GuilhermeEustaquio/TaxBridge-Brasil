export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Role {
  id: string;
  slug: string;
  name: string;
  level: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  last_login_at: string | null;
  role: Role;
}

export interface Assumptions {
  cbs_reference_rate: string | number;
  ibs_reference_rate: string | number;
  input_cost_creditable_ratio: string | number;
  current_credit_efficiency: string | number;
  future_credit_efficiency: string | number;
  split_payment_enabled: boolean;
  split_payment_float_days: number;
  cost_of_capital_annual: string | number;
  simples_effective_rate: string | number;
  icms_inside_price: boolean;
  scenario_adjustments: Record<string, { rate_delta_pp: string | number }>;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  assumptions: Assumptions;
}

export interface Branch {
  id: string;
  name: string;
  cnpj: string | null;
  uf: string;
  municipality: string | null;
}

export interface Company {
  id: string;
  legal_name: string;
  trade_name: string | null;
  cnpj: string;
  tax_regime: string;
  segment: string | null;
  uf: string;
  municipality: string | null;
  municipality_code: string | null;
  branches: Branch[];
}

export interface Product {
  id: string;
  company_id: string;
  sku: string;
  name: string;
  ncm: string;
  cest: string | null;
  cfop: string | null;
  cst_icms: string | null;
  csosn: string | null;
  origin_uf: string | null;
  dest_uf: string | null;
  unit_price: number;
  unit_cost: number;
  monthly_volume: number;
  is_selective: boolean;
}

export interface Service {
  id: string;
  company_id: string;
  code: string;
  name: string;
  nbs: string | null;
  lc116_item: string | null;
  municipality: string | null;
  unit_price: number;
  unit_cost: number;
  monthly_volume: number;
}

export interface TaxRule {
  id: string;
  name: string;
  company_id: string | null;
  item_kind: string;
  ncm_pattern: string | null;
  nbs_pattern: string | null;
  cfop: string | null;
  uf_origin: string | null;
  uf_dest: string | null;
  tax_regime: string | null;
  priority: number;
  icms_rate: number;
  iss_rate: number;
  pis_rate: number;
  cofins_rate: number;
  ipi_rate: number;
  cbs_rate: number | null;
  ibs_rate: number | null;
  is_rate: number;
  cbs_reduction_pct: number;
  ibs_reduction_pct: number;
  credit_allowed: boolean;
  legal_basis: string | null;
  is_active: boolean;
}

export interface TransitionYear {
  id: string;
  year: number;
  cbs_factor: number;
  ibs_factor: number;
  cbs_rate_override: number | null;
  ibs_rate_override: number | null;
  cbs_adjustment_pp: number;
  legacy_icms_iss_factor: number;
  pis_cofins_factor: number;
  selective_active: boolean;
  test_year_compensable: boolean;
  notes: string | null;
}

export interface YearSummary {
  year: number;
  current_total: number;
  future_total: number;
  delta: number;
  delta_pct_revenue: number;
  cbs: number;
  ibs: number;
  is: number;
  legacy: number;
  credits_current: number;
  credits_future: number;
  cash_flow_impact: number;
  revenue: number;
  items_count: number;
}

export interface SimulationSummary {
  years: YearSummary[];
  top_items: {
    item_name: string;
    item_kind: string;
    delta_net: number;
    current_net: number;
    future_net: number;
    margin_current_pct: number | null;
    margin_future_pct: number | null;
    breakeven_price: number | null;
  }[];
  items_without_rule: { name: string; kind: string; reason: string }[];
  items_needing_price_adjustment: string[];
  totals: {
    delta_final_year: number;
    delta_pct_revenue_final_year: number;
    final_year: number | null;
  };
}

export interface Simulation {
  id: string;
  company_id: string;
  name: string;
  scenario: string;
  year_start: number;
  year_end: number;
  status: string;
  origin: string;
  summary: SimulationSummary;
  assumptions_snapshot: Record<string, unknown>;
  created_at: string;
}

export interface SimulationItem {
  id: string;
  item_kind: string;
  item_id: string;
  item_name: string;
  tax_rule_id: string | null;
  year: number;
  annual_revenue: number;
  current_tax_total: number;
  current_credits: number;
  current_net_burden: number;
  future_cbs: number;
  future_ibs: number;
  future_is: number;
  future_legacy: number;
  future_credits: number;
  future_net_burden: number;
  delta_net: number;
  margin_current_pct: number | null;
  margin_future_pct: number | null;
  breakeven_price: number | null;
  cash_flow_impact: number;
  calc_memory: {
    regra?: { id: string; nome: string; base_legal: string | null };
    formulas?: string[];
    premissas?: { chave: string; valor: unknown; configuravel: boolean; descricao: string }[];
    avisos?: string[];
    [key: string]: unknown;
  };
}

export interface ComplianceTask {
  id: string;
  company_id: string;
  area: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  due_date: string | null;
  assignee_id: string | null;
  evidence_url: string | null;
  created_at: string;
}

export interface ComplianceSummary {
  overall_progress_pct: number;
  total: number;
  done: number;
  overdue: number;
  critical: number;
  by_area: { area: string; total: number; done: number; overdue: number; progress_pct: number }[];
}

export interface LegalUpdate {
  id: string;
  norm_type: string;
  reference: string;
  title: string;
  summary: string | null;
  impact: string;
  source_url: string | null;
  published_at: string | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  extra: Record<string, unknown>;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface Report {
  id: string;
  company_id: string | null;
  simulation_id: string | null;
  report_type: string;
  format: string;
  premises: Record<string, unknown>;
  created_at: string;
}

export interface Dashboard {
  company: { id: string; legal_name: string; tax_regime: string; uf: string } | null;
  latest_simulation: {
    id: string;
    name: string;
    scenario: string;
    created_at: string;
    summary: SimulationSummary;
  } | null;
  alerts: { level: string; title: string; detail: string }[];
  compliance: ComplianceSummary;
  counts: { companies: number; products: number; services: number; tax_rules: number; simulations: number };
  onboarding: { has_company: boolean; has_items: boolean; has_rules: boolean; has_simulation: boolean };
}
