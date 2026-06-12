"""Seeds idempotentes: perfis/permissões globais + organização de demonstração completa.

Uso: python -m app.db.seed
"""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Branch,
    Company,
    LegalUpdate,
    Organization,
    Permission,
    Product,
    Role,
    RolePermission,
    Service,
    TaxRule,
    TaxTransitionYear,
    User,
)
from app.schemas.org import Assumptions
from app.services.tax_defaults import build_transition_rows

ROLES = [
    ("admin_global", "Admin Global", 100),
    ("dono_conta", "Dono da Conta", 90),
    ("contador", "Contador", 70),
    ("fiscal", "Fiscal", 60),
    ("financeiro", "Financeiro", 50),
    ("consultor", "Consultor", 40),
    ("leitor", "Leitor", 10),
]

# code -> (descricao, nivel minimo do perfil que recebe a permissao)
PERMISSIONS: dict[str, tuple[str, int]] = {
    "dashboard.read": ("Visualizar dashboard", 10),
    "companies.read": ("Visualizar empresas", 10),
    "companies.write": ("Gerenciar empresas e filiais", 60),
    "companies.delete": ("Excluir empresas", 90),
    "catalog.read": ("Visualizar produtos e serviços", 10),
    "catalog.write": ("Gerenciar produtos e serviços", 60),
    "tax_rules.read": ("Visualizar regras tributárias", 10),
    "tax_rules.write": ("Gerenciar regras tributárias", 60),
    "transition.write": ("Editar anos de transição e premissas", 70),
    "simulations.read": ("Visualizar simulações", 10),
    "simulations.write": ("Executar simulações", 40),
    "compliance.read": ("Visualizar checklist", 10),
    "compliance.write": ("Gerenciar checklist", 40),
    "legal.write": ("Gerenciar monitor legislativo", 60),
    "reports.read": ("Exportar relatórios", 10),
    "audit.read": ("Consultar auditoria", 70),
    "users.manage": ("Gerenciar usuários", 90),
    "api_keys.manage": ("Gerenciar tokens de API", 90),
    "ai.chat": ("Usar assistente de IA", 40),
}


def ensure_roles_and_permissions(db: Session) -> None:
    roles_by_slug: dict[str, Role] = {}
    for slug, name, level in ROLES:
        role = db.scalar(select(Role).where(Role.slug == slug))
        if role is None:
            role = Role(slug=slug, name=name, level=level)
            db.add(role)
            db.flush()
        roles_by_slug[slug] = role

    for code, (description, min_level) in PERMISSIONS.items():
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, description=description)
            db.add(permission)
            db.flush()
        for role in roles_by_slug.values():
            if role.level >= min_level:
                link = db.get(RolePermission, (role.id, permission.id))
                if link is None:
                    db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    db.flush()


def seed_transition_years(db: Session, organization_id) -> None:
    existing = db.scalar(
        select(TaxTransitionYear).where(TaxTransitionYear.organization_id == organization_id).limit(1)
    )
    if existing:
        return
    for row in build_transition_rows(organization_id):
        db.add(TaxTransitionYear(**row))
    db.flush()


DEMO_RULES: list[dict] = [
    dict(name="Cesta básica nacional — alíquota zero CBS/IBS", item_kind="product", ncm_pattern="1006*",
         priority=100, icms_rate=Decimal("7"), pis_rate=Decimal("0"), cofins_rate=Decimal("0"),
         cbs_reduction_pct=Decimal("100"), ibs_reduction_pct=Decimal("100"),
         legal_basis="LC 214/2025, Anexo I (Cesta Básica Nacional)"),
    dict(name="Bebidas açucaradas — Imposto Seletivo (alíquota premissa)", item_kind="product",
         ncm_pattern="2202*", priority=90, icms_rate=Decimal("18"), pis_rate=Decimal("1.65"),
         cofins_rate=Decimal("7.6"), ipi_rate=Decimal("4"), is_rate=Decimal("10"),
         legal_basis="EC 132/2023, art. 153, VIII; alíquota do IS pendente de lei específica (premissa configurável)"),
    dict(name="Medicamentos — redução de 60%", item_kind="product", ncm_pattern="3004*", priority=90,
         icms_rate=Decimal("18"), pis_rate=Decimal("1.65"), cofins_rate=Decimal("7.6"),
         cbs_reduction_pct=Decimal("60"), ibs_reduction_pct=Decimal("60"),
         legal_basis="LC 214/2025 (medicamentos — redução 60%)"),
    dict(name="Chocolates e derivados de cacau", item_kind="product", ncm_pattern="1806*", priority=50,
         icms_rate=Decimal("18"), pis_rate=Decimal("1.65"), cofins_rate=Decimal("7.6"), ipi_rate=Decimal("5"),
         legal_basis="TIPI vigente; regra geral CBS/IBS"),
    dict(name="Produtos — regra geral (regime regular)", item_kind="product", priority=0,
         icms_rate=Decimal("18"), pis_rate=Decimal("1.65"), cofins_rate=Decimal("7.6"),
         legal_basis="Regra geral; alíquotas de referência CBS/IBS das premissas"),
    dict(name="Software e TI — ISS municipal reduzido", item_kind="service", nbs_pattern="1.14*", priority=50,
         iss_rate=Decimal("2.9"), pis_rate=Decimal("1.65"), cofins_rate=Decimal("7.6"),
         legal_basis="LC 116/2003, item 1; alíquota ISS municipal de São Paulo"),
    dict(name="Serviços profissionais — regra geral (regime regular)", item_kind="service", priority=0,
         iss_rate=Decimal("5"), pis_rate=Decimal("1.65"), cofins_rate=Decimal("7.6"),
         legal_basis="LC 116/2003; regra geral CBS/IBS"),
    dict(name="Simples Nacional — permanência no regime", item_kind="any", tax_regime="simples", priority=10,
         legal_basis="LC 123/2006; LC 214/2025 (manutenção do Simples; avaliar migração)"),
]

DEMO_PRODUCTS: list[dict] = [
    dict(sku="ARZ-5KG", name="Arroz branco tipo 1 — 5kg", ncm="10063021", cfop="5102", cst_icms="020",
         origin_uf="SP", dest_uf="SP", unit_price=Decimal("25.90"), unit_cost=Decimal("18.50"),
         monthly_volume=Decimal("4200")),
    dict(sku="REF-2L", name="Refrigerante cola — 2L", ncm="22021000", cfop="5102", cst_icms="000",
         origin_uf="SP", dest_uf="RJ", unit_price=Decimal("9.50"), unit_cost=Decimal("4.20"),
         monthly_volume=Decimal("9800"), is_selective=True),
    dict(sku="MED-DIP500", name="Analgésico dipirona 500mg — 20 comp.", ncm="30049099", cfop="5102",
         cst_icms="000", origin_uf="SP", dest_uf="SP", unit_price=Decimal("12.90"), unit_cost=Decimal("6.10"),
         monthly_volume=Decimal("2600")),
    dict(sku="NTB-PRO14", name="Notebook profissional 14\"", ncm="84713012", cfop="5102", cst_icms="000",
         origin_uf="SP", dest_uf="SP", unit_price=Decimal("4890.00"), unit_cost=Decimal("3550.00"),
         monthly_volume=Decimal("85")),
    dict(sku="CIM-50KG", name="Cimento CP-II — 50kg", ncm="25232910", cfop="5102", cst_icms="000",
         origin_uf="SP", dest_uf="MG", unit_price=Decimal("38.90"), unit_cost=Decimal("27.40"),
         monthly_volume=Decimal("3100")),
    dict(sku="CHO-BAR90", name="Chocolate ao leite — barra 90g", ncm="18063220", cfop="5102", cst_icms="000",
         origin_uf="SP", dest_uf="SP", unit_price=Decimal("8.90"), unit_cost=Decimal("4.30"),
         monthly_volume=Decimal("5400")),
    dict(sku="AGU-MIN500", name="Água mineral sem gás — 500ml", ncm="22011000", cfop="5102", cst_icms="000",
         origin_uf="SP", dest_uf="SP", unit_price=Decimal("2.50"), unit_cost=Decimal("0.95"),
         monthly_volume=Decimal("15200")),
]

DEMO_SERVICES: list[dict] = [
    dict(code="SRV-CONS", name="Consultoria tributária mensal", nbs="1.1501", lc116_item="17.01",
         municipality="São Paulo", unit_price=Decimal("4500.00"), unit_cost=Decimal("1800.00"),
         monthly_volume=Decimal("14")),
    dict(code="SRV-TI", name="Desenvolvimento de software sob demanda", nbs="1.1403", lc116_item="1.01",
         municipality="São Paulo", unit_price=Decimal("280.00"), unit_cost=Decimal("130.00"),
         monthly_volume=Decimal("640")),
    dict(code="SRV-MANUT", name="Manutenção de equipamentos industriais", nbs="1.2101", lc116_item="14.01",
         municipality="São Paulo", unit_price=Decimal("950.00"), unit_cost=Decimal("420.00"),
         monthly_volume=Decimal("75")),
]

DEMO_LEGAL_UPDATES: list[dict] = [
    dict(norm_type="lc", reference="EC 132/2023", title="Emenda Constitucional da Reforma Tributária do Consumo",
         summary="Institui CBS, IBS e Imposto Seletivo; define calendário de transição 2026–2033.",
         impact="critico", source_url="https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm",
         published_at=date(2023, 12, 20)),
    dict(norm_type="lc", reference="LC 214/2025", title="Lei Complementar de regulamentação da Reforma (CBS/IBS/IS)",
         summary="Regulamenta fatos geradores, créditos, cesta básica, reduções, regimes específicos e split payment.",
         impact="critico", source_url="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
         published_at=date(2025, 1, 16)),
    dict(norm_type="nota_tecnica", reference="NT NF-e 2025.002", title="Novos campos de CBS/IBS/IS nos documentos fiscais",
         summary="Leiautes de NF-e/NFC-e passam a contemplar grupos de tributação da reforma para o ano-teste de 2026.",
         impact="alto", source_url="https://www.nfe.fazenda.gov.br/", published_at=date(2025, 6, 30)),
    dict(norm_type="outro", reference="Comitê Gestor do IBS", title="Regulamentação operacional do split payment",
         summary="Definições operacionais do recolhimento na liquidação financeira — acompanhar publicações.",
         impact="medio", source_url=None, published_at=None),
]


def seed_demo(db: Session) -> None:
    from app.core.security import hash_password
    from app.services.checklist_template import CHECKLIST_TEMPLATE
    from app.services.simulation_service import run_simulation

    if db.scalar(select(Organization).where(Organization.slug == "demo")):
        print("Seed demo já aplicado — nada a fazer.")
        return

    org = Organization(
        name="Demo Tributária",
        slug="demo",
        plan="trial",
        assumptions=Assumptions().model_dump(mode="json"),
        lgpd_consent_version="2026-01",
        lgpd_consent_at=datetime.now(timezone.utc),
    )
    db.add(org)
    db.flush()
    seed_transition_years(db, org.id)

    roles = {slug: db.scalar(select(Role).where(Role.slug == slug)) for slug, _, _ in ROLES}
    owner = User(organization_id=org.id, role_id=roles["dono_conta"].id, name="Ana Diretora",
                 email="admin@demo.taxbridge.com.br", password_hash=hash_password("TaxBridge@2026"))
    accountant = User(organization_id=org.id, role_id=roles["contador"].id, name="Carlos Contador",
                      email="contador@demo.taxbridge.com.br", password_hash=hash_password("TaxBridge@2026"))
    reader = User(organization_id=org.id, role_id=roles["leitor"].id, name="Lia Leitora",
                  email="leitor@demo.taxbridge.com.br", password_hash=hash_password("TaxBridge@2026"))
    db.add_all([owner, accountant, reader])
    db.flush()

    aurora = Company(organization_id=org.id, legal_name="Aurora Alimentos e Bebidas Ltda",
                     trade_name="Aurora", cnpj="12.345.678/0001-95", tax_regime="real",
                     segment="Indústria e distribuição de alimentos", uf="SP", municipality="São Paulo",
                     municipality_code="3550308")
    bemservir = Company(organization_id=org.id, legal_name="Bem Servir Refeições ME",
                        trade_name="Bem Servir", cnpj="98.765.432/0001-10", tax_regime="simples",
                        segment="Alimentação fora do lar", uf="MG", municipality="Belo Horizonte",
                        municipality_code="3106200")
    db.add_all([aurora, bemservir])
    db.flush()
    db.add(Branch(organization_id=org.id, company_id=aurora.id, name="Filial Rio de Janeiro",
                  cnpj="12.345.678/0002-76", uf="RJ", municipality="Rio de Janeiro"))

    for rule in DEMO_RULES:
        db.add(TaxRule(organization_id=org.id, **rule))
    for product in DEMO_PRODUCTS:
        db.add(Product(organization_id=org.id, company_id=aurora.id, **product))
    for service in DEMO_SERVICES:
        db.add(Service(organization_id=org.id, company_id=aurora.id, **service))
    db.add(Product(organization_id=org.id, company_id=bemservir.id, sku="MARM-G",
                   name="Marmitex grande", ncm="21069090", cfop="5102", origin_uf="MG", dest_uf="MG",
                   unit_price=Decimal("22.00"), unit_cost=Decimal("11.00"), monthly_volume=Decimal("2600")))
    for update in DEMO_LEGAL_UPDATES:
        db.add(LegalUpdate(organization_id=org.id, **update))

    from datetime import timedelta
    base_due = date.today() + timedelta(days=45)
    for index, task in enumerate(CHECKLIST_TEMPLATE):
        from app.models import ComplianceTask
        db.add(ComplianceTask(
            organization_id=org.id, company_id=aurora.id, area=task["area"], title=task["title"],
            description=task["description"], priority=task["priority"],
            status="em_andamento" if index % 5 == 0 else ("concluido" if index % 7 == 0 else "pendente"),
            due_date=base_due + timedelta(days=7 * (index // 4)),
            assignee_id=accountant.id if task["area"] in {"fiscal", "contabil"} else None,
        ))
    db.flush()

    run_simulation(
        db, organization_id=org.id, company=aurora, user=owner,
        name="Diagnóstico inicial — Aurora Alimentos e Bebidas",
        scenario="provavel", year_start=2026, year_end=2033, origin="diagnostico",
    )

    db.commit()
    print("Seed demo aplicado com sucesso.")
    print("  Login: admin@demo.taxbridge.com.br / TaxBridge@2026 (Dono da Conta)")
    print("         contador@demo.taxbridge.com.br / TaxBridge@2026 (Contador)")
    print("         leitor@demo.taxbridge.com.br / TaxBridge@2026 (Leitor)")


def main() -> None:
    from app.db.session import SessionLocal, engine
    from app.models import Base

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_roles_and_permissions(db)
        db.commit()
        seed_demo(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
