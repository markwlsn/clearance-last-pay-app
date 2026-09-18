"""Unit tests for the document extraction engine."""
import pytest
from pipeline.models import DocumentType, FlagCode
from pipeline.extractor import (
    DeterministicMockExtractor,
    get_extractor,
)


def test_mock_extractor_quit_claim_clean():
    extractor = DeterministicMockExtractor()
    result = extractor.extract(
        file_bytes=b"dummy_bytes",
        file_name="quit_claim_valid.pdf",
        doc_type=DocumentType.QUIT_CLAIM,
    )

    assert result.document_type == DocumentType.QUIT_CLAIM
    assert result.fields.employee_name.raw_value == "Juan Dela Cruz"
    assert result.fields.amounts_match.normalized_value is True
    assert result.fields.employee_signature_present.normalized_value is True
    assert len(result.flags) == 0


def test_mock_extractor_quit_claim_amount_mismatch():
    extractor = DeterministicMockExtractor()
    result = extractor.extract(
        file_bytes=b"dummy_bytes",
        file_name="quit_claim_mismatch.pdf",
        doc_type=DocumentType.QUIT_CLAIM,
    )

    assert result.document_type == DocumentType.QUIT_CLAIM
    assert result.fields.amounts_match.normalized_value is False
    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_AMOUNT_MISMATCH in flag_codes


def test_mock_extractor_bank_enrollment_invalid_format():
    extractor = DeterministicMockExtractor()
    result = extractor.extract(
        file_bytes=b"dummy_bytes",
        file_name="bank_bad_format.png",
        doc_type=DocumentType.BANK_ENROLLMENT,
    )

    assert result.document_type == DocumentType.BANK_ENROLLMENT
    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_FORMAT_MISMATCH in flag_codes


def test_mock_extractor_clearance_sheet_missing_dept():
    extractor = DeterministicMockExtractor()
    result = extractor.extract(
        file_bytes=b"dummy_bytes",
        file_name="clearance_missing_it.pdf",
        doc_type=DocumentType.CLEARANCE_SHEET,
    )

    assert result.document_type == DocumentType.CLEARANCE_SHEET
    flag_codes = [f.code for f in result.flags]
    assert FlagCode.FLAG_MISSING_FIELD in flag_codes or FlagCode.FLAG_ACCOUNTABILITY_NOTED in flag_codes


def test_get_extractor_fallback_to_mock():
    # Without API key, get_extractor returns DeterministicMockExtractor
    extractor = get_extractor(api_key=None, force_mock=False)
    assert isinstance(extractor, DeterministicMockExtractor)
