"""Testes do motor tributário: matching de regras, fatores de transição e cálculos."""

import uuid
from decimal import Decimal

import pytest

from app.models import Company, Product, Service, TaxRule, TaxTransitionYear
from app.schemas.org import Assumptions
from app.services import tax_engine
from app.services.tax_defaults import DEFAULT_TRANSITION_YEARS


def make_company(regime="real", uf="SP") -> Company:
    return Company(id=uuid.uuid4(), organization_id=uuid.uuid4(), legal_name="Empresa X",
                   cnpj="12.345.678/0001-95", tax_regime=regime, uf=uf)


def make_product(company, ncm="22021000", price="10.00", cost="4.00", volume="1000", **kw) -> Product:
    return Product(id=uuid.uuid4(), organization_id=company.organization_id, company_id=company.id,
                   sku="SKU-1", name="Produto", ncm=ncm, unit_price=Decimal(price),
                   unit_cost=Decimal(cost), monthly_volume=Decimal(volume), **kw)


def make_rule(**kw) -> TaxRule:
    defaults = dict(
        id=uuid.uuid4(), organization_id=uuid.uuid4(), name="Regra", item_kind="any",
        priority=0, icms_rate=Decimal("0"), iss_rate=Decimal("0"), pis_rate=Decimal("0"),
        cofins_rate=Decimal("0"), ipi_rate=Decimal("0"), is_rate=Decimal("0"),
        cbs_reduction_pct=Decimal("0"), ibs_reduction_pct=Decimal("0"), credit_allowed=True,
        is_active=True, cbs_rate=None, ibs_rate=None, company_id=None,
        ncm_pattern=None, nbs_pattern=None, cfop=None, uf_origin=None, uf_dest=None, tax_regime=None,
        created_at=None, updated_at=None,
    )
    defaults.update(kw)
    return TaxRule(**defaults)


def year_row(year: int, org_id=None) -> TaxTransitionYear:
    data = next(d for d in DEFAULT_TRANSITION_YEARS if d["year"] == year)
    return TaxTransitionYear(id=uuid.uuid4(), organization_id=org_id or uuid.uuid4(), **data)


# ----------------------------- Matching de regras ----------------------------

def test_match_prefers_most_specific_rule():
    company = make_company()
    product = make_product(company, ncm="22021000")
    generic = make_rule(name="Geral", item_kind="product")
    specific = make_rule(name="Refrigerantes", item_kind="product", ncm_pattern="2202*")
    exact = make_rule(name="Exata", item_kind="product", ncm_pattern="22021000")
    chosen = tax_engine.match_rule(product, "product", company, [generic, specific, exact])
    assert chosen.name == "Exata"


def test_match_disqualifies_on_filled_mismatch():
    company = make_company(uf="SP")
    product = make_product(company, ncm="10063021")
    rule_rj = make_rule(item_kind="product", uf_origin="RJ")
    assert tax_engine.match_rule(product, "product", company, [rule_rj]) is None


def test_match_returns_none_without_rules():
    company = make_company()
    product = make_product(company)
    results, unmatched = tax_engine.simulate_items(
        [("product", product)], company, [], [year_row(2033)], Assumptions(), "provavel"
    )
    assert results == []
    assert len(unmatched) == 1
    assert unmatched[0].item_name == "Produto"


def test_service_rule_does_not_match_product():
    company = make_company()
    product = make_product(company)
    service_rule = make_rule(item_kind="service", nbs_pattern="1.14*")
    assert tax_engine.match_rule(product, "product", company, [service_rule]) is None


# ------------------------- Fatores por ano de transição ----------------------

ASSUMPTIONS = Assumptions()  # CBS ref 8.8 / IBS ref 17.7


def std_rule(**kw):
    return make_rule(item_kind="product", icms_rate=Decimal("18"), pis_rate=Decimal("1.65"),
                     cofins_rate=Decimal("7.6"), **kw)


def compute(year: int, rule=None, company=None, product=None, scenario="provavel"):
    company = company or make_company()
    product = product or make_product(company)
    rule = rule or std_rule()
    return tax_engine.compute_item_year(product, "product", company, rule, year_row(year), ASSUMPTIONS, scenario)


def test_2026_test_year_rates_and_compensation():
    result = compute(2026)
    base = Decimal("120000.00")  # 10 × 1000 × 12
    assert result.annual_revenue == base
    # Overrides legais do ano-teste: CBS 0,9% + IBS 0,1%
    assert result.future_cbs == Decimal("1080.00")
    assert result.future_ibs == Decimal("120.00")
    # Compensável com PIS/Cofins → carga líquida 2026 ≈ carga atual
    assert result.future_net_burden == result.current_net_burden
    assert result.calc_memory["fatores_ano"]["test_year_compensable"] is True


def test_2027_pis_cofins_extinct_cbs_full():
    result = compute(2027)
    base = Decimal("120000.00")
    # CBS = (8.8 × 1.0 − 0.1)% = 8.7%
    assert result.future_cbs == (base * Decimal("0.087")).quantize(Decimal("0.01"))
    assert result.future_ibs == (base * Decimal("0.001")).quantize(Decimal("0.01"))
    # Legado 2027: ICMS 18% permanece; PIS/Cofins extintos (fator 0)
    assert result.future_legacy == (base * Decimal("0.18")).quantize(Decimal("0.01"))


def test_transition_ramp_2029_to_2032():
    legacy_factors = {2029: Decimal("0.9"), 2030: Decimal("0.8"), 2031: Decimal("0.7"), 2032: Decimal("0.6")}
    ibs_factors = {2029: Decimal("0.1"), 2030: Decimal("0.2"), 2031: Decimal("0.3"), 2032: Decimal("0.4")}
    base = Decimal("120000.00")
    for year, factor in legacy_factors.items():
        result = compute(year)
        expected_legacy = (base * Decimal("0.18") * factor).quantize(Decimal("0.01"))
        assert result.future_legacy == expected_legacy, f"legado {year}"
        expected_ibs = (base * Decimal("17.7") / 100 * ibs_factors[year]).quantize(Decimal("0.01"))
        assert result.future_ibs == expected_ibs, f"ibs {year}"


def test_2033_full_model_no_legacy():
    result = compute(2033)
    base = Decimal("120000.00")
    assert result.future_legacy == Decimal("0.00")
    assert result.future_cbs == (base * Decimal("0.088")).quantize(Decimal("0.01"))
    assert result.future_ibs == (base * Decimal("0.177")).quantize(Decimal("0.01"))


# ----------------------------- Exceções e reduções ---------------------------

def test_cesta_basica_100pct_reduction_zeroes_cbs_ibs():
    rule = make_rule(item_kind="product", ncm_pattern="1006*", icms_rate=Decimal("7"),
                     cbs_reduction_pct=Decimal("100"), ibs_reduction_pct=Decimal("100"))
    company = make_company()
    product = make_product(company, ncm="10063021")
    result = tax_engine.compute_item_year(product, "product", company, rule, year_row(2033), ASSUMPTIONS, "provavel")
    assert result.future_cbs == Decimal("0.00")
    assert result.future_ibs == Decimal("0.00")
    assert result.future_net_burden <= Decimal("0.00")  # créditos podem zerar/negativar a carga


def test_selective_tax_applies_only_when_active():
    rule = std_rule(is_rate=Decimal("10"))
    base = Decimal("120000.00")
    assert compute(2026, rule=rule).future_is == Decimal("0.00")  # IS só a partir de 2027
    result_2027 = compute(2027, rule=rule)
    assert result_2027.future_is == (base * Decimal("0.10")).quantize(Decimal("0.01"))
    assert any("Seletivo" in warning for warning in result_2027.calc_memory["avisos"])


def test_credit_allowed_false_zeroes_credits():
    result = compute(2033, rule=std_rule(credit_allowed=False))
    assert result.current_credits == Decimal("0.00")
    assert result.future_credits == Decimal("0.00")


def test_simples_nacional_keeps_regime_and_warns():
    company = make_company(regime="simples")
    product = make_product(company)
    rule = make_rule(item_kind="any", tax_regime="simples")
    result = tax_engine.compute_item_year(product, "product", company, rule, year_row(2030), ASSUMPTIONS, "provavel")
    base = Decimal("120000.00")
    expected = (base * Decimal("0.08")).quantize(Decimal("0.01"))  # simples_effective_rate 8%
    assert result.current_net_burden == expected
    assert result.future_net_burden == expected
    assert result.delta_net == Decimal("0.00")
    assert any("Simples" in warning for warning in result.calc_memory["avisos"])


# --------------------------- Cenários e indicadores --------------------------

def test_scenario_adjustment_changes_future_burden():
    provavel = compute(2033, scenario="provavel")
    conservador = compute(2033, scenario="conservador")
    agressivo = compute(2033, scenario="agressivo")
    assert conservador.future_net_burden > provavel.future_net_burden > agressivo.future_net_burden


def test_scenario_does_not_change_test_year_overrides():
    # 2026 usa overrides legais (0,9/0,1) — cenário não altera
    assert compute(2026, scenario="conservador").future_cbs == compute(2026, scenario="provavel").future_cbs


def test_breakeven_price_restores_margin():
    result = compute(2033)
    assert result.margin_current_pct is not None and result.margin_future_pct is not None
    if result.delta_net > 0:
        assert result.breakeven_price is not None
        assert result.breakeven_price > Decimal("10.00")
        assert result.needs_price_adjustment is True


def test_cash_flow_impact_split_payment():
    result = compute(2033)
    # (CBS+IBS) × 40/365 × 12% — premissas default
    expected = ((result.future_cbs + result.future_ibs) * Decimal("40") / Decimal("365") * Decimal("0.12")
                ).quantize(Decimal("0.01"))
    assert result.cash_flow_impact == expected


def test_calc_memory_is_complete_and_traceable():
    result = compute(2030)
    memory = result.calc_memory
    assert memory["regra"]["nome"] == "Regra"
    assert memory["ano"] == 2030
    assert memory["fatores_ano"]["legacy_icms_iss_factor"] == pytest.approx(0.8)
    assert any(p["chave"] == "cbs_reference_rate" and p["configuravel"] for p in memory["premissas"])
    assert len(memory["formulas"]) >= 5


def test_service_uses_iss_not_icms():
    company = make_company()
    service = Service(id=uuid.uuid4(), organization_id=company.organization_id, company_id=company.id,
                      code="SRV-1", name="Consultoria", nbs="1.1501", unit_price=Decimal("1000"),
                      unit_cost=Decimal("300"), monthly_volume=Decimal("10"))
    rule = make_rule(item_kind="service", iss_rate=Decimal("5"), pis_rate=Decimal("1.65"),
                     cofins_rate=Decimal("7.6"), icms_rate=Decimal("99"))  # icms deve ser ignorado
    result = tax_engine.compute_item_year(service, "service", company, rule, year_row(2033), ASSUMPTIONS, "provavel")
    base = Decimal("120000.00")
    expected_current = (base * (Decimal("5") + Decimal("1.65") + Decimal("7.6")) / 100).quantize(Decimal("0.01"))
    assert result.current_tax_total == expected_current
    # Serviços no Lucro Real: aumento relevante de carga em 2033 (história central da reforma)
    assert result.delta_net > 0
