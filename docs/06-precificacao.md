# Sugestão de Precificação SaaS

## Estratégia
Cobrança **por organização + nº de CNPJs ativos** (empresas + filiais), o driver natural de valor
para empresas e para escritórios contábeis. Trial de 14 dias com dados de demonstração. Preços de
lançamento (ajustar com pesquisa de willingness-to-pay).

## Planos

| | **Starter** | **Profissional** | **Escritório** | **Enterprise** |
|---|---|---|---|---|
| Preço (mensal, anual −20%) | **R$ 297/mês** | **R$ 797/mês** | **R$ 1.497/mês** | sob consulta |
| Público | PME single-CNPJ | Empresa multi-filial | Contadores/consultorias | Grupos e ERPs |
| CNPJs | 1 | até 5 (+R$ 99/extra) | até 25 (+R$ 49/extra) | ilimitado |
| Usuários | 3 | 10 | 25 | ilimitado |
| Produtos/serviços | 500 | 5.000 | 5.000/empresa | ilimitado |
| Simulações/mês | 10 | ilimitado | ilimitado | ilimitado |
| Importação CSV | ✔ | ✔ | ✔ | ✔ |
| Importação XML (F2) | — | ✔ (10k docs/mês) | ✔ (50k docs/mês) | ✔ |
| Motor de créditos (F3) | — | ✔ | ✔ | ✔ |
| IA tributária (F4) | — | 200 msgs/mês | 1.000 msgs/mês | custom |
| API + webhooks (F5) | — | ✔ | ✔ | ✔ + SLA |
| Relatórios white-label (F7) | — | — | ✔ | ✔ |
| Suporte | e-mail | prioritário | prioritário + onboarding | CSM dedicado + SLA 99,9% |

## Racional
- **Ancoragem de valor:** um estudo de impacto de reforma em consultoria custa R$ 15–80 mil;
  o plano Profissional entrega simulações ilimitadas por ~R$ 9,6 mil/ano.
- **Escritório** é o plano estratégico: cada contador traz N empresas (efeito rede → fase 7).
- **Expansão:** upsell por CNPJ extra, volume de XML e mensagens de IA (usage-based saudável).
- **Unit economics alvo:** CAC payback < 6 meses; margem bruta > 80% (infra ~R$ 35/org/mês);
  churn alvo < 2%/mês ancorado em compliance contínuo (não só na simulação inicial).

## Go-to-market
1. **2026 (ano-teste)** = urgência máxima: campanha "Sua empresa está pronta para o piloto da CBS/IBS?"
2. Canal contadores (plano Escritório com comissão recorrente de 20% no 1º ano).
3. Diagnóstico gratuito limitado (1 empresa, 20 produtos, sem export) como lead magnet.
4. Conteúdo: calculadora pública simplificada + webinars sobre LC 214/2025.
