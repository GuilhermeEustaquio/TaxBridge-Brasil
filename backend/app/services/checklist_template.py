"""Template padrão do checklist de adequação à Reforma Tributária (por área)."""

CHECKLIST_TEMPLATE: list[dict] = [
    # Fiscal
    {"area": "fiscal", "priority": "alta", "title": "Mapear NCM/NBS de todos os produtos e serviços",
     "description": "Garantir cadastro completo e correto de NCM (produtos) e NBS (serviços) — base do cálculo de CBS/IBS."},
    {"area": "fiscal", "priority": "alta", "title": "Parametrizar regras de CBS, IBS e Imposto Seletivo",
     "description": "Cadastrar alíquotas, reduções de base e exceções por categoria no motor tributário."},
    {"area": "fiscal", "priority": "alta", "title": "Identificar produtos sujeitos ao Imposto Seletivo",
     "description": "Bebidas açucaradas, alcoólicas, fumo, veículos, bens minerais etc. — acompanhar regulamentação."},
    {"area": "fiscal", "priority": "media", "title": "Revisar benefícios fiscais vigentes e seu fim programado",
     "description": "Incentivos de ICMS serão extintos até 2032 (fundo de compensação) — quantificar perda."},
    {"area": "fiscal", "priority": "media", "title": "Acompanhar obrigações acessórias do ano-teste 2026",
     "description": "Destaque de CBS/IBS nos documentos fiscais; dispensa de recolhimento condicionada ao cumprimento."},
    # Contábil
    {"area": "contabil", "priority": "alta", "title": "Adequar plano de contas para CBS/IBS/IS",
     "description": "Criar contas para débitos, créditos e recolhimentos dos novos tributos."},
    {"area": "contabil", "priority": "media", "title": "Definir política contábil para créditos em transição",
     "description": "Saldos credores de PIS/Cofins e ICMS: regras de utilização/compensação na transição."},
    {"area": "contabil", "priority": "media", "title": "Atualizar relatórios gerenciais com dupla apuração",
     "description": "2026-2032 exigirá visão simultânea dos dois sistemas."},
    # Financeiro
    {"area": "financeiro", "priority": "alta", "title": "Simular impacto no fluxo de caixa do split payment",
     "description": "Recolhimento na liquidação financeira antecipa o desembolso do imposto — dimensionar capital de giro."},
    {"area": "financeiro", "priority": "alta", "title": "Revisar formação de preços por produto/serviço",
     "description": "Tributos 'por fora' mudam o preço de prateleira; usar preço de equilíbrio do simulador."},
    {"area": "financeiro", "priority": "media", "title": "Renegociar prazos com clientes e fornecedores",
     "description": "Mitigar perda de float; avaliar antecipação de recebíveis."},
    # Jurídico
    {"area": "juridico", "priority": "alta", "title": "Revisar contratos de longo prazo (cláusulas tributárias)",
     "description": "Cláusulas de reequilíbrio econômico-financeiro frente à mudança de carga."},
    {"area": "juridico", "priority": "media", "title": "Mapear discussões judiciais de PIS/Cofins/ICMS em curso",
     "description": "Impacto da extinção dos tributos sobre teses e créditos discutidos."},
    {"area": "juridico", "priority": "media", "title": "Acompanhar regulamentações pendentes (IS, regimes específicos)",
     "description": "Comitê Gestor do IBS, alíquotas de referência, split payment operacional."},
    # TI
    {"area": "ti", "priority": "alta", "title": "Atualizar ERP para layouts de NF-e/NFS-e com CBS/IBS/IS",
     "description": "Novos campos e grupos de tributação nos documentos fiscais eletrônicos (NT 2025)."},
    {"area": "ti", "priority": "alta", "title": "Planejar convivência de duas apurações nos sistemas",
     "description": "Cadastros, cálculos e relatórios em paralelo durante a transição."},
    {"area": "ti", "priority": "media", "title": "Integrar sistemas ao TaxBridge via API",
     "description": "Automatizar envio de catálogo e recebimento de simulações (tokens de API)."},
    # Vendas
    {"area": "vendas", "priority": "alta", "title": "Treinar time comercial na nova lógica de preços",
     "description": "Tributo por fora, crédito ao cliente B2B e impacto por UF de destino."},
    {"area": "vendas", "priority": "media", "title": "Revisar tabela de preços por canal e por UF",
     "description": "Alíquota no destino unifica concorrência interestadual — reposicionar ofertas."},
    # Compras
    {"area": "compras", "priority": "alta", "title": "Avaliar fornecedores pela transferência de crédito",
     "description": "Fornecedor do Simples/sem crédito pleno encarece a cadeia no novo modelo."},
    {"area": "compras", "priority": "media", "title": "Renegociar contratos de suprimento considerando créditos CBS/IBS",
     "description": "Crédito amplo muda o custo efetivo de aquisição."},
]
