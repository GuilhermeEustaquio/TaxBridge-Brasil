import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import or_, select

from app.api.v1.common import PageDep, paginate
from app.core.audit import audit
from app.core.deps import (
    LEVEL_ACCOUNTANT,
    LEVEL_CONSULTANT,
    CurrentOrg,
    CurrentUser,
    DbSession,
    get_company_or_404,
    require_level,
)
from app.models import Company, Report, Simulation, SimulationItem
from app.schemas.common import Page
from app.schemas.simulation import SimulationCreate, SimulationItemOut, SimulationListItem, SimulationOut
from app.services.pdf_report import build_simulation_pdf
from app.services.simulation_service import run_simulation
from app.services.xlsx_export import build_simulation_csv, build_simulation_xlsx

router = APIRouter(prefix="/simulations", tags=["Simulações"])


def _get_simulation(db, org_id: uuid.UUID, simulation_id: uuid.UUID) -> Simulation:
    simulation = db.get(Simulation, simulation_id)
    if simulation is None or simulation.organization_id != org_id or simulation.deleted_at is not None:
        raise HTTPException(404, "Simulação não encontrada")
    return simulation


@router.get("", response_model=Page[SimulationListItem])
def list_simulations(db: DbSession, org: CurrentOrg, params: PageDep, company_id: uuid.UUID | None = None):
    query = select(Simulation).where(Simulation.organization_id == org.id, Simulation.deleted_at.is_(None))
    if company_id:
        query = query.where(Simulation.company_id == company_id)
    return paginate(db, query.order_by(Simulation.created_at.desc()), params)


@router.post("", response_model=SimulationOut, status_code=201, dependencies=[require_level(LEVEL_CONSULTANT)])
def create_simulation(payload: SimulationCreate, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    """★ Executa o motor tributário: atual × futuro para cada item × ano da transição."""
    company = get_company_or_404(db, org.id, payload.company_id)
    simulation = run_simulation(
        db, organization_id=org.id, company=company, user=user,
        name=payload.name, scenario=payload.scenario,
        year_start=payload.year_start, year_end=payload.year_end,
        assumptions_override=payload.assumptions_override,
    )
    audit(db, organization_id=org.id, user=user, action="simulation.create",
          entity_type="simulation", entity_id=simulation.id,
          metadata={"scenario": payload.scenario, "years": f"{payload.year_start}-{payload.year_end}"},
          request=request)
    db.commit()
    db.refresh(simulation)
    return simulation


@router.get("/{simulation_id}", response_model=SimulationOut)
def get_simulation(simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg):
    return _get_simulation(db, org.id, simulation_id)


@router.get("/{simulation_id}/items", response_model=Page[SimulationItemOut])
def list_simulation_items(
    simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg, params: PageDep,
    year: int | None = None, search: str | None = None, item_kind: str | None = None,
):
    simulation = _get_simulation(db, org.id, simulation_id)
    query = select(SimulationItem).where(SimulationItem.simulation_id == simulation.id)
    if year:
        query = query.where(SimulationItem.year == year)
    if item_kind:
        query = query.where(SimulationItem.item_kind == item_kind)
    if search:
        query = query.where(or_(SimulationItem.item_name.ilike(f"%{search}%")))
    return paginate(db, query.order_by(SimulationItem.item_name, SimulationItem.year), params)


@router.delete("/{simulation_id}", status_code=204, dependencies=[require_level(LEVEL_ACCOUNTANT)])
def delete_simulation(simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    simulation = _get_simulation(db, org.id, simulation_id)
    simulation.deleted_at = datetime.now(timezone.utc)
    audit(db, organization_id=org.id, user=user, action="simulation.delete",
          entity_type="simulation", entity_id=simulation.id, request=request)
    db.commit()


def _register_report(db, org_id, user, simulation: Simulation, fmt: str, request: Request) -> None:
    db.add(Report(
        organization_id=org_id, company_id=simulation.company_id, simulation_id=simulation.id,
        generated_by=user.id, report_type="impacto_executivo", format=fmt,
        premises=simulation.assumptions_snapshot,
    ))
    audit(db, organization_id=org_id, user=user, action=f"report.export_{fmt}",
          entity_type="simulation", entity_id=simulation.id, request=request)
    db.commit()


@router.get("/{simulation_id}/export.pdf")
def export_pdf(simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    """★ Relatório executivo para diretoria (PDF profissional com premissas)."""
    simulation = _get_simulation(db, org.id, simulation_id)
    company = db.get(Company, simulation.company_id)
    pdf_bytes = build_simulation_pdf(simulation, company, org.name)
    _register_report(db, org.id, user, simulation, "pdf", request)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="taxbridge-relatorio-{simulation_id}.pdf"'},
    )


@router.get("/{simulation_id}/export.xlsx")
def export_xlsx(simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    simulation = _get_simulation(db, org.id, simulation_id)
    items = db.scalars(
        select(SimulationItem).where(SimulationItem.simulation_id == simulation.id)
        .order_by(SimulationItem.item_name, SimulationItem.year)
    ).all()
    content = build_simulation_xlsx(simulation, items)
    _register_report(db, org.id, user, simulation, "xlsx", request)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="taxbridge-simulacao-{simulation_id}.xlsx"'},
    )


@router.get("/{simulation_id}/export.csv")
def export_csv(simulation_id: uuid.UUID, db: DbSession, org: CurrentOrg, user: CurrentUser, request: Request):
    simulation = _get_simulation(db, org.id, simulation_id)
    items = db.scalars(
        select(SimulationItem).where(SimulationItem.simulation_id == simulation.id)
        .order_by(SimulationItem.item_name, SimulationItem.year)
    ).all()
    content = build_simulation_csv(items)
    _register_report(db, org.id, user, simulation, "csv", request)
    return Response(
        content=content, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="taxbridge-simulacao-{simulation_id}.csv"'},
    )
