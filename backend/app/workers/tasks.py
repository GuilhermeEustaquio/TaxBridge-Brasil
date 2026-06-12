"""Jobs assíncronos (fila Redis/RQ).

Fase 2: parsing de XMLs fiscais (NF-e, NFC-e, NFS-e, CT-e) em lote.
O job abaixo é o contrato/stub — o enfileiramento já pode ser integrado por ERPs
via API; o processamento completo entra na fase 2 do roadmap.
"""

import uuid


def process_invoice_xml(organization_id: str, company_id: str, xml_path: str) -> dict:
    """Stub da fase 2: extrai campos fiscais do XML e popula invoices/invoice_items."""
    return {
        "status": "pending_phase_2",
        "detail": "Parser de XML fiscal será habilitado na fase 2 (ver docs/05-roadmap.md)",
        "organization_id": organization_id,
        "company_id": company_id,
        "xml_path": xml_path,
        "job_id": uuid.uuid4().hex,
    }
