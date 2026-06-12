# Arquitetura do Sistema

## 1. Visão geral

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              USUÁRIOS                                    │
│   Diretoria · Contadores · Fiscal · Financeiro · Consultorias · ERPs     │
└─────────────────────────────┬────────────────────────────────────────────┘
                              │ HTTPS
              ┌───────────────▼───────────────┐
              │   FRONTEND — Next.js 14 (TS)   │  Tailwind · Recharts ·
              │   App Router · pt-BR · dark    │  TanStack Query · JWT client
              └───────────────┬───────────────┘
                              │ REST /api/v1 (JSON) + Bearer JWT / X-API-Key
              ┌───────────────▼───────────────────────────────────────────┐
              │              BACKEND — FastAPI (Python 3.11)              │
              │                                                           │
              │  api/v1 (routers) ─ auth · companies · users · catalog    │
              │     · tax-rules · transition · simulations · compliance   │
              │     · legal · dashboard · reports · audit · api-keys · ai │
              │                                                           │
              │  services ─ tax_engine (motor) · simulation · csv_import  │
              │     · pdf_report · xlsx_export · dashboard · templates    │
              │                                                           │
              │  core ─ config · security (JWT/bcrypt) · deps (tenancy,   │
              │     RBAC) · audit · rate_limit                            │
              └────────┬──────────────────┬───────────────┬───────────────┘
                       │ SQLAlchemy 2.0   │ Redis (cache/ │ filesystem ./storage
                       │ + Alembic        │ filas RQ)     │ (S3-ready, fase 2)
              ┌────────▼────────┐  ┌──────▼──────┐  ┌─────▼─────────────┐
              │  PostgreSQL 16  │  │   Redis 7   │  │ WORKER (RQ)       │
              │  multi-tenant   │  │             │  │ XMLs fiscais (F2) │
              └─────────────────┘  └─────────────┘  └───────────────────┘
```

## 2. Decisões de arquitetura (ADRs resumidos)

| # | Decisão | Justificativa |
|---|---|---|
| 1 | **FastAPI** (vs NestJS) | Cálculo fiscal intensivo em `Decimal`, ecossistema Python p/ dados/IA, Pydantic v2 = validação forte, OpenAPI nativo |
| 2 | **Multi-tenant shared-schema** com `organization_id` em toda tabela + filtro obrigatório nas queries | Custo/escala do MVP; isolamento lógico auditável; migração p/ schema-per-tenant possível |
| 3 | **Motor tributário orientado a dados** | Regras (`tax_rules`), fatores por ano (`tax_transition_years`) e premissas (`organizations.assumptions`) são linhas de banco editáveis por admin — exigência central do produto |
| 4 | **Memória de cálculo em JSON** por item/ano (`simulation_items.calc_memory`) | Rastreabilidade e auditoria de cada número exibido |
| 5 | **JWT access (30min) + refresh (7d) stateless** | Simplicidade no MVP; logout client-side + auditoria; blocklist Redis na fase 2 |
| 6 | **Soft delete (`deleted_at`)** em entidades de negócio | LGPD/retenção + trilha de auditoria |
| 7 | **Decimal end-to-end** (`Numeric` no banco, `decimal.Decimal` no motor) | Nunca usar float em dinheiro/alíquota |
| 8 | **Migração inicial = metadata do SQLAlchemy via Alembic**; próximas via `--autogenerate` | Versionamento real desde o dia 1 sem duplicar 21 tabelas à mão |
| 9 | **Storage local `./storage`** com interface própria | MVP simples; troca por S3 = 1 classe (fase 2) |
| 10 | **Rate limit em memória por IP nos endpoints de auth** | Proteção básica no MVP; Redis sliding-window na fase 2 |

## 3. Estrutura de pastas

```
TaxBridge-Brasil/
├── docker-compose.yml
├── README.md
├── docs/                          # especificação, arquitetura, DER, API, regras, roadmap, preço
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── app/
│   │   ├── main.py                # app factory, CORS, middlewares, health
│   │   ├── core/
│   │   │   ├── config.py          # Settings (pydantic-settings, .env)
│   │   │   ├── security.py        # bcrypt, JWT encode/decode
│   │   │   ├── deps.py            # get_db, get_current_user, require_roles (RBAC + tenancy)
│   │   │   ├── audit.py           # helper de log de auditoria
│   │   │   └── rate_limit.py      # limitador simples por IP
│   │   ├── db/
│   │   │   ├── base.py            # Base, TimestampMixin, SoftDeleteMixin, TenantMixin
│   │   │   ├── session.py         # engine + SessionLocal
│   │   │   └── seed.py            # seeds idempotentes (demo completa)
│   │   ├── models/                # 21 tabelas (ver docs/02)
│   │   ├── schemas/               # Pydantic v2 (request/response)
│   │   ├── api/v1/                # routers REST (ver docs/03)
│   │   ├── services/
│   │   │   ├── tax_engine.py      # ★ motor tributário (puro, testável)
│   │   │   ├── simulation_service.py
│   │   │   ├── csv_import.py
│   │   │   ├── pdf_report.py      # ReportLab
│   │   │   ├── xlsx_export.py     # openpyxl
│   │   │   ├── dashboard_service.py
│   │   │   ├── checklist_template.py
│   │   │   └── ai_assistant.py    # integração Anthropic (opcional via env)
│   │   └── workers/
│   │       └── worker.py          # RQ worker (fila fiscal-documents, fase 2)
│   └── tests/
│       ├── conftest.py            # app + SQLite + fixtures
│       ├── test_tax_engine.py     # regras de cálculo e transição
│       └── test_api.py            # fluxo MVP completo via TestClient
└── frontend/
    ├── Dockerfile
    ├── package.json · tsconfig.json · tailwind.config.ts · next.config.mjs
    └── src/
        ├── app/
        │   ├── (auth)/login · (auth)/registro
        │   └── (app)/dashboard · empresas · catalogo · regras · parametros
        │       · simulacoes · simulacoes/[id] · compliance · legislacao
        │       · relatorios · auditoria · usuarios
        ├── components/ui/         # Button, Card, Badge, Table, Modal, Tabs, ...
        ├── components/charts/     # wrappers Recharts
        ├── components/layout/     # Sidebar, Topbar, ThemeToggle
        └── lib/                   # api client (fetch+refresh), auth context, formatters
```

## 4. Fluxos críticos

### 4.1 Simulação (núcleo do produto)
1. `POST /simulations` (empresa, anos, cenário, premissas-override opcionais).
2. `simulation_service` carrega: itens do catálogo, `tax_rules` vigentes (match por
   especificidade), `tax_transition_years` e `assumptions` da organização.
3. `tax_engine` calcula por item × ano: débitos atual/futuro, créditos, carga líquida, margens,
   preço de equilíbrio, impacto de caixa — tudo `Decimal`, com memória de cálculo.
4. Persiste `simulations` (resumo por ano + premissas snapshot) e `simulation_items`.
5. Auditoria registrada; dashboard e relatórios leem o resultado consolidado.

### 4.2 Autenticação e tenancy
`Authorization: Bearer <jwt>` → `get_current_user` resolve usuário+organização → toda query
filtra `organization_id` → `require_roles(...)` valida RBAC → mutações chamam `audit()` com IP,
usuário, entidade, payload resumido.

### 4.3 Importação CSV
Upload multipart → parsing com validação linha a linha (NCM 8 dígitos, preço decimal, UF
válida...) → upsert por SKU → resposta com `criados/atualizados/erros[linha, motivo]` → auditoria.

## 5. Escalabilidade — caminho traçado

| Gargalo futuro | Mitigação preparada |
|---|---|
| Simulações grandes | Mover p/ fila RQ (Redis já no compose, worker já existe) |
| Leitura dashboard | Cache Redis por org + agregados pré-calculados em `simulations.summary` |
| Multi-tenant ruidoso | Índices `(organization_id, ...)` em todas as tabelas; rate limit por API key |
| Storage | Interface de storage local → S3/MinIO |
| Picos de auth | Rate limiter in-memory → Redis |
