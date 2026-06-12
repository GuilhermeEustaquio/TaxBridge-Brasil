"""Assistente de IA tributário (fase 4 — stub funcional no MVP).

Responde com base EXCLUSIVA nos dados da organização (simulações, regras,
premissas, checklist) injetados como contexto. Guardrails:
- nunca inventar legislação;
- declarar premissas e incertezas;
- sempre recomendar validação por contador/advogado/especialista.

Sem ANTHROPIC_API_KEY configurada, devolve resposta offline estruturada com os
dados disponíveis e os mesmos disclaimers (a UI funciona de ponta a ponta).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Company, Organization, Simulation, TaxRule
from app.services.dashboard_service import compliance_summary

settings = get_settings()

DISCLAIMER = (
    "Resposta gerada com base nos dados e premissas cadastrados na sua organização. "
    "Conteúdo de apoio à decisão: não substitui parecer de contador, advogado ou "
    "especialista fiscal. Valide antes de qualquer decisão tributária."
)

SYSTEM_PROMPT = """Você é o assistente tributário do TaxBridge Brasil, especializado na \
Reforma Tributária do Consumo (EC 132/2023, LC 214/2025 — transição CBS/IBS/IS de 2026 a 2033).

Regras invioláveis:
1. Responda APENAS com base no contexto fornecido (dados da organização do usuário) e em \
conhecimento geral consolidado sobre a reforma. NUNCA invente artigos de lei, alíquotas \
oficiais, prazos ou números que não estejam no contexto.
2. Todo valor calculado citado deve indicar que vem de simulação parametrizada com premissas \
configuráveis (alíquotas de referência são estimativas até regulamentação definitiva).
3. Se a pergunta exigir interpretação legal, posicionamento definitivo ou dado ausente do \
contexto, diga explicitamente que isso depende de validação por contador/advogado.
4. Responda em português do Brasil, de forma objetiva e estruturada.
5. Encerre indicando os próximos passos práticos dentro do TaxBridge quando fizer sentido \
(ex.: rodar nova simulação, ajustar premissas, completar checklist)."""


def build_org_context(db: Session, organization: Organization, company_id: uuid.UUID | None) -> str:
    """Serializa um resumo compacto dos dados da organização para o modelo."""
    companies = db.scalars(
        select(Company).where(Company.organization_id == organization.id, Company.deleted_at.is_(None))
    ).all()
    rules_count = len(
        db.scalars(
            select(TaxRule.id).where(
                TaxRule.organization_id == organization.id,
                TaxRule.deleted_at.is_(None),
                TaxRule.is_active.is_(True),
            )
        ).all()
    )
    sim_query = (
        select(Simulation)
        .where(Simulation.organization_id == organization.id, Simulation.deleted_at.is_(None))
        .order_by(Simulation.created_at.desc())
    )
    if company_id:
        sim_query = sim_query.where(Simulation.company_id == company_id)
    simulation = db.scalars(sim_query.limit(1)).first()
    compliance = compliance_summary(db, organization.id, company_id)

    lines = [
        f"Organização: {organization.name}",
        "Empresas: " + "; ".join(f"{c.legal_name} ({c.tax_regime}, {c.uf})" for c in companies[:10]),
        f"Regras tributárias ativas: {rules_count}",
        f"Premissas configuradas: {organization.assumptions}",
        f"Checklist de adequação: {compliance['done']}/{compliance['total']} concluídas, "
        f"{compliance['overdue']} vencidas, progresso {compliance['overall_progress_pct']}%",
    ]
    if simulation is not None:
        lines.append(
            f"Última simulação: '{simulation.name}' (cenário {simulation.scenario}, "
            f"{simulation.year_start}-{simulation.year_end})"
        )
        lines.append(f"Resumo por ano (valores em R$): {simulation.summary.get('years', [])}")
        lines.append(f"Itens sem regra: {simulation.summary.get('items_without_rule', [])}")
        lines.append(f"Top itens impactados: {simulation.summary.get('top_items', [])[:5]}")
    else:
        lines.append("Nenhuma simulação executada ainda.")
    return "\n".join(lines)


def _offline_answer(context: str, message: str) -> str:
    return (
        "**Assistente em modo offline** (chave da API de IA não configurada — defina "
        "`ANTHROPIC_API_KEY` no backend para ativar respostas completas).\n\n"
        f"Sua pergunta: \"{message}\"\n\n"
        "Dados disponíveis na sua organização para análise:\n\n"
        f"```\n{context}\n```\n\n"
        "Sugestões enquanto isso: consulte o Dashboard para o comparativo atual × futuro, "
        "a tela Simulações para a memória de cálculo item a item e a tela Parâmetros para "
        "ajustar premissas configuráveis."
    )


def answer_question(db: Session, organization: Organization, company_id: uuid.UUID | None, message: str) -> tuple[str, str | None]:
    """Retorna (resposta, modelo_usado|None)."""
    context = build_org_context(db, organization, company_id)
    if not settings.ANTHROPIC_API_KEY:
        return _offline_answer(context, message), None

    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"<contexto_da_organizacao>\n{context}\n</contexto_da_organizacao>\n\n"
                        f"Pergunta do usuário: {message}"
                    ),
                }
            ],
        )
    except anthropic.APIError:
        return (
            "O assistente de IA está temporariamente indisponível. Tente novamente em instantes.\n\n"
            + _offline_answer(context, message)
        ), None

    if response.stop_reason == "refusal":
        return (
            "O assistente não pôde responder a esta pergunta. Reformule focando nos dados "
            "fiscais da sua organização.",
            settings.CLAUDE_MODEL,
        )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text or "Não foi possível gerar resposta. Tente novamente.", settings.CLAUDE_MODEL
