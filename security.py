# TaxBridge Brasil

**A ponte entre o sistema tributário atual e o novo modelo CBS/IBS/IS.**

SaaS B2B multi-tenant que ajuda empresas, contadores e consultorias a **calcular, simular,
auditar, parametrizar e acompanhar** o impacto da Reforma Tributária do Consumo
(EC 132/2023 + LC 214/2025) durante toda a transição **2026–2033**.

> ⚠️ **Aviso:** ferramenta de apoio à decisão. Todos os cálculos são estimativas baseadas em
> **premissas configuráveis** (alíquotas de referência, fatores de transição, Imposto Seletivo)
> e **não substituem parecer contábil, jurídico ou fiscal profissional**.

---

## O que o MVP entrega (Fase 1)

| Capacidade | Onde |
|---|---|
| Login/registro com JWT + refresh, RBAC com 7 perfis, LGPD | `/login`, `/registro`, `/usuarios` |
| Cadastro multiempresa (CNPJ, regime, filiais) | `/empresas` |
| Catálogo de produtos (NCM) e serviços (NBS) + importação CSV validada | `/catalogo` |
| Regras tributárias parametrizáveis (CBS/IBS/IS, reduções, exceções) | `/regras` |
| Premissas e calendário de transição 2026–2033 editáveis sem deploy | `/parametros` |
| **Simulador atual × futuro** por item × ano, 3 cenários, memória de cálculo | `/simulacoes` |
| Diagnóstico em 1 clique + dashboard de impacto com gráficos e alertas | `/dashboard` |
| Checklist de adequação (21 tarefas, 7 áreas) + painel de maturidade | `/compliance` |
| Monitor legislativo manual com classificação de impacto | `/legislacao` |
| Relatório executivo em **PDF** + exportação **XLSX/CSV** com premissas | botão "Exportar relatório para diretoria" |
| Logs de auditoria (usuário, IP, entidade, metadados) | `/auditoria` |
| Assistente IA tributário (Claude; modo offline sem chave) | `/assistente` |
| API REST documentada (Swagger) + tokens de API | `http://localhost:8000/docs` |

## Stack

- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS + Recharts + TanStack Query (pt-BR, tema claro/escuro, responsivo)
- **Backend:** FastAPI (Python 3.11) + SQLAlchemy 2 + Alembic + Pydantic v2
- **Banco:** PostgreSQL 16 (multi-tenant por `organization_id`, soft delete, auditoria)
- **Infra:** Docker Compose, Redis + worker RQ (XMLs fiscais — fase 2), ReportLab (PDF), openpyxl (XLSX)

## Rodando localmente (Docker — recomendado)

```bash
git clone <repo>
cd TaxBridge-Brasil
docker compose up --build
```

Aguarde os serviços subirem (a API roda migração + seed automaticamente):

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |

**Logins da organização demo** (seed com empresa, catálogo, regras, checklist e diagnóstico prontos):

```
admin@demo.taxbridge.com.br    / TaxBridge@2026   (Dono da Conta)
contador@demo.taxbridge.com.br / TaxBridge@2026   (Contador)
leitor@demo.taxbridge.com.br   / TaxBridge@2026   (Leitor — somente leitura)
```

Para habilitar o assistente de IA com respostas completas: `ANTHROPIC_API_KEY=sk-... docker compose up`.

## Rodando sem Docker (dev)

```bash
# Backend (requer PostgreSQL e, opcionalmente, Redis locais)
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                # ajuste DATABASE_URL/SECRET_KEY
alembic upgrade head
python -m app.db.seed               # dados de demonstração
uvicorn app.main:app --reload       # http://localhost:8000

# Frontend (em outro terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev                         # http://localhost:3000
```

## Testes

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

37 testes cobrem: matching de regras por especificidade, fatores de cada ano da transição
(ano-teste 2026 compensável, extinção do PIS/Cofins em 2027, rampa 2029–2032, modelo integral
2033), reduções (cesta básica 100%), Imposto Seletivo, créditos, Simples Nacional, cenários,
preço de equilíbrio, split payment, memória de cálculo, e o fluxo completo da API
(auth, RBAC, isolamento multi-tenant, CSV, simulação, exports PDF/XLSX/CSV, auditoria).

## Documentação

| Documento | Conteúdo |
|---|---|
| [docs/00-especificacao-produto.md](docs/00-especificacao-produto.md) | Especificação completa (personas, módulos, requisitos) |
| [docs/01-arquitetura.md](docs/01-arquitetura.md) | Arquitetura, ADRs e estrutura de pastas |
| [docs/02-modelo-de-dados.md](docs/02-modelo-de-dados.md) | DER (21 tabelas) e dicionário do motor |
| [docs/03-api.md](docs/03-api.md) | Rotas da API REST (também em `/docs` via Swagger) |
| [docs/04-regras-de-negocio.md](docs/04-regras-de-negocio.md) | Fórmulas do motor, premissas e RBAC |
| [docs/05-roadmap.md](docs/05-roadmap.md) | Evolução em 7 fases (XML → créditos → IA → ERP → marketplace) |
| [docs/06-precificacao.md](docs/06-precificacao.md) | Planos SaaS e go-to-market |
| [docs/07-seguranca-lgpd.md](docs/07-seguranca-lgpd.md) | Segurança, LGPD e backups |

## Princípios não negociáveis

1. **Nenhuma regra fiscal hardcoded** — alíquotas, fatores de transição e exceções vivem em
   tabelas (`tax_rules`, `tax_transition_years`) e premissas editáveis pelo admin.
2. **Toda simulação grava memória de cálculo** — regra aplicada, fórmulas, premissas e avisos
   por item × ano (rastreabilidade total).
3. **Todo relatório declara as premissas** usadas no cálculo.
4. **Incertezas legislativas = premissas configuráveis**, sinalizadas na UI e nos relatórios.
5. **Isolamento multi-tenant** em todas as queries + auditoria de todas as escritas.
