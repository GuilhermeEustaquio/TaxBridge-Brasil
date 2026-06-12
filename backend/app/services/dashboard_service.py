"""Agregações do dashboard: KPIs, série anual, alertas de risco e onboarding."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Company, ComplianceTask, Product, Service, Simulation, TaxRule
from app.schemas.common import COMPLIANCE_AREAS


def compliance_summary(db: Session, organization_id: uuid.UUID, company_id: uuid.UUID | None) -> dict:
    query = select(ComplianceTask).where(
        ComplianceTask.organization_id == organization_id,
        ComplianceTask.deleted_at.is_(None),
    )
    if company_id:
        query = query.where(ComplianceTask.company_id == company_id)
    tasks = db.scalars(query).all()

    today = date.today()
    by_area: dict[str, dict] = {area: {"area": area, "total": 0, "done": 0, "overdue": 0} for area in sorted(COMPLIANCE_AREAS)}
    done = overdue = critical = 0
    for task in tasks:
        bucket = by_area.setdefault(task.area, {"area": task.area, "total": 0, "done": 0, "overdue": 0})
        bucket["total"] += 1
        is_overdue = task.status in {"vencido"} or (
            task.due_date is not None and task.due_date < today and task.status not in {"concluido"}
        )
        if task.status == "concluido":
            bucket["done"] += 1
            done += 1
        elif is_overdue:
            bucket["overdue"] += 1
            overdue += 1
        if task.status == "critico":
            critical += 1

    areas_out = []
    for area, bucket in by_area.items():
        total = bucket["total"]
        areas_out.append({
            "area": area, "total": total, "done": bucket["done"], "overdue": bucket["overdue"],
            "progress_pct": round(bucket["done"] / total * 100, 1) if total else 0.0,
        })
    total_tasks = len(tasks)
    return {
        "overall_progress_pct": round(done / total_tasks * 100, 1) if total_tasks else 0.0,
        "total": total_tasks, "done": done, "overdue": overdue, "critical": critical,
        "by_area": areas_out,
    }


def build_alerts(simulation: Simulation | None, compliance: dict, company: Company | None) -> list[dict]:
    alerts: list[dict] = []
    if simulation is not None:
        summary = simulation.summary or {}
        for item in summary.get("items_without_rule", []):
            alerts.append({
                "level": "critico",
                "title": f"Item sem parametrização: {item['name']}",
                "detail": "Cadastre uma regra tributária que alcance este item — sem regra não há cálculo.",
            })
        totals = summary.get("totals", {})
        delta_pct = totals.get("delta_pct_revenue_final_year") or 0
        if delta_pct >= 1:
            alerts.append({
                "level": "alto",
                "title": f"Aumento de carga estimado em {delta_pct:.1f}% da receita em {totals.get('final_year')}",
                "detail": "Revisar formação de preços e estrutura de créditos (ver simulação).",
            })
        needing = summary.get("items_needing_price_adjustment", [])
        if needing:
            alerts.append({
                "level": "medio",
                "title": f"{len(needing)} item(ns) precisam de reajuste de preço para manter margem",
                "detail": ", ".join(needing[:5]) + ("..." if len(needing) > 5 else ""),
            })
        years = summary.get("years", [])
        is_total = sum((y.get("is") or 0) for y in years)
        if is_total > 0:
            alerts.append({
                "level": "alto",
                "title": "Itens sujeitos ao Imposto Seletivo na carteira",
                "detail": "Alíquotas do IS dependem de regulamentação — valores simulados são premissas configuráveis.",
            })
    if company is not None and company.tax_regime == "simples":
        alerts.append({
            "level": "medio",
            "title": "Empresa no Simples Nacional",
            "detail": "Avaliar migração para o regime regular: clientes poderão preferir fornecedores com crédito pleno de CBS/IBS.",
        })
    if compliance.get("overdue"):
        alerts.append({
            "level": "alto",
            "title": f"{compliance['overdue']} tarefa(s) de adequação vencida(s)",
            "detail": "Atualize o checklist de compliance da Reforma.",
        })
    if compliance.get("critical"):
        alerts.append({
            "level": "critico",
            "title": f"{compliance['critical']} tarefa(s) crítica(s) no checklist",
            "detail": "Priorize as tarefas marcadas como críticas.",
        })
    return alerts


def build_dashboard(db: Session, organization_id: uuid.UUID, company_id: uuid.UUID | None) -> dict:
    company = None
    if company_id:
        company = db.get(Company, company_id)
        if company is None or company.organization_id != organization_id or company.deleted_at is not None:
            company = None
            company_id = None

    sim_query = (
        select(Simulation)
        .where(Simulation.organization_id == organization_id, Simulation.deleted_at.is_(None))
        .order_by(Simulation.created_at.desc())
    )
    if company_id:
        sim_query = sim_query.where(Simulation.company_id == company_id)
    simulation = db.scalars(sim_query.limit(1)).first()

    compliance = compliance_summary(db, organization_id, company_id)

    def _count(model) -> int:
        query = select(func.count()).select_from(model).where(
            model.organization_id == organization_id, model.deleted_at.is_(None)
        )
        if company_id is not None and hasattr(model, "company_id"):
            query = query.where(model.company_id == company_id)
        return db.scalar(query) or 0

    counts = {
        "companies": _count(Company),
        "products": _count(Product),
        "services": _count(Service),
        "tax_rules": db.scalar(
            select(func.count()).select_from(TaxRule).where(
                TaxRule.organization_id == organization_id,
                TaxRule.deleted_at.is_(None),
                TaxRule.is_active.is_(True),
            )
        ) or 0,
        "simulations": db.scalar(
            select(func.count()).select_from(Simulation).where(
                Simulation.organization_id == organization_id, Simulation.deleted_at.is_(None)
            )
        ) or 0,
    }

    return {
        "company": {
            "id": str(company.id), "legal_name": company.legal_name,
            "tax_regime": company.tax_regime, "uf": company.uf,
        } if company else None,
        "latest_simulation": {
            "id": str(simulation.id), "name": simulation.name, "scenario": simulation.scenario,
            "created_at": simulation.created_at.isoformat(),
            "summary": simulation.summary,
        } if simulation else None,
        "alerts": build_alerts(simulation, compliance, company),
        "compliance": compliance,
        "counts": counts,
        "onboarding": {
            "has_company": counts["companies"] > 0,
            "has_items": (counts["products"] + counts["services"]) > 0,
            "has_rules": counts["tax_rules"] > 0,
            "has_simulation": counts["simulations"] > 0,
        },
    }
