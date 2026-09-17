"""Unit tests for the append-only structured audit logger."""
import json
import os
import tempfile
from pathlib import Path
from pipeline.models import (
    DocumentType,
    ExtractedField,
    DocumentAuditMetadata,
    QuitClaimFields,
    QuitClaimExtractionResult,
    ExtractionFlag,
    FlagCode,
    FlagSeverity,
)
from pipeline.audit import AuditLogger, compute_file_sha256


def test_compute_file_sha256(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"hello world")
    # sha256 for "hello world" is b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
    assert compute_file_sha256(str(test_file)) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_audit_logger_append_only(tmp_path):
    log_path = tmp_path / "audit_log.jsonl"
    logger = AuditLogger(log_path=str(log_path))

    metadata = DocumentAuditMetadata(
        document_id="doc-qc-01",
        file_name="sample.pdf",
        file_hash_sha256="hash111",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:00:00Z",
        model_id="mock-v1",
        processing_time_ms=75,
    )

    fields = QuitClaimFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Juan", normalized_value="Juan", confidence=0.9),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-1", normalized_value="EMP-1", confidence=0.9),
        separation_date=ExtractedField(field_name="separation_date", raw_value="2026-09-01", normalized_value="2026-09-01", confidence=0.9),
        settlement_amount_figures=ExtractedField(field_name="settlement_amount_figures", raw_value="1000", normalized_value=1000.0, confidence=0.9),
        settlement_amount_words=ExtractedField(field_name="settlement_amount_words", raw_value="One Thousand", normalized_value="One Thousand", confidence=0.9),
        amounts_match=ExtractedField(field_name="amounts_match", raw_value="true", normalized_value=True, confidence=0.9),
        employee_signature_present=ExtractedField(field_name="employee_signature_present", raw_value="true", normalized_value=True, confidence=0.9),
        witness_signature_present=ExtractedField(field_name="witness_signature_present", raw_value="true", normalized_value=True, confidence=0.9),
        notary_present=ExtractedField(field_name="notary_present", raw_value="true", normalized_value=True, confidence=0.9),
        waiver_clauses_intact=ExtractedField(field_name="waiver_clauses_intact", raw_value="true", normalized_value=True, confidence=0.9),
    )

    result1 = QuitClaimExtractionResult(
        document_type=DocumentType.QUIT_CLAIM,
        metadata=metadata,
        fields=fields,
        flags=[ExtractionFlag(code=FlagCode.FLAG_LOW_CONFIDENCE, field_name="notary_present", severity=FlagSeverity.WARNING, message="Low confidence notary")],
        overall_confidence=0.9,
    )

    logger.log_extraction(result1, caller_id="test-agent")

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    entry1 = json.loads(lines[0])
    assert entry1["document_id"] == "doc-qc-01"
    assert entry1["caller_id"] == "test-agent"
    assert entry1["document_type"] == "QUIT_CLAIM"
    assert len(entry1["flags"]) == 1
    assert entry1["flags"][0]["code"] == "FLAG_LOW_CONFIDENCE"

    # Second log entry to verify append
    metadata2 = metadata.model_copy(update={"document_id": "doc-qc-02"})
    result2 = result1.model_copy(update={"metadata": metadata2})
    logger.log_extraction(result2, caller_id="test-agent-2")

    lines_after = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines_after) == 2
    assert json.loads(lines_after[1])["document_id"] == "doc-qc-02"

    # Query recent logs
    recent = logger.get_recent_logs(limit=10)
    assert len(recent) == 2
    assert recent[0]["document_id"] == "doc-qc-02"  # Reverse chronological
