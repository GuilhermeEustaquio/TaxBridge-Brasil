from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models import Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Em produção o schema é gerido pelo Alembic; create_all é idempotente e
    # garante DX simples em dev/teste (AUTO_CREATE_TABLES=false para desligar).
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.db.seed import ensure_roles_and_permissions

        ensure_roles_and_permissions(db)
        db.commit()
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="TaxBridge Brasil API",
        version="0.1.0",
        description=(
            "API do TaxBridge Brasil — simulação e gestão da transição para CBS/IBS/IS "
            "(Reforma Tributária do Consumo). Valores calculados são estimativas baseadas "
            "em premissas configuráveis e não substituem parecer profissional."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Saúde"])
    def health() -> dict:
        return {"status": "ok", "service": "taxbridge-api", "env": settings.ENV}

    return app


app = create_app()
