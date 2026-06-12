"""Smoke test do fluxo MVP completo via API (TestClient + SQLite)."""

import io

COMPANY = {
    "legal_name": "Indústria Modelo Ltda",
    "cnpj": "11222333000181",
    "tax_regime": "real",
    "segment": "Indústria",
    "uf": "SP",
    "municipality": "São Paulo",
}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_requires_lgpd_consent(client):
    response = client.post("/api/v1/auth/register", json={
        "organization_name": "Sem Consentimento", "name": "X", "email": "x@x.com.br",
        "password": "SenhaForte@123", "lgpd_consent": False,
    })
    assert response.status_code == 422


def test_login_and_me(client, auth_headers):
    response = client.post("/api/v1/auth/login", json={
        "email": "dona@teste.com.br", "password": "SenhaForte@123",
    })
    assert response.status_code == 200
    assert "refresh_token" in response.json()

    me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    body = me.json()
    assert body["user"]["role"]["slug"] == "dono_conta"
    assert float(body["organization"]["assumptions"]["cbs_reference_rate"]) == 8.8


def test_login_wrong_password_is_neutral(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "dona@teste.com.br", "password": "errada",
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciais inválidas"


def test_refresh_token_flow(client):
    tokens = client.post("/api/v1/auth/login", json={
        "email": "dona@teste.com.br", "password": "SenhaForte@123",
    }).json()
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    # access token não serve como refresh
    bad = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert bad.status_code == 401


def _create_company(client, auth_headers) -> str:
    listed = client.get("/api/v1/companies", headers=auth_headers).json()
    for item in listed["items"]:
        if item["cnpj"] == "11.222.333/0001-81":
            return item["id"]
    response = client.post("/api/v1/companies", json=COMPANY, headers=auth_headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_company_crud_and_validation(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    # CNPJ inválido rejeitado
    bad = client.post("/api/v1/companies", json={**COMPANY, "cnpj": "123"}, headers=auth_headers)
    assert bad.status_code == 422
    # Duplicado rejeitado
    duplicate = client.post("/api/v1/companies", json=COMPANY, headers=auth_headers)
    assert duplicate.status_code == 409
    # Filial
    branch = client.post(f"/api/v1/companies/{company_id}/branches",
                         json={"name": "Filial MG", "uf": "MG"}, headers=auth_headers)
    assert branch.status_code == 201


def test_transition_years_seeded_and_editable(client, auth_headers):
    years = client.get("/api/v1/transition-years", headers=auth_headers).json()
    assert [y["year"] for y in years] == list(range(2026, 2034))
    y2026 = next(y for y in years if y["year"] == 2026)
    assert y2026["cbs_rate_override"] == 0.9 and y2026["test_year_compensable"] is True

    updated = client.put("/api/v1/transition-years/2030", json={"legacy_icms_iss_factor": "0.75"},
                         headers=auth_headers)
    assert updated.status_code == 200
    assert updated.json()["legacy_icms_iss_factor"] == 0.75
    # restaura default para não afetar os demais testes
    client.put("/api/v1/transition-years/2030", json={"legacy_icms_iss_factor": "0.8"}, headers=auth_headers)


def test_csv_import_with_line_errors(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    csv_content = (
        "sku;nome;ncm;cest;cfop;cst_icms;csosn;uf_origem;uf_destino;preco_unitario;custo_unitario;volume_mensal;seletivo\n"
        "P-001;Arroz 5kg;10063021;;5102;020;;SP;SP;25,90;18,00;1000;nao\n"
        "P-002;Refrigerante 2L;22021000;;5102;000;;SP;RJ;9,50;4,20;5000;sim\n"
        "P-003;NCM invalido;123;;5102;;;SP;SP;10,00;5,00;100;nao\n"
        "P-004;Servico de TI;84713012;;5102;;;SP;SP;4890,00;3550,00;80;nao\n"
    )
    response = client.post(
        "/api/v1/products/import-csv",
        data={"company_id": company_id},
        files={"file": ("produtos.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["created"] == 3
    assert len(body["errors"]) == 1 and body["errors"][0]["line"] == 4

    # reimportação = update (idempotente por SKU)
    again = client.post(
        "/api/v1/products/import-csv",
        data={"company_id": company_id},
        files={"file": ("produtos.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=auth_headers,
    )
    assert again.json()["updated"] == 3


def _create_rules(client, auth_headers):
    existing = client.get("/api/v1/tax-rules", headers=auth_headers).json()
    if existing["total"] == 0:
        for rule in [
            {"name": "Cesta básica", "item_kind": "product", "ncm_pattern": "1006*", "priority": 100,
             "icms_rate": "7", "cbs_reduction_pct": "100", "ibs_reduction_pct": "100",
             "legal_basis": "LC 214/2025 Anexo I"},
            {"name": "Bebidas açucaradas IS", "item_kind": "product", "ncm_pattern": "2202*", "priority": 90,
             "icms_rate": "18", "pis_rate": "1.65", "cofins_rate": "7.6", "is_rate": "10"},
            {"name": "Geral produtos", "item_kind": "product", "priority": 0,
             "icms_rate": "18", "pis_rate": "1.65", "cofins_rate": "7.6"},
        ]:
            response = client.post("/api/v1/tax-rules", json=rule, headers=auth_headers)
            assert response.status_code == 201, response.text


def test_simulation_full_flow(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    _create_rules(client, auth_headers)

    response = client.post("/api/v1/simulations", json={
        "company_id": company_id, "name": "Simulação teste", "scenario": "provavel",
        "year_start": 2026, "year_end": 2033,
    }, headers=auth_headers)
    assert response.status_code == 201, response.text
    simulation = response.json()
    years = simulation["summary"]["years"]
    assert len(years) == 8
    assert years[0]["year"] == 2026 and years[-1]["year"] == 2033
    assert simulation["assumptions_snapshot"]["cbs_reference_rate"] == "8.8"

    items = client.get(f"/api/v1/simulations/{simulation['id']}/items?year=2033",
                       headers=auth_headers).json()
    assert items["total"] == 3  # 3 produtos válidos importados
    memory = items["items"][0]["calc_memory"]
    assert "formulas" in memory and "premissas" in memory and "regra" in memory

    # Exports: PDF, XLSX e CSV
    pdf = client.get(f"/api/v1/simulations/{simulation['id']}/export.pdf", headers=auth_headers)
    assert pdf.status_code == 200 and pdf.content[:5] == b"%PDF-"
    xlsx = client.get(f"/api/v1/simulations/{simulation['id']}/export.xlsx", headers=auth_headers)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"
    csv_export = client.get(f"/api/v1/simulations/{simulation['id']}/export.csv", headers=auth_headers)
    assert csv_export.status_code == 200 and "Item" in csv_export.text

    reports = client.get("/api/v1/reports", headers=auth_headers).json()
    assert reports["total"] >= 3


def test_diagnostic_one_click(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    _create_rules(client, auth_headers)
    response = client.post(f"/api/v1/companies/{company_id}/diagnostico", headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["origin"] == "diagnostico"


def test_dashboard_payload(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    response = client.get(f"/api/v1/dashboard?company_id={company_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["latest_simulation"] is not None
    assert body["onboarding"]["has_simulation"] is True
    assert isinstance(body["alerts"], list)
    assert body["counts"]["products"] == 3


def test_compliance_template_and_summary(client, auth_headers):
    company_id = _create_company(client, auth_headers)
    applied = client.post("/api/v1/compliance/apply-template", json={"company_id": company_id},
                          headers=auth_headers)
    assert applied.status_code == 200
    assert applied.json()["created"] == 21
    # idempotente
    again = client.post("/api/v1/compliance/apply-template", json={"company_id": company_id},
                        headers=auth_headers)
    assert again.json()["created"] == 0

    tasks = client.get(f"/api/v1/compliance/tasks?company_id={company_id}&area=fiscal",
                       headers=auth_headers).json()
    assert tasks["total"] == 5
    task_id = tasks["items"][0]["id"]
    done = client.put(f"/api/v1/compliance/tasks/{task_id}", json={"status": "concluido"},
                      headers=auth_headers)
    assert done.status_code == 200

    summary = client.get(f"/api/v1/compliance/summary?company_id={company_id}",
                         headers=auth_headers).json()
    assert summary["total"] == 21 and summary["done"] == 1


def test_legal_updates_crud(client, auth_headers):
    response = client.post("/api/v1/legal-updates", json={
        "norm_type": "lc", "reference": "LC 214/2025", "title": "Regulamentação da Reforma",
        "impact": "critico", "summary": "Regulamenta CBS/IBS/IS.",
    }, headers=auth_headers)
    assert response.status_code == 201
    listed = client.get("/api/v1/legal-updates?impact=critico", headers=auth_headers).json()
    assert listed["total"] >= 1


def test_rbac_leitor_cannot_write(client, auth_headers):
    invited = client.post("/api/v1/users", json={
        "name": "Leitor Teste", "email": "leitor@teste.com.br", "role_slug": "leitor",
    }, headers=auth_headers)
    assert invited.status_code == 201
    password = invited.json()["temporary_password"]

    login = client.post("/api/v1/auth/login", json={"email": "leitor@teste.com.br", "password": password})
    reader_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # leitura ok
    assert client.get("/api/v1/companies", headers=reader_headers).status_code == 200
    # escrita negada (403)
    denied = client.post("/api/v1/companies", json={**COMPANY, "cnpj": "22333444000155"},
                         headers=reader_headers)
    assert denied.status_code == 403
    denied_sim = client.post("/api/v1/simulations", json={
        "company_id": _create_company(client, auth_headers), "name": "X",
    }, headers=reader_headers)
    assert denied_sim.status_code == 403


def test_tenant_isolation(client, auth_headers):
    other = client.post("/api/v1/auth/register", json={
        "organization_name": "Outra Org", "name": "Outro Dono", "email": "outro@org.com.br",
        "password": "SenhaForte@123", "lgpd_consent": True,
    })
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    company_id = _create_company(client, auth_headers)
    # Org B não enxerga empresa da Org A
    assert client.get(f"/api/v1/companies/{company_id}", headers=other_headers).status_code == 404
    assert client.get("/api/v1/companies", headers=other_headers).json()["total"] == 0


def test_audit_logs_recorded(client, auth_headers):
    response = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    actions = {log["action"] for log in body["items"]}
    assert "auth.register" in actions or "auth.login" in actions
    assert any(a.startswith("company.") for a in actions)
    assert any(a.startswith("simulation.") for a in actions)
    sample = body["items"][0]
    assert "ip_address" in sample and "created_at" in sample


def test_api_keys_lifecycle(client, auth_headers):
    created = client.post("/api/v1/api-keys", json={"name": "ERP Integração"}, headers=auth_headers)
    assert created.status_code == 201
    body = created.json()
    assert body["secret"].startswith("tbk_")
    key_id = body["api_key"]["id"]
    revoked = client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
    assert revoked.status_code == 204


def test_ai_chat_offline_mode(client, auth_headers):
    response = client.post("/api/v1/ai/chat", json={"message": "Qual o impacto da reforma na minha empresa?"},
                           headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "não substitui parecer" in body["disclaimer"]
    assert body["model"] is None  # sem ANTHROPIC_API_KEY → modo offline
    assert body["conversation_id"]


def test_assumptions_update_is_audited(client, auth_headers):
    current = client.get("/api/v1/organizations/me", headers=auth_headers).json()["assumptions"]
    current["cbs_reference_rate"] = "9.5"
    updated = client.put("/api/v1/organizations/assumptions", json=current, headers=auth_headers)
    assert updated.status_code == 200
    assert float(updated.json()["assumptions"]["cbs_reference_rate"]) == 9.5
    logs = client.get("/api/v1/audit-logs?action=assumptions", headers=auth_headers).json()
    assert logs["total"] >= 1
