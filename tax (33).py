from fastapi import APIRouter

from app.api.v1 import auth, catalog, companies, compliance, misc, organizations, simulations, tax_rules, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(companies.router)
api_router.include_router(users.router)
api_router.include_router(catalog.router)
api_router.include_router(tax_rules.router)
api_router.include_router(simulations.router)
api_router.include_router(compliance.router)
api_router.include_router(misc.legal_router)
api_router.include_router(misc.dashboard_router)
api_router.include_router(misc.audit_router)
api_router.include_router(misc.apikeys_router)
api_router.include_router(misc.reports_router)
api_router.include_router(misc.ai_router)
