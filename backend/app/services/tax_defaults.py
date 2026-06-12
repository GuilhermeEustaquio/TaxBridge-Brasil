"""Defaults do calendário de transição (EC 132/2023 + LC 214/2025).

Estes valores são SEMENTES copiadas para `tax_transition_years` de cada
organização no momento do cadastro — a partir daí são dados editáveis pelo
administrador (UI Parâmetros), nunca constantes de código consultadas pelo motor.
"""

from decimal import Decimal

DEFAULT_TRANSITION_YEARS: list[dict] = [
    dict(year=2026, cbs_factor=Decimal("0"), ibs_factor=Decimal("0"),
         cbs_rate_override=Decimal("0.9"), ibs_rate_override=Decimal("0.1"),
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("1"),
         pis_cofins_factor=Decimal("1"), selective_active=False, test_year_compensable=True,
         notes="Ano-teste: CBS 0,9% + IBS 0,1%, compensáveis com PIS/Cofins (LC 214/2025)."),
    dict(year=2027, cbs_factor=Decimal("1"), ibs_factor=Decimal("0"),
         cbs_rate_override=None, ibs_rate_override=Decimal("0.1"),
         cbs_adjustment_pp=Decimal("-0.1"), legacy_icms_iss_factor=Decimal("1"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="CBS plena substitui PIS/Cofins; IBS 0,1%; CBS reduzida em 0,1 p.p.; IS em vigor; IPI zerado (exceto ZFM)."),
    dict(year=2028, cbs_factor=Decimal("1"), ibs_factor=Decimal("0"),
         cbs_rate_override=None, ibs_rate_override=Decimal("0.1"),
         cbs_adjustment_pp=Decimal("-0.1"), legacy_icms_iss_factor=Decimal("1"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="Igual a 2027."),
    dict(year=2029, cbs_factor=Decimal("1"), ibs_factor=Decimal("0.1"),
         cbs_rate_override=None, ibs_rate_override=None,
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("0.9"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="Início da transição IBS: ICMS/ISS a 90%; IBS a 10% da referência (proporção premissa configurável)."),
    dict(year=2030, cbs_factor=Decimal("1"), ibs_factor=Decimal("0.2"),
         cbs_rate_override=None, ibs_rate_override=None,
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("0.8"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="ICMS/ISS a 80%; IBS a 20%."),
    dict(year=2031, cbs_factor=Decimal("1"), ibs_factor=Decimal("0.3"),
         cbs_rate_override=None, ibs_rate_override=None,
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("0.7"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="ICMS/ISS a 70%; IBS a 30%."),
    dict(year=2032, cbs_factor=Decimal("1"), ibs_factor=Decimal("0.4"),
         cbs_rate_override=None, ibs_rate_override=None,
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("0.6"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="ICMS/ISS a 60%; IBS a 40%."),
    dict(year=2033, cbs_factor=Decimal("1"), ibs_factor=Decimal("1"),
         cbs_rate_override=None, ibs_rate_override=None,
         cbs_adjustment_pp=Decimal("0"), legacy_icms_iss_factor=Decimal("0"),
         pis_cofins_factor=Decimal("0"), selective_active=True, test_year_compensable=False,
         notes="Modelo integral: ICMS e ISS extintos; CBS + IBS plenos."),
]


def build_transition_rows(organization_id) -> list[dict]:
    return [{"organization_id": organization_id, **row} for row in DEFAULT_TRANSITION_YEARS]
