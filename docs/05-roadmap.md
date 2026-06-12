# Plano de Evolução do Produto

## Fase 1 — MVP Fiscal ✅ (este repositório)
**Objetivo:** valor imediato — diagnóstico de impacto da reforma em < 30 minutos de setup.
- Auth JWT + RBAC + auditoria · multiempresa · catálogo + CSV · regras CBS/IBS/IS e anos de
  transição parametrizáveis · simulador 2026–2033 com 3 cenários e memória de cálculo ·
  dashboard de impacto · checklist com template · monitor legislativo manual · PDF/XLSX/CSV.
- **Métrica de sucesso:** tempo até o primeiro diagnóstico; nº de simulações/org/semana.

## Fase 2 — Importação de XML (T+2 meses)
- Parser NF-e/NFC-e/NFS-e/CT-e (lote) no worker RQ (fila Redis já provisionada).
- Storage S3/MinIO (interface local já isolada) · validações e inconsistências · filtros.
- Simulação passa a usar **dados reais de faturamento** em vez de volume estimado.
- 2FA TOTP · blocklist de refresh tokens em Redis.

## Fase 3 — Motor de créditos (T+4 meses)
- Apuração crédito a crédito por documento (`tax_credits` por `invoice_item`).
- Créditos perdidos/potenciais/em risco com trilha por documento · relatório de aproveitamento.
- Conciliação crédito atual × crédito CBS/IBS projetado.

## Fase 4 — IA tributária (T+6 meses)
- RAG sobre dados da organização (simulações, regras, documentos, checklist).
- Geração de pareceres preliminares, planos de ação e resumos executivos.
- Guardrails: citações obrigatórias, sem invenção de legislação, disclaimers automáticos,
  revisão humana sinalizada. (Stub seguro já existe no MVP em `/ai/chat`.)

## Fase 5 — Integrações ERP (T+9 meses)
- Webhooks (eventos: simulação concluída, alerta crítico, tarefa vencida).
- Conectores: TOTVS, SAP B1, Omie, Bling, Conta Azul (priorizar por demanda).
- API keys por empresa (já existe) + rate limit por chave em Redis + portal do desenvolvedor.

## Fase 6 — Monitor legislativo automático (T+12 meses)
- Ingestão de fontes oficiais (DOU, Confaz, RFB, comitês IBS/CBS) + classificação de impacto
  por IA + vínculo automático a tarefas e regras afetadas (ex.: "NCM 2202 teve alíquota IS
  publicada — atualizar regra X").

## Fase 7 — Marketplace para contadores e consultorias (T+15 meses)
- Perfis públicos de escritórios parceiros, white-label de relatórios, indicação de clientes,
  revenue share, templates de checklist e de regras publicáveis entre organizações.

## Riscos e mitigação
| Risco | Mitigação |
|---|---|
| Mudança normativa (alíquotas, prazos) | Motor 100% parametrizado; atualização administrativa |
| Responsabilidade por cálculo | Disclaimers + memória de cálculo + premissas explícitas |
| Concorrência de ERPs | Foco em transição/simulação (não emissão fiscal) + integrações |
| Sazonalidade de interesse | Compliance contínuo + monitor legislativo geram recorrência |
