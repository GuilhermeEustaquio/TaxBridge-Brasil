# Regras de Negócio e Motor de Cálculo

> **Princípio nº 1:** nenhuma alíquota, fator de transição ou exceção é hardcoded. Tudo vive em
> `tax_rules`, `tax_transition_years` e `organizations.assumptions`, editáveis por administrador.
> O motor (`app/services/tax_engine.py`) apenas **aplica** parâmetros e registra memória de cálculo.

## 1. Casamento item → regra (`tax_rules`)

Para cada item (produto/serviço) o motor seleciona a regra ativa **mais específica**:

```
score = 0
+ ncm/nbs casa exatamente............ +40   (prefixo com '*' ...... +25)
+ cfop igual......................... +15
+ uf_origin igual.................... +10
+ uf_dest igual...................... +10
+ item_kind específico............... +5
+ tax_regime igual................... +5
+ company_id da regra = empresa...... +20   (regra org-wide = 0)
desempate: priority (maior vence), depois updated_at mais recente
```

Sem regra aplicável ⇒ item entra na simulação **sem cálculo** e gera alerta
`"produto sem parametrização"` (risco de divergência) — nunca calcular silenciosamente errado.

## 2. Cenário ATUAL (por item, base anual = preço × volume mensal × 12)

```
ICMS  = base × icms_rate                     (produtos; premissa simplificada "por dentro" documentada)
ISS   = base × iss_rate                      (serviços)
PIS   = base × pis_rate                      COFINS = base × cofins_rate
IPI   = base × ipi_rate
débitos_atual   = soma acima
créditos_atual  = base × input_cost_creditable_ratio × (icms+pis+cofins) × current_credit_efficiency
                  (produtos; serviços tipicamente sem crédito no cumulativo — regra decide via credit_allowed)
carga_atual     = débitos_atual − créditos_atual
```

**Simples Nacional:** `carga_atual = base × simples_effective_rate` (premissa configurável);
cenário futuro assume **permanência no Simples** (LC 214 mantém o regime) ⇒ carga futura ≈ atual,
com **alerta automático** para estudo de migração para o regime regular (split de crédito aos clientes).

## 3. Cenário FUTURO (por item × ano `Y` de 2026 a 2033)

Fatores do ano vêm de `tax_transition_years` (ver tabela em docs/02). Alíquotas efetivas:

```
cbs_aliq(Y) = cbs_rate_override(Y)                                    se definido (ex.: 0,9 em 2026)
            senão (cbs_rate_da_regra ou cbs_reference_rate) × cbs_factor(Y) + cbs_adjustment_pp(Y)
ibs_aliq(Y) = idem com ibs_*
ajuste de cenário: ± scenario_adjustments[cenário].rate_delta_pp distribuído proporcionalmente CBS/IBS
reduções da regra: cbs_aliq ×= (1 − cbs_reduction_pct/100); idem IBS   (cesta básica = 100% ⇒ zero)

CBS(Y)    = base × cbs_aliq(Y)
IBS(Y)    = base × ibs_aliq(Y)
IS(Y)     = base × is_rate                       somente se selective_active(Y) e regra tem is_rate
legado(Y) = [ICMS+ISS] × legacy_icms_iss_factor(Y) + [PIS+COFINS] × pis_cofins_factor(Y) + IPI × pis_cofins_factor(Y)*
créditos_cbs_ibs(Y)  = base × input_cost_creditable_ratio × (cbs_aliq+ibs_aliq) × future_credit_efficiency × credit_allowed
créditos_legados(Y)  = base × input_cost_creditable_ratio × [ICMS×legacy_factor + (PIS+COFINS)×pc_factor] × current_credit_efficiency
                       (tributos legados remanescentes seguem creditáveis na proporção dos fatores; ISS/IPI não creditáveis)
ano-teste compensável (2026): se test_year_compensable, CBS+IBS do teste compensam PIS/Cofins até o limite
                              e NÃO geram crédito próprio (valor neutralizado pela compensação)
carga_futura(Y) = CBS + IBS + IS + legado − créditos_cbs_ibs − créditos_legados − compensação
```
\* IPI segue fator do PIS/Cofins como premissa simplificada (zerado a partir de 2027, exceto ZFM — exceção via regra própria).

## 4. Indicadores financeiros

```
margem_atual %  = (preço − custo − carga_atual_unit) / preço
margem_futura % = (preço − custo − carga_futura_unit) / preço
preço_equilíbrio(Y): preço' tal que margem_futura(preço') = margem_atual   [resolvido algebricamente]
precisa_reajustar = preço_equilíbrio > preço × 1,001
impacto_caixa(Y) = split_payment_enabled ? (CBS+IBS) × (split_payment_float_days/365) × cost_of_capital_annual : 0
                   (custo financeiro anual da antecipação do recolhimento via split payment — premissa)
```

## 5. Memória de cálculo (obrigatória)

Cada `simulation_item` grava JSON com: regra aplicada (id, nome, base legal), todas as alíquotas
e fatores usados, fórmulas em texto, premissas (com flag `configuravel: true`) e avisos.
Relatórios reproduzem premissas; **todo número da UI é rastreável**.

## 6. Alertas de risco (dashboard)

| Alerta | Gatilho | Severidade |
|---|---|---|
| Item sem parametrização | item sem regra casada | crítico |
| Sujeito ao Imposto Seletivo | `is_rate > 0` | alto |
| Compressão de margem | margem_futura − margem_atual ≤ −3pp em 2033 | alto |
| Necessidade de reajuste | preço_equilíbrio > preço atual | médio |
| Créditos em risco | regra com `credit_allowed = false` | médio |
| Simples Nacional | empresa no Simples | médio (estudo de migração) |
| Checklist atrasado | tarefas `vencido`/`critico` | alto |
| Alíquota IS é premissa | IS usado antes de regulamentação específica | informativo |

## 7. Incertezas legislativas = premissas configuráveis

Pontos ainda dependentes de regulamentação (alíquota de referência CBS/IBS, alíquotas do IS,
split payment operacional, regimes específicos) são **parâmetros com default documentado** e
marcação explícita na memória de cálculo e nos relatórios. A atualização é administrativa
(UI Parâmetros), sem deploy.

## 8. RBAC

| Perfil | Nível | Pode |
|---|---|---|
| admin_global | 100 | tudo (inclui usuários, API keys, premissas) |
| dono_conta | 90 | tudo na organização |
| contador | 70 | empresas, catálogo, regras, simulações, compliance, relatórios, auditoria |
| fiscal | 60 | catálogo, regras, simulações, compliance, legislativo |
| financeiro | 50 | simulações, relatórios, compliance |
| consultor | 40 | simulações e relatórios |
| leitor | 10 | somente leitura |

Escrita sempre exige nível mínimo do recurso; tudo auditado (`audit_logs`: usuário, IP,
user-agent, ação, entidade, metadados, timestamp).
