# TaxBridge Brasil — Especificação Completa do Produto

> **Versão:** 1.0 · **Status:** MVP em desenvolvimento
>
> **Aviso importante:** o TaxBridge Brasil é uma ferramenta de **apoio à decisão**. Todos os
> cálculos são **estimativas baseadas em premissas configuráveis** (EC 132/2023, LC 214/2025 e
> regulamentação em evolução) e **não substituem parecer jurídico, contábil ou fiscal
> profissional**. Alíquotas de referência de CBS/IBS ainda dependem de atos normativos futuros.

---

## 1. Visão do produto

### 1.1 O problema

A Reforma Tributária do Consumo (EC 132/2023, regulamentada pela LC 214/2025) substitui
gradualmente **PIS, Cofins, ICMS, ISS e parte do IPI** por três novos tributos:

| Novo tributo | Substitui | Competência |
|---|---|---|
| **CBS** — Contribuição sobre Bens e Serviços | PIS + Cofins | Federal |
| **IBS** — Imposto sobre Bens e Serviços | ICMS + ISS | Estados + Municípios |
| **IS** — Imposto Seletivo | (novo, extrafiscal) | Federal |

Entre **2026 e 2033** as empresas operarão com **dois sistemas simultâneos**: regras antigas em
extinção e regras novas em implantação, com mudanças em documentos fiscais, créditos, alíquotas
por destino, *split payment*, formação de preço, margem, fluxo de caixa e obrigações acessórias.

Não existe hoje, para o mercado médio, uma ferramenta que responda de forma simples:
**"quanto a reforma vai impactar a minha empresa, ano a ano, e o que eu preciso fazer?"**

### 1.2 A solução

SaaS B2B multi-tenant que permite **calcular, simular, auditar, parametrizar e acompanhar** os
impactos fiscais, financeiros e operacionais da transição, por empresa, filial, produto, serviço,
UF, município e ano (2026–2033).

### 1.3 Personas

| Persona | Dor principal | O que o produto entrega |
|---|---|---|
| **CFO / Diretoria** | "Qual o impacto em margem, preço e caixa?" | Dashboard executivo, relatório PDF para diretoria, cenários |
| **Contador / Escritório contábil** | Atender dezenas de clientes na transição | Multiempresa, diagnóstico em 1 clique, relatórios white-label (fase 7) |
| **Analista fiscal** | Parametrizar NCM/CFOP/CST no novo modelo | Motor tributário parametrizável, alertas de divergência |
| **Consultoria tributária** | Escalar estudos de impacto | Simulador de cenários, memória de cálculo auditável |
| **TI / ERP** | Integrar dados fiscais | API REST documentada, tokens por empresa, webhooks (fase 5) |

### 1.4 Proposta de valor (one-liner)

> **"A ponte entre o sistema tributário atual e o novo: saiba hoje quanto CBS, IBS e Imposto
> Seletivo vão custar para a sua empresa em cada ano da transição — e o que fazer a respeito."**

---

## 2. Módulos funcionais

### 2.1 Dashboard geral (MVP)
- Visão consolidada por empresa, período e regime tributário.
- Cards de impacto: Δ carga anual estimada, Δ margem média, créditos potenciais, alertas ativos.
- Gráfico **carga atual × carga futura** ano a ano (2026–2033) com linha do tempo da transição.
- Top produtos/serviços mais impactados.
- Painel de maturidade do checklist de adequação.
- Botões de ação: **"Gerar diagnóstico da empresa"**, **"Simular Reforma Tributária"**,
  **"Exportar relatório para diretoria"**.

### 2.2 Cadastro multiempresa (MVP)
- Organização (tenant) → empresas (CNPJ, regime, segmento, UF/município) → filiais.
- Perfis: `admin_global`, `dono_conta`, `contador`, `fiscal`, `financeiro`, `consultor`, `leitor`.
- Permissões por perfil; logs de auditoria em todas as ações de escrita.

### 2.3 Motor tributário da Reforma (MVP)
- Catálogo de **produtos** (NCM, CST, CSOSN, CFOP, UF origem/destino, preço, custo, volume) e
  **serviços** (NBS, item LC 116, município, preço, custo, volume).
- **Regras tributárias parametrizáveis** (`tax_rules`): casam itens por NCM/NBS/CFOP/UF/tipo e
  definem alíquotas atuais (ICMS, ISS, PIS, Cofins, IPI) e futuras (CBS, IBS, IS, % de redução
  de base — ex.: cesta básica 100%, saúde/educação 60%).
- **Anos de transição parametrizáveis** (`tax_transition_years`): fatores de CBS/IBS/legado por
  ano, editáveis pelo administrador — *nenhuma regra fiscal hardcoded*.
- Premissas da organização configuráveis: alíquotas de referência, % de insumos creditáveis,
  eficiência de créditos, split payment, custo de capital, ajustes por cenário.
- Tratamento de exceções: reduções de base, Imposto Seletivo, Simples Nacional (alerta de
  permanência/migração), regimes específicos via regras dedicadas.

### 2.4 Simulador de impacto financeiro (MVP)
- Compara **cenário atual × cenário futuro** por item e por ano (2026–2033).
- Calcula: débitos, créditos, carga líquida, margem bruta/líquida, **preço de equilíbrio**
  (para manter margem), impacto de caixa do split payment.
- Cenários: **conservador / provável / agressivo** (ajustes de alíquota configuráveis).
- Toda simulação grava **memória de cálculo** por item/ano (regra aplicada, alíquotas, fórmulas,
  premissas) — rastreabilidade total.
- Exporta PDF, XLSX e CSV.

### 2.5 Importador fiscal (Fase 2)
- Upload de XML de NF-e, NFC-e, NFS-e e CT-e (individual e em lote, processado por worker).
- Extração automática de campos, validação, identificação de inconsistências, histórico,
  filtros por período/cliente/fornecedor/CFOP/NCM/município/UF.
- *Tabelas `invoices`/`invoice_items` já existem no MVP para compatibilidade futura.*

### 2.6 Análise de créditos (Fase 3)
- Créditos atuais × créditos estimados no modelo CBS/IBS; créditos perdidos, potenciais e em
  risco; trilha de auditoria por documento; relatório de aproveitamento.
- *No MVP, créditos são estimados por premissas (% de insumos creditáveis) na simulação; a
  tabela `tax_credits` já existe.*

### 2.7 Compliance e checklist (MVP)
- Checklist de adequação por área: fiscal, contábil, financeiro, jurídico, TI, vendas, compras.
- Status: pendente, em andamento, concluído, vencido, crítico. Responsáveis, prazos, evidências.
- Template padrão aplicável em 1 clique; painel de maturidade (% por área).

### 2.8 Monitor legislativo (MVP manual / Fase 6 automático)
- Cadastro de normas (lei, LC, decreto, NT, portaria) com classificação de impacto
  (baixo/médio/alto/crítico), link para fonte oficial e vínculo com tarefas.
- Fase 6: feed automático + resumo executivo com IA.
- Disclaimer permanente: informação de apoio, não substitui parecer profissional.

### 2.9 Assistente de IA tributário (Fase 4; stub no MVP)
- Chat sobre os **dados da própria organização** (simulações, regras, checklist).
- Explica cálculos, gera planos de ação e pareceres preliminares.
- Regras rígidas: **não inventa legislação**, cita premissas, sempre indica necessidade de
  validação por contador/advogado. Integração via API Anthropic (configurável por env).

### 2.10 Relatórios (MVP: PDF executivo + XLSX/CSV)
- Impacto por empresa, por produto/serviço, por ano; plano de ação; riscos.
- Todo relatório lista as **premissas utilizadas** e referência das regras aplicadas.

### 2.11 Integrações (Fase 5; fundações no MVP)
- API REST com OpenAPI/Swagger (`/docs`), tokens de API por empresa (`api_keys`),
  rate limiting, importação CSV/XLSX no MVP; webhooks e conectores ERP na fase 5.

### 2.12 Segurança e LGPD (MVP)
- JWT access + refresh, hash bcrypt, 2FA opcional (fase 2), isolamento multi-tenant por
  `organization_id` em todas as consultas, RBAC, auditoria com IP/usuário/data,
  soft delete + política de retenção, backups (volume Postgres), variáveis de ambiente.

---

## 3. Regras de negócio essenciais

1. Comparação **modelo atual × modelo futuro** sempre disponível, por item e consolidada.
2. Simulação de **cada ano da transição (2026–2033)** com fatores próprios por ano.
3. Motor 100% **parametrizável**: alíquotas, fatores de transição, reduções e exceções são
   dados (tabelas), nunca código. Admin altera sem deploy.
4. Toda simulação grava **memória de cálculo** completa (JSON por item/ano).
5. Todo relatório declara **premissas** usadas.
6. Todo valor calculado é **rastreável** até regra/parâmetro/documento de origem.
7. Incertezas legislativas (ex.: alíquota de referência, alíquotas do IS) são
   **premissas configuráveis** sinalizadas na UI e nos relatórios.
8. Anos de teste (2026: CBS 0,9% + IBS 0,1%) tratados com compensação configurável contra
   PIS/Cofins, conforme premissa.
9. Simples Nacional: simulação assume permanência no regime e gera alerta para estudo de
   migração (regra parametrizável).

---

## 4. Requisitos não funcionais

| Categoria | Requisito |
|---|---|
| Escala | Multi-tenant shared-schema com `organization_id`; pronto para sharding futuro |
| Performance | Simulação de 1.000 itens × 8 anos < 30s (síncrona no MVP; worker na fase 2) |
| Segurança | OWASP top 10, JWT curto + refresh, bcrypt, rate limit em auth, CORS restrito |
| LGPD | Minimização, consentimento no cadastro, soft delete, auditoria, exportação de dados |
| Disponibilidade | Stateless API, pronto para réplicas; Redis para cache/filas |
| Observabilidade | Logs estruturados, health checks `/health`, auditoria persistida |
| i18n | Interface 100% pt-BR; moeda BRL; datas dd/mm/aaaa |

---

## 5. MVP — escopo fechado

1. Login + registro de organização (JWT + refresh).
2. Cadastro de empresas e filiais.
3. Catálogo de produtos/serviços + importação CSV com validação linha a linha.
4. Cadastro manual de regras CBS/IBS/IS + editor dos anos de transição + premissas.
5. Simulador atual × futuro (2026–2033, 3 cenários, memória de cálculo).
6. Dashboard de impacto com gráficos e alertas de risco.
7. Checklist de adequação com template padrão e painel de maturidade.
8. Relatório executivo em PDF + exportação XLSX/CSV.
9. Logs de auditoria consultáveis.
10. UI profissional, responsiva, tema claro/escuro, onboarding guiado.

Critérios de aceite do MVP: usuário cria conta → cadastra empresa → importa CSV de produtos →
aplica regras seed/dadas → clica "Gerar diagnóstico" → vê impacto no dashboard → exporta PDF.
Tudo auditado, tudo parametrizável, zero regra fiscal hardcoded.

---

## 6. Fora de escopo do MVP (e por quê)

| Item | Fase | Motivo |
|---|---|---|
| Parsing de XML NF-e/CT-e | 2 | Exige worker + storage robusto; tabelas já criadas |
| Motor de créditos por documento | 3 | Depende da fase 2 |
| IA conversacional plena | 4 | Stub seguro no MVP; exige guardrails e RAG |
| Conectores ERP + webhooks | 5 | Fundações (API keys, OpenAPI) já no MVP |
| Monitor legislativo automático | 6 | Curadoria manual no MVP |
| Marketplace contadores | 7 | Depende de tração |
