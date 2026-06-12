"""Motor tributário da Reforma (CBS/IBS/IS) — núcleo do TaxBridge Brasil.

Princípios:
- NENHUMA alíquota ou fator é hardcoded: tudo vem de `tax_rules`,
  `tax_transition_years` e das premissas da organização (`Assumptions`).
- Aritmética 100% em `Decimal` (nunca float em dinheiro/alíquota).
- Toda saída carrega memória de cálculo (regra, fatores, fórmulas, premissas,
  avisos) — requisito de rastreabilidade do produto.
- Incertezas legislativas aparecem como premissas marcadas `configuravel: true`.

O motor é puro (sem I/O): recebe objetos já carregados e devolve resultados.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.models import Company, Product, Service, TaxRule, TaxTransitionYear
from app.schemas.org import Assumptions

CENTS = Decimal("0.01")
RATE_Q = Decimal("0.0001")
ZERO = Decimal("0")
HUNDRED = Decimal("100")
MONTHS = Decimal("12")
DAYS_YEAR = Decimal("365")


def _money(x: Decimal) -> Decimal:
    return x.quantize(CENTS, rounding=ROUND_HALF_UP)


def _rate(x: Decimal) -> Decimal:
    return x.quantize(RATE_Q, rounding=ROUND_HALF_UP)


def _f(x: Decimal | None) -> float | None:
    """Converte Decimal para float arredondado (uso exclusivo em JSON de memória)."""
    return None if x is None else float(x.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _pct_to_frac(rate_pp: Decimal) -> Decimal:
    """Converte pontos percentuais (18.0) em fração (0.18)."""
    return rate_pp / HUNDRED


@dataclass
class ItemYearResult:
    item_kind: str
    item_id: Any
    item_name: str
    tax_rule_id: Any
    year: int
    annual_revenue: Decimal
    current_tax_total: Decimal
    current_credits: Decimal
    current_net_burden: Decimal
    future_cbs: Decimal
    future_ibs: Decimal
    future_is: Decimal
    future_legacy: Decimal
    future_credits: Decimal
    future_net_burden: Decimal
    delta_net: Decimal
    margin_current_pct: Decimal | None
    margin_future_pct: Decimal | None
    breakeven_price: Decimal | None
    cash_flow_impact: Decimal
    calc_memory: dict = field(default_factory=dict)
    needs_price_adjustment: bool = False


@dataclass
class UnmatchedItem:
    item_kind: str
    item_id: Any
    item_name: str
    reason: str = "Nenhuma regra tributária parametrizada casa com este item"


# ---------------------------------------------------------------------------
# Casamento item → regra (especificidade; ver docs/04-regras-de-negocio.md)
# ---------------------------------------------------------------------------

def _match_code(pattern: str | None, code: str | None) -> int | None:
    """Retorna pontos do casamento de NCM/NBS ou None se desqualificado."""
    if pattern is None:
        return 0
    if not code:
        return None
    if pattern.endswith("*"):
        return 25 if code.startswith(pattern[:-1]) else None
    return 40 if code == pattern else None


def rule_match_score(rule: TaxRule, item: Product | Service, kind: str, company: Company) -> int | None:
    if rule.item_kind != "any" and rule.item_kind != kind:
        return None
    score = 0
    if rule.item_kind == kind:
        score += 5

    if kind == "product":
        pts = _match_code(rule.ncm_pattern, getattr(item, "ncm", None))
        if pts is None:
            return None
        score += pts
        if rule.nbs_pattern is not None:
            return None  # regra de serviço não casa com produto
    else:
        pts = _match_code(rule.nbs_pattern, getattr(item, "nbs", None))
        if pts is None:
            return None
        score += pts
        if rule.ncm_pattern is not None:
            return None

    if rule.cfop is not None:
        if getattr(item, "cfop", None) != rule.cfop:
            return None
        score += 15

    if rule.uf_origin is not None:
        origin = getattr(item, "origin_uf", None) or company.uf
        if origin != rule.uf_origin:
            return None
        score += 10

    if rule.uf_dest is not None:
        if getattr(item, "dest_uf", None) != rule.uf_dest:
            return None
        score += 10

    if rule.tax_regime is not None:
        if company.tax_regime != rule.tax_regime:
            return None
        score += 5

    if rule.company_id is not None:
        if rule.company_id != item.company_id:
            return None
        score += 20

    return score


def match_rule(item: Product | Service, kind: str, company: Company, rules: list[TaxRule]) -> TaxRule | None:
    best: TaxRule | None = None
    best_key: tuple = ()
    for rule in rules:
        score = rule_match_score(rule, item, kind, company)
        if score is None:
            continue
        key = (score, rule.priority, rule.updated_at or rule.created_at)
        if best is None or key > best_key:
            best, best_key = rule, key
    return best


# ---------------------------------------------------------------------------
# Alíquotas efetivas do ano (parametrizadas em tax_transition_years)
# ---------------------------------------------------------------------------

def effective_future_rates(
    rule: TaxRule,
    year_row: TaxTransitionYear,
    assumptions: Assumptions,
    scenario: str,
) -> dict[str, Any]:
    premises: list[dict] = []
    warnings: list[str] = []

    cbs_base_pp = Decimal(rule.cbs_rate) if rule.cbs_rate is not None else Decimal(assumptions.cbs_reference_rate)
    ibs_base_pp = Decimal(rule.ibs_rate) if rule.ibs_rate is not None else Decimal(assumptions.ibs_reference_rate)
    if rule.cbs_rate is None:
        premises.append({"chave": "cbs_reference_rate", "valor": _f(cbs_base_pp), "configuravel": True,
                         "descricao": "Alíquota de referência CBS (estimativa; regulamentação pendente)"})
    if rule.ibs_rate is None:
        premises.append({"chave": "ibs_reference_rate", "valor": _f(ibs_base_pp), "configuravel": True,
                         "descricao": "Alíquota de referência IBS (estimativa; regulamentação pendente)"})

    scenario_delta = ZERO
    adj = assumptions.scenario_adjustments.get(scenario)
    if adj is not None:
        scenario_delta = Decimal(adj.rate_delta_pp)

    # CBS
    if year_row.cbs_rate_override is not None:
        cbs_pp = Decimal(year_row.cbs_rate_override)
        premises.append({"chave": f"cbs_override_{year_row.year}", "valor": _f(cbs_pp), "configuravel": True,
                         "descricao": f"Alíquota CBS fixada para {year_row.year} (ano de transição)"})
    else:
        cbs_pp = cbs_base_pp * Decimal(year_row.cbs_factor) + Decimal(year_row.cbs_adjustment_pp)

    # IBS
    if year_row.ibs_rate_override is not None:
        ibs_pp = Decimal(year_row.ibs_rate_override)
        premises.append({"chave": f"ibs_override_{year_row.year}", "valor": _f(ibs_pp), "configuravel": True,
                         "descricao": f"Alíquota IBS fixada para {year_row.year} (ano de transição)"})
    else:
        ibs_pp = ibs_base_pp * Decimal(year_row.ibs_factor)

    # Ajuste de cenário: somente sobre componentes derivados da referência
    # (overrides legais do ano-teste não variam por cenário)
    if scenario_delta != ZERO:
        total = cbs_pp + ibs_pp
        adj_applied = ZERO
        if total > ZERO:
            if year_row.cbs_rate_override is None:
                cbs_share = cbs_pp / total
                cbs_pp += scenario_delta * cbs_share
                adj_applied += scenario_delta * cbs_share
            if year_row.ibs_rate_override is None:
                ibs_share = ibs_pp / total
                ibs_pp += scenario_delta * ibs_share
                adj_applied += scenario_delta * ibs_share
        premises.append({"chave": f"cenario_{scenario}", "valor": _f(scenario_delta), "configuravel": True,
                         "descricao": f"Ajuste do cenário '{scenario}' em p.p. (aplicado: {_f(adj_applied)})"})

    cbs_pp = max(cbs_pp, ZERO)
    ibs_pp = max(ibs_pp, ZERO)

    # Reduções de base/alíquota da regra (ex.: cesta básica 100%, saúde/educação 60%)
    cbs_red = _pct_to_frac(Decimal(rule.cbs_reduction_pct))
    ibs_red = _pct_to_frac(Decimal(rule.ibs_reduction_pct))
    cbs_eff_pp = cbs_pp * (Decimal("1") - cbs_red)
    ibs_eff_pp = ibs_pp * (Decimal("1") - ibs_red)

    is_pp = ZERO
    if year_row.selective_active and Decimal(rule.is_rate) > ZERO:
        is_pp = Decimal(rule.is_rate)
        warnings.append(
            "Imposto Seletivo aplicado com alíquota parametrizada na regra; "
            "alíquotas definitivas do IS dependem de regulamentação específica."
        )

    return {
        "cbs_pp": _rate(cbs_eff_pp),
        "ibs_pp": _rate(ibs_eff_pp),
        "is_pp": _rate(is_pp),
        "cbs_reduction_pct": Decimal(rule.cbs_reduction_pct),
        "ibs_reduction_pct": Decimal(rule.ibs_reduction_pct),
        "premises": premises,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Cálculo por item × ano
# ---------------------------------------------------------------------------

def compute_item_year(
    item: Product | Service,
    kind: str,
    company: Company,
    rule: TaxRule,
    year_row: TaxTransitionYear,
    assumptions: Assumptions,
    scenario: str,
) -> ItemYearResult:
    price = Decimal(item.unit_price)
    cost = Decimal(item.unit_cost or ZERO)
    volume = Decimal(item.monthly_volume or ZERO)
    base = _money(price * volume * MONTHS)  # receita anual estimada

    formulas: list[str] = []
    premises: list[dict] = []
    warnings: list[str] = []

    if company.tax_regime == "simples":
        return _compute_simples(item, kind, company, rule, year_row, assumptions, base, price, cost)

    # ----------------------- Cenário ATUAL (fração da receita) ---------------
    icms = _pct_to_frac(Decimal(rule.icms_rate)) if kind == "product" else ZERO
    iss = _pct_to_frac(Decimal(rule.iss_rate)) if kind == "service" else ZERO
    pis = _pct_to_frac(Decimal(rule.pis_rate))
    cofins = _pct_to_frac(Decimal(rule.cofins_rate))
    ipi = _pct_to_frac(Decimal(rule.ipi_rate)) if kind == "product" else ZERO
    r_current_debits = icms + iss + pis + cofins + ipi

    input_ratio = Decimal(assumptions.input_cost_creditable_ratio)
    cur_eff = Decimal(assumptions.current_credit_efficiency)
    creditable_current = (icms + pis + cofins) if kind == "product" else (pis + cofins)
    if not rule.credit_allowed:
        creditable_current = ZERO
    r_current_credits = input_ratio * creditable_current * cur_eff
    r_current_net = r_current_debits - r_current_credits

    premises.append({"chave": "input_cost_creditable_ratio", "valor": _f(input_ratio), "configuravel": True,
                     "descricao": "% do preço correspondente a insumos creditáveis (premissa)"})
    premises.append({"chave": "current_credit_efficiency", "valor": _f(cur_eff), "configuravel": True,
                     "descricao": "Eficiência de aproveitamento de créditos no sistema atual (premissa)"})
    if assumptions.icms_inside_price and icms > ZERO:
        warnings.append(
            "Premissa simplificadora: ICMS tratado como percentual direto sobre o preço "
            "(cálculo 'por dentro' detalhado na fase 2 com documentos fiscais reais)."
        )

    # ----------------------- Cenário FUTURO (ano Y) --------------------------
    fut = effective_future_rates(rule, year_row, assumptions, scenario)
    premises.extend(fut["premises"])
    warnings.extend(fut["warnings"])
    cbs_f = _pct_to_frac(fut["cbs_pp"])
    ibs_f = _pct_to_frac(fut["ibs_pp"])
    is_f = _pct_to_frac(fut["is_pp"])

    legacy_factor = Decimal(year_row.legacy_icms_iss_factor)
    pc_factor = Decimal(year_row.pis_cofins_factor)
    r_legacy = (icms + iss) * legacy_factor + (pis + cofins + ipi) * pc_factor

    # Créditos do sistema futuro = crédito amplo de CBS/IBS + créditos dos tributos
    # legados remanescentes no ano (ICMS/PIS/Cofins residuais seguem creditáveis
    # na proporção dos fatores de transição; ISS e IPI permanecem não creditáveis).
    fut_eff = Decimal(assumptions.future_credit_efficiency)
    creditable_legacy = (icms * legacy_factor + (pis + cofins) * pc_factor) if kind == "product" \
        else (pis + cofins) * pc_factor
    if not rule.credit_allowed:
        creditable_legacy = ZERO
    r_legacy_credits = input_ratio * creditable_legacy * cur_eff
    r_cbs_ibs_credits = input_ratio * (cbs_f + ibs_f) * fut_eff if rule.credit_allowed else ZERO
    premises.append({"chave": "future_credit_efficiency", "valor": _f(fut_eff), "configuravel": True,
                     "descricao": "Eficiência de créditos no modelo CBS/IBS (crédito amplo; premissa)"})
    if not rule.credit_allowed:
        warnings.append("Regra define operação sem direito a crédito (credit_allowed=false): créditos zerados.")

    # Ano-teste (2026): CBS/IBS compensáveis com PIS/Cofins (parametrizável).
    # O valor de teste é neutralizado pela compensação — não gera crédito próprio.
    compensation = ZERO
    if year_row.test_year_compensable:
        compensation = min(cbs_f + ibs_f, (pis + cofins) * pc_factor)
        r_cbs_ibs_credits = ZERO
        warnings.append(
            f"Ano-teste {year_row.year}: CBS/IBS compensáveis com PIS/Cofins "
            "(LC 214/2025; premissa test_year_compensable)."
        )

    r_future_credits = r_cbs_ibs_credits + r_legacy_credits
    r_future_net = cbs_f + ibs_f + is_f + r_legacy - r_future_credits - compensation

    # ----------------------- Valores anuais ----------------------------------
    current_tax_total = _money(base * r_current_debits)
    current_credits = _money(base * r_current_credits)
    current_net = _money(base * r_current_net)
    future_cbs = _money(base * cbs_f)
    future_ibs = _money(base * ibs_f)
    future_is = _money(base * is_f)
    future_legacy = _money(base * r_legacy)
    future_credits = _money(base * (r_future_credits + compensation))
    future_net = _money(base * r_future_net)
    delta_net = _money(future_net - current_net)

    # ----------------------- Margens e preço de equilíbrio -------------------
    margin_current = margin_future = None
    breakeven: Decimal | None = None
    needs_adjustment = False
    if price > ZERO:
        margin_current = ((Decimal("1") - r_current_net - cost / price) * HUNDRED).quantize(CENTS, ROUND_HALF_UP)
        margin_future = ((Decimal("1") - r_future_net - cost / price) * HUNDRED).quantize(CENTS, ROUND_HALF_UP)
        delta_r = r_future_net - r_current_net
        if delta_r <= ZERO:
            breakeven = _money(price)
        elif cost > ZERO and (cost / price - delta_r) > ZERO:
            breakeven = _money(cost / (cost / price - delta_r))
            needs_adjustment = breakeven > _money(price)
        else:
            breakeven = None  # aumento de preço não recompõe a margem (custo zero ou Δ muito alto)
            needs_adjustment = True
            warnings.append("Reajuste de preço não recompõe a margem para este item (verificar estrutura de custo).")

    # ----------------------- Split payment (impacto de caixa) ----------------
    cash_flow = ZERO
    if assumptions.split_payment_enabled and (cbs_f + ibs_f) > ZERO:
        float_days = Decimal(assumptions.split_payment_float_days)
        capital = Decimal(assumptions.cost_of_capital_annual)
        cash_flow = _money(base * (cbs_f + ibs_f) * float_days / DAYS_YEAR * capital)
        premises.append({"chave": "split_payment", "valor": f"{assumptions.split_payment_float_days} dias × "
                         f"{_f(capital)} a.a.", "configuravel": True,
                         "descricao": "Custo financeiro anual estimado da antecipação do recolhimento (split payment)"})

    formulas.extend([
        f"Receita anual = {_f(price)} × {_f(volume)} × 12 = {_f(base)}",
        f"Carga atual = base × {_f(_rate(r_current_debits * HUNDRED))}% − créditos {_f(current_credits)} = {_f(current_net)}",
        f"CBS({year_row.year}) = base × {_f(fut['cbs_pp'])}% = {_f(future_cbs)}",
        f"IBS({year_row.year}) = base × {_f(fut['ibs_pp'])}% = {_f(future_ibs)}",
        f"IS({year_row.year}) = base × {_f(fut['is_pp'])}% = {_f(future_is)}",
        f"Tributos legados({year_row.year}) = base × {_f(_rate(r_legacy * HUNDRED))}% = {_f(future_legacy)}",
        f"Créditos futuros({year_row.year}) = CBS/IBS {_f(_money(base * r_cbs_ibs_credits))} + "
        f"legados {_f(_money(base * r_legacy_credits))} + compensação {_f(_money(base * compensation))} "
        f"= {_f(future_credits)}",
        f"Carga futura líquida({year_row.year}) = {_f(future_net)} | Δ vs atual = {_f(delta_net)}",
    ])

    memory = {
        "regra": {"id": str(rule.id), "nome": rule.name, "base_legal": rule.legal_basis,
                  "credit_allowed": rule.credit_allowed},
        "ano": year_row.year,
        "fatores_ano": {
            "cbs_factor": _f(Decimal(year_row.cbs_factor)),
            "ibs_factor": _f(Decimal(year_row.ibs_factor)),
            "cbs_rate_override": _f(Decimal(year_row.cbs_rate_override)) if year_row.cbs_rate_override is not None else None,
            "ibs_rate_override": _f(Decimal(year_row.ibs_rate_override)) if year_row.ibs_rate_override is not None else None,
            "cbs_adjustment_pp": _f(Decimal(year_row.cbs_adjustment_pp)),
            "legacy_icms_iss_factor": _f(legacy_factor),
            "pis_cofins_factor": _f(pc_factor),
            "selective_active": year_row.selective_active,
            "test_year_compensable": year_row.test_year_compensable,
        },
        "aliquotas_atuais_pp": {"icms": _f(Decimal(rule.icms_rate)), "iss": _f(Decimal(rule.iss_rate)),
                                "pis": _f(Decimal(rule.pis_rate)), "cofins": _f(Decimal(rule.cofins_rate)),
                                "ipi": _f(Decimal(rule.ipi_rate))},
        "aliquotas_futuras_efetivas_pp": {"cbs": _f(fut["cbs_pp"]), "ibs": _f(fut["ibs_pp"]), "is": _f(fut["is_pp"]),
                                          "reducao_cbs_pct": _f(fut["cbs_reduction_pct"]),
                                          "reducao_ibs_pct": _f(fut["ibs_reduction_pct"])},
        "formulas": formulas,
        "premissas": premises,
        "avisos": warnings,
    }

    return ItemYearResult(
        item_kind=kind, item_id=item.id, item_name=item.name, tax_rule_id=rule.id, year=year_row.year,
        annual_revenue=base, current_tax_total=current_tax_total, current_credits=current_credits,
        current_net_burden=current_net, future_cbs=future_cbs, future_ibs=future_ibs, future_is=future_is,
        future_legacy=future_legacy, future_credits=future_credits, future_net_burden=future_net,
        delta_net=delta_net, margin_current_pct=margin_current, margin_future_pct=margin_future,
        breakeven_price=breakeven, cash_flow_impact=cash_flow, calc_memory=memory,
        needs_price_adjustment=needs_adjustment,
    )


def _compute_simples(item, kind, company, rule, year_row, assumptions, base, price, cost) -> ItemYearResult:
    """Simples Nacional: LC 214/2025 mantém o regime; simulação assume permanência.

    Carga atual ≈ carga futura = alíquota efetiva do Simples (premissa configurável).
    Gera aviso para estudo de migração ao regime regular (crédito amplo aos clientes).
    """
    rate = _pct_to_frac(Decimal(assumptions.simples_effective_rate))
    net = _money(base * rate)
    margin = None
    if price > ZERO:
        margin = ((Decimal("1") - rate - cost / price) * HUNDRED).quantize(CENTS, ROUND_HALF_UP)
    memory = {
        "regra": {"id": str(rule.id), "nome": rule.name, "base_legal": rule.legal_basis},
        "ano": year_row.year,
        "regime": "simples",
        "formulas": [f"Carga (Simples) = base {_f(base)} × {_f(Decimal(assumptions.simples_effective_rate))}% = {_f(net)}"],
        "premissas": [{"chave": "simples_effective_rate", "valor": _f(Decimal(assumptions.simples_effective_rate)),
                       "configuravel": True, "descricao": "Alíquota efetiva média do Simples Nacional (premissa)"}],
        "avisos": [
            "Empresa no Simples Nacional: a reforma mantém o regime (LC 214/2025). "
            "Simulação assume permanência — recomendamos estudo de migração para o regime regular, "
            "pois clientes no novo modelo poderão preferir fornecedores que transferem crédito de CBS/IBS.",
        ],
    }
    return ItemYearResult(
        item_kind=kind, item_id=item.id, item_name=item.name, tax_rule_id=rule.id, year=year_row.year,
        annual_revenue=base, current_tax_total=net, current_credits=ZERO, current_net_burden=net,
        future_cbs=ZERO, future_ibs=ZERO, future_is=ZERO, future_legacy=net, future_credits=ZERO,
        future_net_burden=net, delta_net=ZERO, margin_current_pct=margin, margin_future_pct=margin,
        breakeven_price=_money(price) if price > ZERO else None, cash_flow_impact=ZERO,
        calc_memory=memory, needs_price_adjustment=False,
    )


def simulate_items(
    items: list[tuple[str, Product | Service]],
    company: Company,
    rules: list[TaxRule],
    years: list[TaxTransitionYear],
    assumptions: Assumptions,
    scenario: str,
) -> tuple[list[ItemYearResult], list[UnmatchedItem]]:
    """Executa a simulação completa: cada item × cada ano da transição."""
    results: list[ItemYearResult] = []
    unmatched: list[UnmatchedItem] = []
    for kind, item in items:
        rule = match_rule(item, kind, company, rules)
        if rule is None:
            unmatched.append(UnmatchedItem(item_kind=kind, item_id=item.id, item_name=item.name))
            continue
        for year_row in years:
            results.append(compute_item_year(item, kind, company, rule, year_row, assumptions, scenario))
    return results, unmatched
