"""Orquestração de simulações: carrega dados, executa o motor e persiste resultados."""

import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Company,
    Organization,
    Product,
    Service,
    Simulation,
    SimulationItem,
    TaxRule,
    TaxTransitionYear,
    User,
)
from app.schemas.org import Assumptions
from app.services import tax_engine
from app.services.tax_engine import ItemYearResult, UnmatchedItem


def _f(x: Decimal | None) -> float | None:
    return None if x is None else float(x)


def load_assumptions(org_assumptions: dict, override: dict | None = None) -> Assumptions:
    data = dict(org_assumptions or {})
    if override:
        data.update(override)
    return Assumptions(**data)


def run_simulation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    company: Company,
    user: User | None,
    name: str,
    scenario: str,
    year_start: int,
    year_end: int,
    assumptions_override: dict | None = None,
    origin: str = "manual",
) -> Simulation:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(404, "Organização não encontrada")
    assumptions = load_assumptions(organization.assumptions, assumptions_override)

    products = db.scalars(
        select(Product).where(
            Product.organization_id == organization_id,
            Product.company_id == company.id,
            Product.deleted_at.is_(None),
        )
    ).all()
    services = db.scalars(
        select(Service).where(
            Service.organization_id == organization_id,
            Service.company_id == company.id,
            Service.deleted_at.is_(None),
        )
    ).all()
    items: list[tuple[str, Product | Service]] = [("product", p) for p in products] + [
        ("service", s) for s in services
    ]
    if not items:
        raise HTTPException(422, "A empresa não possui produtos ou serviços cadastrados para simular")

    rules = db.scalars(
        select(TaxRule).where(
            TaxRule.organization_id == organization_id,
            TaxRule.is_active.is_(True),
            TaxRule.deleted_at.is_(None),
        )
    ).all()
    years = db.scalars(
        select(TaxTransitionYear)
        .where(
            TaxTransitionYear.organization_id == organization_id,
            TaxTransitionYear.year >= year_start,
            TaxTransitionYear.year <= year_end,
        )
        .order_by(TaxTransitionYear.year)
    ).all()
    if not years:
        raise HTTPException(422, "Anos de transição não parametrizados para a organização")

    results, unmatched = tax_engine.simulate_items(items, company, rules, years, assumptions, scenario)

    simulation = Simulation(
        organization_id=organization_id,
        company_id=company.id,
        created_by=user.id if user else None,
        name=name,
        scenario=scenario,
        year_start=year_start,
        year_end=year_end,
        status="concluida",
        origin=origin,
        assumptions_snapshot=assumptions.model_dump(mode="json"),
        summary=build_summary(results, unmatched, [y.year for y in years]),
    )
    db.add(simulation)
    db.flush()

    for r in results:
        db.add(
            SimulationItem(
                simulation_id=simulation.id,
                item_kind=r.item_kind,
                item_id=r.item_id,
                item_name=r.item_name,
                tax_rule_id=r.tax_rule_id,
                year=r.year,
                annual_revenue=r.annual_revenue,
                current_tax_total=r.current_tax_total,
                current_credits=r.current_credits,
                current_net_burden=r.current_net_burden,
                future_cbs=r.future_cbs,
                future_ibs=r.future_ibs,
                future_is=r.future_is,
                future_legacy=r.future_legacy,
                future_credits=r.future_credits,
                future_net_burden=r.future_net_burden,
                delta_net=r.delta_net,
                margin_current_pct=r.margin_current_pct,
                margin_future_pct=r.margin_future_pct,
                breakeven_price=r.breakeven_price,
                cash_flow_impact=r.cash_flow_impact,
                calc_memory=r.calc_memory,
            )
        )
    return simulation


def build_summary(results: list[ItemYearResult], unmatched: list[UnmatchedItem], years: list[int]) -> dict:
    by_year: dict[int, dict] = {
        y: {
            "year": y, "current_total": Decimal("0"), "future_total": Decimal("0"),
            "cbs": Decimal("0"), "ibs": Decimal("0"), "is": Decimal("0"), "legacy": Decimal("0"),
            "credits_current": Decimal("0"), "credits_future": Decimal("0"),
            "cash_flow_impact": Decimal("0"), "revenue": Decimal("0"), "items_count": 0,
        }
        for y in years
    }
    items_needing_adjustment: set[str] = set()
    for r in results:
        row = by_year[r.year]
        row["current_total"] += r.current_net_burden
        row["future_total"] += r.future_net_burden
        row["cbs"] += r.future_cbs
        row["ibs"] += r.future_ibs
        row["is"] += r.future_is
        row["legacy"] += r.future_legacy
        row["credits_current"] += r.current_credits
        row["credits_future"] += r.future_credits
        row["cash_flow_impact"] += r.cash_flow_impact
        row["revenue"] += r.annual_revenue
        row["items_count"] += 1
        if r.needs_price_adjustment:
            items_needing_adjustment.add(r.item_name)

    years_out = []
    for y in years:
        row = by_year[y]
        delta = row["future_total"] - row["current_total"]
        revenue = row["revenue"]
        years_out.append({
            "year": y,
            "current_total": _f(row["current_total"]),
            "future_total": _f(row["future_total"]),
            "delta": _f(delta),
            "delta_pct_revenue": _f((delta / revenue * 100).quantize(Decimal("0.01"))) if revenue else 0.0,
            "cbs": _f(row["cbs"]), "ibs": _f(row["ibs"]), "is": _f(row["is"]), "legacy": _f(row["legacy"]),
            "credits_current": _f(row["credits_current"]), "credits_future": _f(row["credits_future"]),
            "cash_flow_impact": _f(row["cash_flow_impact"]),
            "revenue": _f(revenue),
            "items_count": row["items_count"],
        })

    final_year = years_out[-1] if years_out else None
    top_items: list[dict] = []
    if final_year is not None:
        last = [r for r in results if r.year == final_year["year"]]
        last.sort(key=lambda r: abs(r.delta_net), reverse=True)
        top_items = [
            {
                "item_name": r.item_name, "item_kind": r.item_kind,
                "delta_net": _f(r.delta_net),
                "current_net": _f(r.current_net_burden), "future_net": _f(r.future_net_burden),
                "margin_current_pct": _f(r.margin_current_pct), "margin_future_pct": _f(r.margin_future_pct),
                "breakeven_price": _f(r.breakeven_price),
            }
            for r in last[:10]
        ]

    return {
        "years": years_out,
        "top_items": top_items,
        "items_without_rule": [{"name": u.item_name, "kind": u.item_kind, "reason": u.reason} for u in unmatched],
        "items_needing_price_adjustment": sorted(items_needing_adjustment),
        "totals": {
            "delta_final_year": final_year["delta"] if final_year else 0.0,
            "delta_pct_revenue_final_year": final_year["delta_pct_revenue"] if final_year else 0.0,
            "final_year": final_year["year"] if final_year else None,
        },
    }
