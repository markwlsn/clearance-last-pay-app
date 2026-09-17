"""Unit tests for Pydantic data models conforming to specs/interface-contract.md."""
import pytest
from datetime import datetime
from pydantic import ValidationError

from pipeline.models import (
    DocumentType,
    FlagSeverity,
    FlagCode,
    ExtractionFlag,
    ExtractedField,
    DocumentAuditMetadata,
    QuitClaimFields,
    QuitClaimExtractionResult,
    BankEnrollmentFields,
    BankEnrollmentExtractionResult,
    DepartmentClearanceStatus,
    ClearanceSheetFields,
    ClearanceSheetExtractionResult,
)


def test_extracted_field_valid():
    field = ExtractedField[str](
        field_name="employee_name",
        raw_value="Juan Dela Cruz",
        normalized_value="Juan Dela Cruz",
        confidence=0.95,
        is_flagged=False,
    )
    assert field.confidence == 0.95
    assert not field.is_flagged
    assert field.normalized_value == "Juan Dela Cruz"


def test_extracted_field_confidence_bounds():
    with pytest.raises(ValidationError):
        ExtractedField[str](
            field_name="test",
            raw_value="val",
            normalized_value="val",
            confidence=1.5,  # Exceeds max 1.0
            is_flagged=False,
        )

    with pytest.raises(ValidationError):
        ExtractedField[str](
            field_name="test",
            raw_value="val",
            normalized_value="val",
            confidence=-0.1,  # Below min 0.0
            is_flagged=False,
        )


def test_flag_creation_and_severity():
    flag = ExtractionFlag(
        code=FlagCode.FLAG_AMOUNT_MISMATCH,
        field_name="settlement_amount_figures",
        severity=FlagSeverity.BLOCKER,
        message="Amount in figures does not match words",
        confidence=0.90,
    )
    assert flag.code == FlagCode.FLAG_AMOUNT_MISMATCH
    assert flag.severity == FlagSeverity.BLOCKER


def test_quit_claim_schema_serialization():
    metadata = DocumentAuditMetadata(
        document_id="doc-qc-001",
        file_name="quit_claim_sample.pdf",
        file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:00:00Z",
        model_id="claude-3-5-sonnet-20241022",
        processing_time_ms=1250,
    )

    fields = QuitClaimFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Maria Santos", normalized_value="Maria Santos", confidence=0.98, is_flagged=False),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-10294", normalized_value="EMP-10294", confidence=0.99, is_flagged=False),
        separation_date=ExtractedField(field_name="separation_date", raw_value="2026-08-31", normalized_value="2026-08-31", confidence=0.95, is_flagged=False),
        settlement_amount_figures=ExtractedField(field_name="settlement_amount_figures", raw_value="52,400.00", normalized_value=52400.00, confidence=0.96, is_flagged=False),
        settlement_amount_words=ExtractedField(field_name="settlement_amount_words", raw_value="Fifty Two Thousand Four Hundred Pesos", normalized_value="Fifty Two Thousand Four Hundred Pesos", confidence=0.92, is_flagged=False),
        amounts_match=ExtractedField(field_name="amounts_match", raw_value="true", normalized_value=True, confidence=0.95, is_flagged=False),
        employee_signature_present=ExtractedField(field_name="employee_signature_present", raw_value="present", normalized_value=True, confidence=0.89, is_flagged=False),
        witness_signature_present=ExtractedField(field_name="witness_signature_present", raw_value="present", normalized_value=True, confidence=0.88, is_flagged=False),
        notary_present=ExtractedField(field_name="notary_present", raw_value="present", normalized_value=True, confidence=0.91, is_flagged=False),
        waiver_clauses_intact=ExtractedField(field_name="waiver_clauses_intact", raw_value="intact", normalized_value=True, confidence=0.97, is_flagged=False),
    )

    qc_result = QuitClaimExtractionResult(
        document_type=DocumentType.QUIT_CLAIM,
        metadata=metadata,
        fields=fields,
        flags=[],
        overall_confidence=0.94,
    )

    json_str = qc_result.model_dump_json()
    assert "Maria Santos" in json_str
    assert "QUIT_CLAIM" in json_str

    restored = QuitClaimExtractionResult.model_validate_json(json_str)
    assert restored.fields.settlement_amount_figures.normalized_value == 52400.00
    assert restored.metadata.document_id == "doc-qc-001"


def test_bank_enrollment_schema():
    metadata = DocumentAuditMetadata(
        document_id="doc-bank-001",
        file_name="gcash_screenshot.jpg",
        file_hash_sha256="abc123hash",
        mime_type="image/jpeg",
        processed_at="2026-09-18T10:05:00Z",
        model_id="claude-3-5-sonnet-20241022",
        processing_time_ms=850,
    )

    fields = BankEnrollmentFields(
        account_holder_name=ExtractedField(field_name="account_holder_name", raw_value="JUAN DELA CRUZ", normalized_value="Juan Dela Cruz", confidence=0.95, is_flagged=False),
        institution=ExtractedField(field_name="institution", raw_value="GCash", normalized_value="GCASH", confidence=0.99, is_flagged=False),
        account_number=ExtractedField(field_name="account_number", raw_value="09171234567", normalized_value="09171234567", confidence=0.97, is_flagged=False),
        account_number_format_valid=ExtractedField(field_name="account_number_format_valid", raw_value="valid", normalized_value=True, confidence=1.0, is_flagged=False),
        qr_code_detected=ExtractedField(field_name="qr_code_detected", raw_value="false", normalized_value=False, confidence=0.90, is_flagged=False),
        proof_type=ExtractedField(field_name="proof_type", raw_value="screenshot", normalized_value="SCREENSHOT", confidence=0.95, is_flagged=False),
        proof_legible=ExtractedField(field_name="proof_legible", raw_value="true", normalized_value=True, confidence=0.92, is_flagged=False),
    )

    result = BankEnrollmentExtractionResult(
        document_type=DocumentType.BANK_ENROLLMENT,
        metadata=metadata,
        fields=fields,
        flags=[],
        overall_confidence=0.95,
    )

    assert result.fields.institution.normalized_value == "GCASH"
    assert result.fields.account_number.normalized_value == "09171234567"


def test_clearance_sheet_schema():
    metadata = DocumentAuditMetadata(
        document_id="doc-clr-001",
        file_name="clearance_sheet.pdf",
        file_hash_sha256="def456hash",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:10:00Z",
        model_id="claude-3-5-sonnet-20241022",
        processing_time_ms=1100,
    )

    dept_statuses = [
        DepartmentClearanceStatus(
            department="IT",
            is_cleared=ExtractedField(field_name="IT_is_cleared", raw_value="Cleared", normalized_value=True, confidence=0.95, is_flagged=False),
            approver_name=ExtractedField(field_name="IT_approver", raw_value="Alex Tan", normalized_value="Alex Tan", confidence=0.90, is_flagged=False),
            signature_present=ExtractedField(field_name="IT_signature", raw_value="Yes", normalized_value=True, confidence=0.88, is_flagged=False),
            sign_date=ExtractedField(field_name="IT_date", raw_value="2026-09-01", normalized_value="2026-09-01", confidence=0.92, is_flagged=False),
            has_outstanding_accountability=ExtractedField(field_name="IT_accountability", raw_value="None", normalized_value=False, confidence=0.95, is_flagged=False),
            accountability_notes=ExtractedField(field_name="IT_notes", raw_value="", normalized_value="", confidence=1.0, is_flagged=False),
        )
    ]

    fields = ClearanceSheetFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Juan Dela Cruz", normalized_value="Juan Dela Cruz", confidence=0.96, is_flagged=False),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-94812", normalized_value="EMP-94812", confidence=0.98, is_flagged=False),
        department_statuses=dept_statuses,
        all_departments_cleared=ExtractedField(field_name="all_departments_cleared", raw_value="true", normalized_value=True, confidence=0.95, is_flagged=False),
    )

    result = ClearanceSheetExtractionResult(
        document_type=DocumentType.CLEARANCE_SHEET,
        metadata=metadata,
        fields=fields,
        flags=[],
        overall_confidence=0.94,
    )

    assert result.fields.department_statuses[0].department == "IT"
    assert result.fields.department_statuses[0].is_cleared.normalized_value is True
