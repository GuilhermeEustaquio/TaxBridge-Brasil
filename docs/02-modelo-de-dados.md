# Modelo de Dados (DER)

Banco: **PostgreSQL 16** · ORM: **SQLAlchemy 2.0** · Migrações: **Alembic**.

Convenções:
- PK `id UUID`; FKs com índice; **todas** as tabelas de negócio têm `organization_id` (isolamento multi-tenant).
- `created_at`, `updated_at` em todas; `deleted_at` (soft delete) nas entidades de negócio.
- Dinheiro `NUMERIC(14,2)`; alíquotas em **pontos percentuais** `NUMERIC(8,4)` (ex.: `18.0000` = 18%).
- Enums armazenados como `VARCHAR` validados na aplicação (portabilidade + migração simples).

## DER

```mermaid
erDiagram
    organizations ||--o{ companies : possui
    organizations ||--o{ users : possui
    organizations ||--o{ tax_rules : parametriza
    organizations ||--o{ tax_transition_years : parametriza
    organizations ||--o{ legal_updates : acompanha
    organizations ||--o{ audit_logs : registra
    companies ||--o{ branches : possui
    companies ||--o{ products : cataloga
    companies ||--o{ services : cataloga
    companies ||--o{ invoices : recebe
    companies ||--o{ simulations : simula
    companies ||--o{ compliance_tasks : executa
    companies ||--o{ api_keys : integra
    roles ||--o{ users : classifica
    roles ||--o{ role_permissions : tem
    permissions ||--o{ role_permissions : compoe
    invoices ||--o{ invoice_items : contem
    invoice_items ||--o{ tax_credits : gera
    simulations ||--o{ simulation_items : detalha
    simulations ||--o{ reports : origina
    users ||--o{ ai_conversations : conversa
    users ||--o{ compliance_tasks : responsavel

    organizations { uuid id PK; varchar name; varchar slug UK; varchar plan; json assumptions; varchar lgpd_consent_version; timestamptz lgpd_consent_at }
    companies { uuid id PK; uuid organization_id FK; varchar legal_name; varchar trade_name; varchar cnpj UK; varchar tax_regime; varchar segment; varchar uf; varchar municipality; varchar municipality_code }
    branches { uuid id PK; uuid organization_id FK; uuid company_id FK; varchar name; varchar cnpj; varchar uf; varchar municipality }
    users { uuid id PK; uuid organization_id FK; uuid role_id FK; varchar name; varchar email UK; varchar password_hash; bool is_active; bool totp_enabled; timestamptz last_login_at }
    roles { uuid id PK; varchar slug UK; varchar name; int level }
    permissions { uuid id PK; varchar code UK; varchar description }
    role_permissions { uuid role_id FK; uuid permission_id FK }
    products { uuid id PK; uuid organization_id FK; uuid company_id FK; varchar sku; varchar name; varchar ncm; varchar cest; varchar cfop; varchar cst_icms; varchar csosn; varchar origin_uf; varchar dest_uf; numeric unit_price; numeric unit_cost; numeric monthly_volume; bool is_selective }
    services { uuid id PK; uuid organization_id FK; uuid company_id FK; varchar code; varchar name; varchar nbs; varchar lc116_item; varchar municipality; numeric unit_price; numeric unit_cost; numeric monthly_volume }
    tax_rules { uuid id PK; uuid organization_id FK; uuid company_id FK "null=org inteira"; varchar name; varchar item_kind "product|service|any"; varchar ncm_pattern; varchar nbs_pattern; varchar cfop; varchar uf_origin; varchar uf_dest; varchar tax_regime; int priority; numeric icms_rate; numeric iss_rate; numeric pis_rate; numeric cofins_rate; numeric ipi_rate; numeric cbs_rate "null=referencia org"; numeric ibs_rate "null=referencia org"; numeric is_rate; numeric cbs_reduction_pct; numeric ibs_reduction_pct; bool credit_allowed; varchar legal_basis; date valid_from; date valid_to; bool is_active }
    tax_transition_years { uuid id PK; uuid organization_id FK; int year; numeric cbs_factor; numeric ibs_factor; numeric cbs_rate_override; numeric ibs_rate_override; numeric cbs_adjustment_pp; numeric legacy_icms_iss_factor; numeric pis_cofins_factor; bool selective_active; bool test_year_compensable; text notes }
    invoices { uuid id PK; uuid organization_id FK; uuid company_id FK; varchar doc_type "nfe|nfce|nfse|cte"; varchar access_key UK; varchar number; varchar series; varchar direction "in|out"; varchar partner_name; varchar partner_cnpj; varchar uf_origin; varchar uf_dest; date issued_at; numeric total_amount; varchar status; varchar xml_path }
    invoice_items { uuid id PK; uuid invoice_id FK; int line; varchar ncm; varchar cfop; varchar cst; varchar description; numeric quantity; numeric unit_price; numeric total; numeric icms_amount; numeric pis_amount; numeric cofins_amount; numeric ipi_amount; numeric iss_amount }
    simulations { uuid id PK; uuid organization_id FK; uuid company_id FK; uuid created_by FK; varchar name; varchar scenario "conservador|provavel|agressivo"; int year_start; int year_end; varchar status; json assumptions_snapshot; json summary "agregado por ano"; varchar origin "manual|diagnostico" }
    simulation_items { uuid id PK; uuid simulation_id FK; varchar item_kind; uuid item_id; varchar item_name; uuid tax_rule_id FK; int year; numeric annual_revenue; numeric current_tax_total; numeric current_credits; numeric current_net_burden; numeric future_cbs; numeric future_ibs; numeric future_is; numeric future_legacy; numeric future_credits; numeric future_net_burden; numeric delta_net; numeric margin_current_pct; numeric margin_future_pct; numeric breakeven_price; numeric cash_flow_impact; json calc_memory }
    tax_credits { uuid id PK; uuid organization_id FK; uuid company_id FK; uuid invoice_item_id FK; varchar regime "atual|cbs_ibs"; varchar credit_type; varchar status "apurado|potencial|perdido|em_risco"; numeric amount; json evidence }
    compliance_tasks { uuid id PK; uuid organization_id FK; uuid company_id FK; uuid assignee_id FK; varchar area "fiscal|contabil|financeiro|juridico|ti|vendas|compras"; varchar title; text description; varchar status "pendente|em_andamento|concluido|vencido|critico"; varchar priority; date due_date; varchar evidence_url; uuid legal_update_id FK }
    legal_updates { uuid id PK; uuid organization_id FK; varchar norm_type "lei|lc|decreto|nota_tecnica|portaria|outro"; varchar reference; varchar title; text summary; varchar impact "baixo|medio|alto|critico"; varchar source_url; date published_at }
    reports { uuid id PK; uuid organization_id FK; uuid company_id FK; uuid simulation_id FK; uuid generated_by FK; varchar report_type; varchar format "pdf|xlsx|csv"; varchar file_path; json premises }
    ai_conversations { uuid id PK; uuid organization_id FK; uuid user_id FK; varchar title; json messages; varchar model; timestamptz last_message_at }
    audit_logs { uuid id PK; uuid organization_id FK; uuid user_id FK; varchar action; varchar entity_type; varchar entity_id; json metadata; varchar ip_address; varchar user_agent; timestamptz created_at }
    api_keys { uuid id PK; uuid organization_id FK; uuid company_id FK; varchar name; varchar prefix; varchar key_hash; int rate_limit_per_minute; timestamptz last_used_at; timestamptz revoked_at }
```

## Tabelas-chave do motor tributário

### `tax_rules` — regras parametrizáveis
Casamento item→regra por **especificidade** (soma de pesos dos campos preenchidos que casam) e
`priority` como desempate. Campos `NULL` = "qualquer". `ncm_pattern`/`nbs_pattern` aceitam
prefixo (`2202*`). `cbs_rate`/`ibs_rate` nulos ⇒ usa alíquota de referência das premissas da
organização, permitindo regra que só define **redução** (ex.: cesta básica 100%).

### `tax_transition_years` — calendário da transição (seed editável)

| Ano | CBS | IBS | PIS/Cofins | ICMS/ISS | IS | Observação (premissa configurável) |
|---|---|---|---|---|---|---|
| 2026 | 0,9% (override) | 0,1% (override) | 100% | 100% | não | Ano-teste; compensável c/ PIS/Cofins |
| 2027 | 100% ref − 0,1pp | 0,1% (override) | **0%** | 100% | sim | CBS plena; IPI zerado (exceto ZFM) |
| 2028 | 100% ref − 0,1pp | 0,1% (override) | 0% | 100% | sim | |
| 2029 | 100% ref | 10% ref | 0% | 90% | sim | Início da redução ICMS/ISS |
| 2030 | 100% ref | 20% ref | 0% | 80% | sim | |
| 2031 | 100% ref | 30% ref | 0% | 70% | sim | |
| 2032 | 100% ref | 40% ref | 0% | 60% | sim | |
| 2033 | 100% ref | 100% ref | 0% | **0%** | sim | Modelo integral |

### `organizations.assumptions` — premissas (JSON editável na UI)
`cbs_reference_rate` (8,8), `ibs_reference_rate` (17,7), `input_cost_creditable_ratio` (0,60),
`current_credit_efficiency` (0,70), `future_credit_efficiency` (0,95), `split_payment_enabled`,
`split_payment_float_days` (40), `cost_of_capital_annual` (0,12), `simples_effective_rate` (8,0),
`icms_inside_price` (true), `scenario_adjustments` ({conservador: +1,5pp; provavel: 0; agressivo: −1,0pp}).

> Valores default citados são **estimativas de mercado/Ministério da Fazenda** — não são
> alíquotas oficiais definitivas; por isso vivem em dados, não em código.

## Índices principais
- `users(email)`, `organizations(slug)`, `companies(cnpj)`, `invoices(access_key)` — únicos.
- `(organization_id)` em todas; compostos: `products(organization_id, company_id, sku)` único,
  `simulation_items(simulation_id, year)`, `audit_logs(organization_id, created_at)`,
  `tax_rules(organization_id, is_active)`, `tax_transition_years(organization_id, year)` único.
