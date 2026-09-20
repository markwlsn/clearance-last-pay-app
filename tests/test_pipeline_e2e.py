"""End-to-end integration tests for the local document extraction harness."""
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from pipeline.models import DocumentType, FlagCode
from pipeline.extractor import get_extractor
from pipeline.audit import AuditLogger
from pipeline.local_harness import app, run_cli_extraction


@pytest.fixture
def client(tmp_path):
    test_log = tmp_path / "test_audit.jsonl"
    app.state.audit_logger = AuditLogger(log_path=str(test_log))
    app.state.extractor = get_extractor(force_mock=True)
    return TestClient(app)


def test_e2e_quit_claim_valid(tmp_path):
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    file_path = samples_dir / "quit_claim_valid.pdf"

    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=str(audit_path))
    extractor = get_extractor(force_mock=True)

    result = run_cli_extraction(
        file_path=str(file_path),
        doc_type=DocumentType.QUIT_CLAIM,
        extractor=extractor,
        audit_logger=logger,
    )

    assert result.document_type == DocumentType.QUIT_CLAIM
    assert result.fields.employee_name.raw_value == "Juan Dela Cruz"
    assert result.fields.amounts_match.normalized_value is True
    assert len(result.flags) == 0

    logs = logger.get_recent_logs(limit=5)
    assert len(logs) == 1
    assert logs[0]["document_type"] == "QUIT_CLAIM"
    assert logs[0]["flag_count"] == 0


def test_e2e_quit_claim_mismatch(tmp_path):
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    file_path = samples_dir / "quit_claim_mismatch.pdf"

    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=str(audit_path))
    extractor = get_extractor(force_mock=True)

    result = run_cli_extraction(
        file_path=str(file_path),
        doc_type=DocumentType.QUIT_CLAIM,
        extractor=extractor,
        audit_logger=logger,
    )

    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_AMOUNT_MISMATCH in flag_codes
    assert FlagCode.FLAG_SIGNATURE_ABSENT in flag_codes

    logs = logger.get_recent_logs(limit=5)
    assert len(logs) == 1
    assert logs[0]["flag_count"] >= 2


def test_e2e_bank_bad_format(tmp_path):
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    file_path = samples_dir / "bank_bad_format.png"

    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=str(audit_path))
    extractor = get_extractor(force_mock=True)

    result = run_cli_extraction(
        file_path=str(file_path),
        doc_type=DocumentType.BANK_ENROLLMENT,
        extractor=extractor,
        audit_logger=logger,
    )

    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_FORMAT_MISMATCH in flag_codes


def test_e2e_clearance_missing_it(tmp_path):
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    file_path = samples_dir / "clearance_missing_it.pdf"

    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=str(audit_path))
    extractor = get_extractor(force_mock=True)

    result = run_cli_extraction(
        file_path=str(file_path),
        doc_type=DocumentType.CLEARANCE_SHEET,
        extractor=extractor,
        audit_logger=logger,
    )

    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_ACCOUNTABILITY_NOTED in flag_codes


def test_web_harness_endpoints(client):
    samples_dir = Path(__file__).resolve().parent.parent / "samples"
    file_path = samples_dir / "quit_claim_valid.pdf"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/precheck",
            data={"document_type": "QUIT_CLAIM"},
            files={"file": ("quit_claim_valid.pdf", f, "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "QUIT_CLAIM"
    assert data["fields"]["employee_name"]["raw_value"] == "Juan Dela Cruz"

    # Test audit log endpoint
    log_resp = client.get("/api/audit-logs")
    assert log_resp.status_code == 200
    logs = log_resp.json()
    assert len(logs) >= 1
    assert logs[0]["document_type"] == "QUIT_CLAIM"

    # Test web HTML endpoint
    html_resp = client.get("/")
    assert html_resp.status_code == 200
    assert "Clearance &amp; Last Pay" in html_resp.text or "Clearance & Last Pay" in html_resp.text


def test_parallel_routing_and_node_sign(client):
    """Verifies Option 1: Parallel routing toggle and individual node sign-off."""
    # 1. Toggle routing mode to PARALLEL
    toggle_resp = client.post("/api/approvals/toggle-routing-mode", json={"mode": "PARALLEL"})
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["routing_mode"] == "PARALLEL"

    # 2. Sign off IT node for DOS-2026-001
    sign_resp = client.post("/api/approvals/node-sign", json={
        "dossier_id": "DOS-2026-001",
        "node_key": "IT",
        "approver_name": "Alex Tan (IT Lead)",
        "role": "IT_APPROVER",
        "action": "CLEARED",
        "notes": "ThinkPad surrendered to HQ reception desk"
    })
    assert sign_resp.status_code == 200
    data = sign_resp.json()
    assert data["status"] == "SUCCESS"
    assert data["dossier"]["nodes"]["IT"]["status"] == "CLEARED"
    # In DOS-2026-001, ADMIN and FINANCE are also CLEARED, so all_dept_cleared should become True and unlock HR!
    assert data["all_dept_cleared"] is True
    assert data["dossier"]["nodes"]["HR"]["status"] == "READY"


def test_sla_timeout_auto_forward(client):
    """Verifies Option 2: SLA 48h timeout simulation and auto-forwarding to OIC."""
    resp = client.post("/api/approvals/simulate-timeout-forward", json={
        "dossier_id": "DOS-2026-002",
        "current_role": "FINANCE_APPROVER",
        "timeout_hours": 48,
        "new_assignee": "Carlo Mendoza (Designated OIC / Peer Lead)"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "AUTO_FORWARDED"
    assert data["new_assignee"] == "Carlo Mendoza (Designated OIC / Peer Lead)"


def test_split_escrow_disbursement(client):
    """Verifies Option 3: Split clearance and escrow release for disputed amounts."""
    resp = client.post("/api/approvals/split-escrow", json={
        "dossier_id": "DOS-2026-002",
        "undisputed_amount": 48500.00,
        "escrow_amount": 3500.00,
        "escrow_reason": "Disputed adapter deduction: Quitclaim stated amount (₱52,000) vs Computed Final Pay (₱48,500)",
        "approver_name": "Roberto Ong (Finance Lead)",
        "role": "FINANCE_APPROVER"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SPLIT_DISBURSED"
    assert data["undisputed_amount"] == 48500.00
    assert data["escrow_amount"] == 3500.00

    # Verify audit log was recorded
    logs_resp = client.get("/api/audit-logs?limit=5")
    assert logs_resp.status_code == 200
    actions = [l.get("action") for l in logs_resp.json()]
    assert "SPLIT_ESCROW_DISBURSEMENT" in actions


def test_transaction_comments(client):
    """Verifies Centralized Transaction Discussion thread posting and audit logging."""
    # Approver post
    resp = client.post("/api/approvals/transaction-comment", json={
        "dossier_id": "DOS-2026-001",
        "author": "Alex Tan (IT Clearance Lead)",
        "role": "IT_APPROVER",
        "message": "Lenovo ThinkPad T14s serial verified (20WM-0045PH). Charger missing, applied ₱1,200 deduction."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["comment"]["author"] == "Alex Tan (IT Clearance Lead)"
    assert "20WM-0045PH" in data["comment"]["text"]
    assert len(data["comments"]) >= 1

    # Requester post
    resp_req = client.post("/api/approvals/transaction-comment", json={
        "dossier_id": "DOS-2026-001",
        "author": "Juan Dela Cruz",
        "role": "REQUESTER",
        "message": "Acknowledging charger deduction from final pay computation."
    })
    assert resp_req.status_code == 200
    data_req = resp_req.json()
    assert data_req["status"] == "SUCCESS"
    assert data_req["comment"]["role"] == "REQUESTER"

    # Unauthorized party rejection (403 Forbidden)
    resp_unauth = client.post("/api/approvals/transaction-comment", json={
        "dossier_id": "DOS-2026-001",
        "author": "Unrelated Employee",
        "role": "EXTERNAL_STAFF",
        "message": "Trying to view or post on someone else's clearance."
    })
    assert resp_unauth.status_code == 403

    # Verify audit log was recorded
    logs_resp = client.get("/api/audit-logs?limit=5")
    assert logs_resp.status_code == 200
    actions = [l.get("action") for l in logs_resp.json()]
    assert "TRANSACTION_COMMENT_POSTED" in actions


def test_approval_metrics_endpoint(client):
    """Verifies Executive Clearance Dashboard KPI metrics endpoint with 15 tester accounts."""
    resp = client.get("/api/approvals/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_requests" in data
    assert "pending" in data
    assert "action_needed" in data
    assert "ready_for_release" in data
    assert data["total_requests"] == 15
    assert data["pending"] == 5
    assert data["action_needed"] == 5
    assert data["ready_for_release"] == 5
    assert data["avg_sla_days"] == 4.2


def test_dossiers_have_timeline_and_comments(client):
    """Verifies all 15 tester accounts are partitioned into 5 pending, 5 for review, and 5 for release."""
    resp = client.get("/api/clearance/dossiers")
    assert resp.status_code == 200
    dossiers = resp.json()
    assert len(dossiers) >= 4

    for d in dossiers:
        assert "timeline" in d
        assert len(d["timeline"]) >= 1
        m = d["timeline"][0]
        assert "milestone" in m
        assert "status" in m
        assert "details" in m
        assert "comments" in d

