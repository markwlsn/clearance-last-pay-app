"""Unit tests for the pre-check & flagging engine."""
import pytest
from pipeline.models import (
    DocumentType,
    FlagCode,
    FlagSeverity,
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
from pipeline.flagger import PreCheckFlagger, validate_bank_account_format


def test_bank_format_validator():
    # GCash: 11 digits starting with 09
    assert validate_bank_account_format("GCASH", "09171234567") is True
    assert validate_bank_account_format("GCASH", "0917-123-4567") is True
    assert validate_bank_account_format("GCASH", "12345") is False
    assert validate_bank_account_format("GCASH", "08171234567") is False

    # Maya: 11 digits starting with 09
    assert validate_bank_account_format("MAYA", "09289876543") is True
    assert validate_bank_account_format("MAYA", "0928987") is False

    # BPI: 10 digits
    assert validate_bank_account_format("BPI", "1234567890") is True
    assert validate_bank_account_format("BPI", "12345") is False

    # BDO: 10 or 12 digits
    assert validate_bank_account_format("BDO", "1234567890") is True
    assert validate_bank_account_format("BDO", "123456789012") is True
    assert validate_bank_account_format("BDO", "1234567") is False


def test_flagger_quit_claim_clean():
    flagger = PreCheckFlagger(confidence_threshold=0.80)
    metadata = DocumentAuditMetadata(
        document_id="doc-1",
        file_name="clean_qc.pdf",
        file_hash_sha256="hash123",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:00:00Z",
        model_id="mock-v1",
        processing_time_ms=50,
    )
    fields = QuitClaimFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Pedro Penduko", normalized_value="Pedro Penduko", confidence=0.95),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-001", normalized_value="EMP-001", confidence=0.95),
        separation_date=ExtractedField(field_name="separation_date", raw_value="2026-09-01", normalized_value="2026-09-01", confidence=0.95),
        settlement_amount_figures=ExtractedField(field_name="settlement_amount_figures", raw_value="45000", normalized_value=45000.0, confidence=0.95),
        settlement_amount_words=ExtractedField(field_name="settlement_amount_words", raw_value="Forty Five Thousand", normalized_value="Forty Five Thousand", confidence=0.95),
        amounts_match=ExtractedField(field_name="amounts_match", raw_value="true", normalized_value=True, confidence=0.95),
        employee_signature_present=ExtractedField(field_name="employee_signature_present", raw_value="true", normalized_value=True, confidence=0.90),
        witness_signature_present=ExtractedField(field_name="witness_signature_present", raw_value="true", normalized_value=True, confidence=0.90),
        notary_present=ExtractedField(field_name="notary_present", raw_value="true", normalized_value=True, confidence=0.90),
        waiver_clauses_intact=ExtractedField(field_name="waiver_clauses_intact", raw_value="true", normalized_value=True, confidence=0.95),
    )
    result = QuitClaimExtractionResult(
        metadata=metadata,
        fields=fields,
        overall_confidence=0.94,
    )

    flags = flagger.evaluate(result)
    assert len(flags) == 0


def test_flagger_quit_claim_mismatches_and_missing_sig():
    flagger = PreCheckFlagger(confidence_threshold=0.80)
    metadata = DocumentAuditMetadata(
        document_id="doc-2",
        file_name="bad_qc.pdf",
        file_hash_sha256="hash456",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:00:00Z",
        model_id="mock-v1",
        processing_time_ms=50,
    )
    fields = QuitClaimFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Pedro Penduko", normalized_value="Pedro Penduko", confidence=0.95),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-001", normalized_value="EMP-001", confidence=0.95),
        separation_date=ExtractedField(field_name="separation_date", raw_value="2026-09-01", normalized_value="2026-09-01", confidence=0.95),
        settlement_amount_figures=ExtractedField(field_name="settlement_amount_figures", raw_value="45000", normalized_value=45000.0, confidence=0.95),
        settlement_amount_words=ExtractedField(field_name="settlement_amount_words", raw_value="Fifty Thousand", normalized_value="Fifty Thousand", confidence=0.95),
        amounts_match=ExtractedField(field_name="amounts_match", raw_value="false", normalized_value=False, confidence=0.95),
        employee_signature_present=ExtractedField(field_name="employee_signature_present", raw_value="false", normalized_value=False, confidence=0.90),
        witness_signature_present=ExtractedField(field_name="witness_signature_present", raw_value="true", normalized_value=True, confidence=0.90),
        notary_present=ExtractedField(field_name="notary_present", raw_value="false", normalized_value=False, confidence=0.70),  # Low confidence
        waiver_clauses_intact=ExtractedField(field_name="waiver_clauses_intact", raw_value="true", normalized_value=True, confidence=0.95),
    )
    result = QuitClaimExtractionResult(
        metadata=metadata,
        fields=fields,
        overall_confidence=0.85,
    )

    flags = flagger.evaluate(result)
    flag_codes = [f.code for f in flags]

    assert FlagCode.FLAG_AMOUNT_MISMATCH in flag_codes
    assert FlagCode.FLAG_SIGNATURE_ABSENT in flag_codes
    assert FlagCode.FLAG_LOW_CONFIDENCE in flag_codes


def test_flagger_bank_enrollment_format_error():
    flagger = PreCheckFlagger(confidence_threshold=0.80)
    metadata = DocumentAuditMetadata(
        document_id="doc-bank-err",
        file_name="gcash_bad.jpg",
        file_hash_sha256="hash789",
        mime_type="image/jpeg",
        processed_at="2026-09-18T10:00:00Z",
        model_id="mock-v1",
        processing_time_ms=50,
    )
    fields = BankEnrollmentFields(
        account_holder_name=ExtractedField(field_name="account_holder_name", raw_value="Juan", normalized_value="Juan", confidence=0.95),
        institution=ExtractedField(field_name="institution", raw_value="GCash", normalized_value="GCASH", confidence=0.95),
        account_number=ExtractedField(field_name="account_number", raw_value="091712", normalized_value="091712", confidence=0.95),  # Truncated
        account_number_format_valid=ExtractedField(field_name="account_number_format_valid", raw_value="false", normalized_value=False, confidence=1.0),
        qr_code_detected=ExtractedField(field_name="qr_code_detected", raw_value="false", normalized_value=False, confidence=0.90),
        proof_type=ExtractedField(field_name="proof_type", raw_value="screenshot", normalized_value="SCREENSHOT", confidence=0.90),
        proof_legible=ExtractedField(field_name="proof_legible", raw_value="true", normalized_value=True, confidence=0.90),
    )
    result = BankEnrollmentExtractionResult(
        metadata=metadata,
        fields=fields,
        overall_confidence=0.92,
    )

    flags = flagger.evaluate(result)
    flag_codes = [f.code for f in flags]
    assert FlagCode.FLAG_FORMAT_MISMATCH in flag_codes


def test_flagger_clearance_sheet_accountability_and_missing_dept():
    flagger = PreCheckFlagger(confidence_threshold=0.80)
    metadata = DocumentAuditMetadata(
        document_id="doc-clr-err",
        file_name="clearance_pending.pdf",
        file_hash_sha256="hash101",
        mime_type="application/pdf",
        processed_at="2026-09-18T10:00:00Z",
        model_id="mock-v1",
        processing_time_ms=50,
    )
    dept_statuses = [
        DepartmentClearanceStatus(
            department="IT",
            is_cleared=ExtractedField(field_name="IT_is_cleared", raw_value="Pending", normalized_value=False, confidence=0.95),
            approver_name=ExtractedField(field_name="IT_approver", raw_value="", normalized_value="", confidence=0.90),
            signature_present=ExtractedField(field_name="IT_signature", raw_value="false", normalized_value=False, confidence=0.95),
            sign_date=ExtractedField(field_name="IT_date", raw_value="", normalized_value="", confidence=0.90),
            has_outstanding_accountability=ExtractedField(field_name="IT_accountability", raw_value="true", normalized_value=True, confidence=0.95),
            accountability_notes=ExtractedField(field_name="IT_notes", raw_value="Unreturned ThinkPad T14 laptop", normalized_value="Unreturned ThinkPad T14 laptop", confidence=0.95),
        )
    ]
    fields = ClearanceSheetFields(
        employee_name=ExtractedField(field_name="employee_name", raw_value="Juan Dela Cruz", normalized_value="Juan Dela Cruz", confidence=0.95),
        employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-001", normalized_value="EMP-001", confidence=0.95),
        department_statuses=dept_statuses,
        all_departments_cleared=ExtractedField(field_name="all_departments_cleared", raw_value="false", normalized_value=False, confidence=0.95),
    )
    result = ClearanceSheetExtractionResult(
        metadata=metadata,
        fields=fields,
        overall_confidence=0.94,
    )

    flags = flagger.evaluate(result)
    flag_codes = [f.code for f in flags]
    assert FlagCode.FLAG_ACCOUNTABILITY_NOTED in flag_codes
    assert FlagCode.FLAG_MISSING_FIELD in flag_codes
