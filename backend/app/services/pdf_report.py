"""Relatório executivo em PDF (ReportLab) — layout profissional com premissas e disclaimer."""

import io
from datetime import datetime

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Company, Simulation

NAVY = colors.HexColor("#102A43")
BLUE = colors.HexColor("#2563EB")
GREEN = colors.HexColor("#059669")
RED = colors.HexColor("#DC2626")
GRAY = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")

DISCLAIMER = (
    "Documento gerado pelo TaxBridge Brasil como apoio à decisão. Valores são estimativas baseadas em "
    "premissas configuráveis (EC 132/2023, LC 214/2025 e regulamentação em evolução) e NÃO substituem "
    "parecer jurídico, contábil ou fiscal profissional."
)


def fmt_brl(value: float | None) -> str:
    if value is None:
        return "—"
    text = f"{value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {text}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}".replace(".", ",") + "%"


def _header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 18 * mm, width, 18 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(15 * mm, height - 12 * mm, "TaxBridge Brasil")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 15 * mm, height - 12 * mm, "Relatório Executivo — Reforma Tributária do Consumo")
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 6.5)
    footer_y = 10 * mm
    for i, line in enumerate(_wrap(DISCLAIMER, 150)):
        canvas.drawString(15 * mm, footer_y - i * 8, line)
    canvas.drawRightString(width - 15 * mm, footer_y, f"Página {doc.page}")
    canvas.restoreState()


def _wrap(text: str, width: int) -> list[str]:
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _table(data: list[list], col_widths: list[float], align_right_from: int = 1) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (align_right_from, 1), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return table


def _bar_chart(years: list[dict]) -> Drawing:
    drawing = Drawing(460, 190)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 40, 30, 390, 140
    chart.data = [
        [y["current_total"] or 0 for y in years],
        [y["future_total"] or 0 for y in years],
    ]
    chart.categoryAxis.categoryNames = [str(y["year"]) for y in years]
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 6.5
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = GRAY
    chart.bars[1].fillColor = BLUE
    chart.bars.strokeColor = colors.white
    chart.groupSpacing = 8
    drawing.add(chart)
    return drawing


def build_simulation_pdf(simulation: Simulation, company: Company, organization_name: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=26 * mm, bottomMargin=22 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
        title=f"TaxBridge — {simulation.name}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=NAVY, fontSize=16, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=NAVY, fontSize=11, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#1E293B"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=7.5, textColor=GRAY)

    summary = simulation.summary or {}
    years = summary.get("years", [])
    totals = summary.get("totals", {})
    story = []

    story.append(Paragraph("Impacto da Reforma Tributária do Consumo", h1))
    story.append(Paragraph(
        f"<b>{company.legal_name}</b> · CNPJ {company.cnpj} · {company.uf} · "
        f"Regime: {company.tax_regime.capitalize()} · Organização: {organization_name}", body))
    story.append(Paragraph(
        f"Simulação: <b>{simulation.name}</b> · Cenário: <b>{simulation.scenario}</b> · "
        f"Período: {simulation.year_start}–{simulation.year_end} · "
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", small))
    story.append(Spacer(1, 6))

    delta = totals.get("delta_final_year") or 0
    delta_pct = totals.get("delta_pct_revenue_final_year") or 0
    final_year = totals.get("final_year") or simulation.year_end
    direction = "AUMENTO" if delta > 0 else "REDUÇÃO"
    color = "#DC2626" if delta > 0 else "#059669"
    story.append(Paragraph(
        f'Em {final_year}, a carga tributária líquida estimada apresenta <b><font color="{color}">{direction} de '
        f"{fmt_brl(abs(delta))}</font></b> por ano em relação ao sistema atual "
        f"({fmt_pct(abs(delta_pct))} da receita anual simulada).", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Carga tributária líquida por ano — atual × futura", h2))
    if years:
        story.append(_bar_chart(years))
        story.append(Paragraph('<font color="#64748B">Cinza: sistema atual · Azul: sistema da reforma</font>', small))
        story.append(Spacer(1, 6))
        rows = [["Ano", "Carga atual", "Carga futura", "Δ anual", "CBS", "IBS", "IS", "Legado", "Caixa (split)"]]
        for y in years:
            rows.append([
                str(y["year"]), fmt_brl(y["current_total"]), fmt_brl(y["future_total"]), fmt_brl(y["delta"]),
                fmt_brl(y["cbs"]), fmt_brl(y["ibs"]), fmt_brl(y["is"]), fmt_brl(y["legacy"]),
                fmt_brl(y["cash_flow_impact"]),
            ])
        story.append(_table(rows, [14 * mm] + [21 * mm] * 8))

    top_items = summary.get("top_items", [])
    if top_items:
        story.append(Paragraph(f"Itens mais impactados em {final_year}", h2))
        rows = [["Item", "Tipo", "Carga atual", "Carga futura", "Δ", "Margem atual", "Margem futura", "Preço equilíbrio"]]
        for item in top_items:
            rows.append([
                Paragraph(item["item_name"][:60], body),
                "Produto" if item["item_kind"] == "product" else "Serviço",
                fmt_brl(item["current_net"]), fmt_brl(item["future_net"]), fmt_brl(item["delta_net"]),
                fmt_pct(item["margin_current_pct"]), fmt_pct(item["margin_future_pct"]),
                fmt_brl(item["breakeven_price"]),
            ])
        story.append(_table(rows, [44 * mm, 14 * mm, 21 * mm, 21 * mm, 19 * mm, 19 * mm, 19 * mm, 22 * mm]))

    without_rule = summary.get("items_without_rule", [])
    if without_rule:
        story.append(Paragraph("Riscos de parametrização", h2))
        story.append(Paragraph(
            "Itens sem regra tributária aplicável (não calculados): " +
            ", ".join(i["name"] for i in without_rule), body))

    story.append(Paragraph("Premissas utilizadas", h2))
    assumptions = simulation.assumptions_snapshot or {}
    premise_rows = [["Premissa", "Valor"]]
    labels = {
        "cbs_reference_rate": "Alíquota de referência CBS (p.p.) — estimativa configurável",
        "ibs_reference_rate": "Alíquota de referência IBS (p.p.) — estimativa configurável",
        "input_cost_creditable_ratio": "% do preço em insumos creditáveis",
        "current_credit_efficiency": "Eficiência de créditos — sistema atual",
        "future_credit_efficiency": "Eficiência de créditos — CBS/IBS",
        "split_payment_enabled": "Split payment considerado",
        "split_payment_float_days": "Dias de antecipação (split payment)",
        "cost_of_capital_annual": "Custo de capital anual",
        "simples_effective_rate": "Alíquota efetiva Simples (p.p.)",
        "icms_inside_price": "ICMS tratado como % direto do preço (simplificação)",
    }
    for key, label in labels.items():
        if key in assumptions:
            value = assumptions[key]
            if isinstance(value, bool):
                value = "Sim" if value else "Não"
            premise_rows.append([Paragraph(label, body), str(value)])
    story.append(_table(premise_rows, [120 * mm, 40 * mm]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Memória de cálculo por item/ano disponível no TaxBridge (Simulações → Itens → Memória). "
        "Premissas marcadas como configuráveis podem ser ajustadas em Parâmetros sem alteração de código.", small))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
