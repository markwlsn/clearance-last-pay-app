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

# progressive refinement step
