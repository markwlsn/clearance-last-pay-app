"""Document extraction engine supporting Claude API and deterministic mock provider."""
import base64
import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline.audit import compute_bytes_sha256
from pipeline.flagger import PreCheckFlagger
from pipeline.models import (
    BankEnrollmentFields,
    BankEnrollmentExtractionResult,
    ClearanceSheetFields,
    ClearanceSheetExtractionResult,
    DepartmentClearanceStatus,
    DocumentAuditMetadata,
    DocumentType,
    ExtractedField,
    ExtractionResult,
    FinancialInstitution,
    QuitClaimFields,
    QuitClaimExtractionResult,
)


class BaseExtractor(ABC):
    """Base document extractor contract."""

    def __init__(self, flagger: Optional[PreCheckFlagger] = None):
        self.flagger = flagger or PreCheckFlagger()

    @abstractmethod
    def extract(
        self,
        file_bytes: bytes,
        file_name: str,
        doc_type: DocumentType,
        mime_type: str = "application/pdf",
    ) -> ExtractionResult:
        """Extract structured fields and evaluate flags from document."""
        pass


class DeterministicMockExtractor(BaseExtractor):
    """High-fidelity mock extractor returning deterministic results for testing."""

    def extract(
        self,
        file_bytes: bytes,
        file_name: str,
        doc_type: DocumentType,
        mime_type: str = "application/pdf",
    ) -> ExtractionResult:
        start_time = time.time()
        file_hash = compute_bytes_sha256(file_bytes) if file_bytes else "mock_sha256_hash"
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"
        fn_lower = file_name.lower()

        metadata = DocumentAuditMetadata(
            document_id=doc_id,
            file_name=file_name,
            file_hash_sha256=file_hash,
            mime_type=mime_type,
            processed_at=datetime.now(timezone.utc).isoformat(),
            model_id="mock-deterministic-v1",
            processing_time_ms=int((time.time() - start_time) * 1000) + 25,
        )

        if doc_type == DocumentType.QUIT_CLAIM:
            result = self._extract_mock_quit_claim(fn_lower, metadata)
        elif doc_type == DocumentType.BANK_ENROLLMENT:
            result = self._extract_mock_bank_enrollment(fn_lower, metadata)
        elif doc_type == DocumentType.CLEARANCE_SHEET:
            result = self._extract_mock_clearance_sheet(fn_lower, metadata)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

        # Run through flagging engine
        self.flagger.evaluate(result)
        return result

    def _extract_mock_quit_claim(self, fn: str, metadata: DocumentAuditMetadata) -> QuitClaimExtractionResult:
        is_mismatch = "mismatch" in fn
        is_missing_sig = "missing_sig" in fn or "unsigned" in fn or "mismatch" in fn
        is_low_conf = "low_conf" in fn or "blurry" in fn

        if is_mismatch:
            figures = 48500.00
            figures_raw = "48,500.00"
            words = "Fifty Eight Thousand Five Hundred Pesos"
            amounts_match = False
        else:
            figures = 52400.00
            figures_raw = "52,400.00"
            words = "Fifty Two Thousand Four Hundred Pesos"
            amounts_match = True

        sig_present = not is_missing_sig
        conf = 0.65 if is_low_conf else 0.95

        fields = QuitClaimFields(
            employee_name=ExtractedField(field_name="employee_name", raw_value="Juan Dela Cruz", normalized_value="Juan Dela Cruz", confidence=conf),
            employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-94812", normalized_value="EMP-94812", confidence=conf),
            separation_date=ExtractedField(field_name="separation_date", raw_value="2026-08-31", normalized_value="2026-08-31", confidence=conf),
            settlement_amount_figures=ExtractedField(field_name="settlement_amount_figures", raw_value=figures_raw, normalized_value=figures, confidence=conf),
            settlement_amount_words=ExtractedField(field_name="settlement_amount_words", raw_value=words, normalized_value=words, confidence=conf),
            amounts_match=ExtractedField(field_name="amounts_match", raw_value=str(amounts_match).lower(), normalized_value=amounts_match, confidence=conf),
            employee_signature_present=ExtractedField(field_name="employee_signature_present", raw_value="true" if sig_present else "false", normalized_value=sig_present, confidence=conf),
            witness_signature_present=ExtractedField(field_name="witness_signature_present", raw_value="true", normalized_value=True, confidence=conf),
            notary_present=ExtractedField(field_name="notary_present", raw_value="true", normalized_value=True, confidence=conf),
            waiver_clauses_intact=ExtractedField(field_name="waiver_clauses_intact", raw_value="true", normalized_value=True, confidence=conf),
        )

        return QuitClaimExtractionResult(
            document_type=DocumentType.QUIT_CLAIM,
            metadata=metadata,
            fields=fields,
            overall_confidence=conf,
        )

    def _extract_mock_bank_enrollment(self, fn: str, metadata: DocumentAuditMetadata) -> BankEnrollmentExtractionResult:
        is_bad_format = "bad_format" in fn or "invalid" in fn
        is_blurry = "blurry" in fn

        inst = "GCASH"
        acc_num = "091712" if is_bad_format else "09179876543"
        conf = 0.60 if is_blurry else 0.96

        fields = BankEnrollmentFields(
            account_holder_name=ExtractedField(field_name="account_holder_name", raw_value="Juan Dela Cruz", normalized_value="Juan Dela Cruz", confidence=conf),
            institution=ExtractedField(field_name="institution", raw_value=inst, normalized_value=inst, confidence=0.98),
            account_number=ExtractedField(field_name="account_number", raw_value=acc_num, normalized_value=acc_num, confidence=conf),
            account_number_format_valid=ExtractedField(field_name="account_number_format_valid", raw_value=str(not is_bad_format).lower(), normalized_value=not is_bad_format, confidence=1.0),
            qr_code_detected=ExtractedField(field_name="qr_code_detected", raw_value="true", normalized_value=True, confidence=0.92),
            proof_type=ExtractedField(field_name="proof_type", raw_value="SCREENSHOT", normalized_value="SCREENSHOT", confidence=0.95),
            proof_legible=ExtractedField(field_name="proof_legible", raw_value=str(not is_blurry).lower(), normalized_value=not is_blurry, confidence=conf),
        )

        return BankEnrollmentExtractionResult(
            document_type=DocumentType.BANK_ENROLLMENT,
            metadata=metadata,
            fields=fields,
            overall_confidence=conf,
        )

    def _extract_mock_clearance_sheet(self, fn: str, metadata: DocumentAuditMetadata) -> ClearanceSheetExtractionResult:
        has_it_hold = "missing_it" in fn or "it_hold" in fn or "accountability" in fn
        conf = 0.94

        dept_statuses = [
            DepartmentClearanceStatus(
                department="IT",
                is_cleared=ExtractedField(field_name="IT_is_cleared", raw_value="Cleared" if not has_it_hold else "Pending", normalized_value=not has_it_hold, confidence=conf),
                approver_name=ExtractedField(field_name="IT_approver", raw_value="Alex Tan" if not has_it_hold else "", normalized_value="Alex Tan" if not has_it_hold else "", confidence=conf),
                signature_present=ExtractedField(field_name="IT_signature", raw_value="true" if not has_it_hold else "false", normalized_value=not has_it_hold, confidence=conf),
                sign_date=ExtractedField(field_name="IT_date", raw_value="2026-09-02" if not has_it_hold else "", normalized_value="2026-09-02" if not has_it_hold else "", confidence=conf),
                has_outstanding_accountability=ExtractedField(field_name="IT_accountability", raw_value="true" if has_it_hold else "false", normalized_value=has_it_hold, confidence=conf),
                accountability_notes=ExtractedField(field_name="IT_notes", raw_value="Unreturned ThinkPad T14 & Monitor" if has_it_hold else "", normalized_value="Unreturned ThinkPad T14 & Monitor" if has_it_hold else "", confidence=conf),
            ),
            DepartmentClearanceStatus(
                department="ADMIN",
                is_cleared=ExtractedField(field_name="ADMIN_is_cleared", raw_value="Cleared", normalized_value=True, confidence=conf),
                approver_name=ExtractedField(field_name="ADMIN_approver", raw_value="Elena Cruz", normalized_value="Elena Cruz", confidence=conf),
                signature_present=ExtractedField(field_name="ADMIN_signature", raw_value="true", normalized_value=True, confidence=conf),
                sign_date=ExtractedField(field_name="ADMIN_date", raw_value="2026-09-02", normalized_value="2026-09-02", confidence=conf),
                has_outstanding_accountability=ExtractedField(field_name="ADMIN_accountability", raw_value="false", normalized_value=False, confidence=conf),
                accountability_notes=ExtractedField(field_name="ADMIN_notes", raw_value="", normalized_value="", confidence=conf),
            ),
            DepartmentClearanceStatus(
                department="FINANCE",
                is_cleared=ExtractedField(field_name="FINANCE_is_cleared", raw_value="Cleared", normalized_value=True, confidence=conf),
                approver_name=ExtractedField(field_name="FINANCE_approver", raw_value="Roberto Ong", normalized_value="Roberto Ong", confidence=conf),
                signature_present=ExtractedField(field_name="FINANCE_signature", raw_value="true", normalized_value=True, confidence=conf),
                sign_date=ExtractedField(field_name="FINANCE_date", raw_value="2026-09-03", normalized_value="2026-09-03", confidence=conf),
                has_outstanding_accountability=ExtractedField(field_name="FINANCE_accountability", raw_value="false", normalized_value=False, confidence=conf),
                accountability_notes=ExtractedField(field_name="FINANCE_notes", raw_value="", normalized_value="", confidence=conf),
            ),
            DepartmentClearanceStatus(
                department="HR",
                is_cleared=ExtractedField(field_name="HR_is_cleared", raw_value="Cleared", normalized_value=True, confidence=conf),
                approver_name=ExtractedField(field_name="HR_approver", raw_value="Grace Diaz", normalized_value="Grace Diaz", confidence=conf),
                signature_present=ExtractedField(field_name="HR_signature", raw_value="true", normalized_value=True, confidence=conf),
                sign_date=ExtractedField(field_name="HR_date", raw_value="2026-09-04", normalized_value="2026-09-04", confidence=conf),
                has_outstanding_accountability=ExtractedField(field_name="HR_accountability", raw_value="false", normalized_value=False, confidence=conf),
                accountability_notes=ExtractedField(field_name="HR_notes", raw_value="", normalized_value="", confidence=conf),
            ),
        ]

        all_cleared = not has_it_hold

        fields = ClearanceSheetFields(
            employee_name=ExtractedField(field_name="employee_name", raw_value="Juan Dela Cruz", normalized_value="Juan Dela Cruz", confidence=conf),
            employee_id=ExtractedField(field_name="employee_id", raw_value="EMP-94812", normalized_value="EMP-94812", confidence=conf),
            department_statuses=dept_statuses,
            all_departments_cleared=ExtractedField(field_name="all_departments_cleared", raw_value=str(all_cleared).lower(), normalized_value=all_cleared, confidence=conf),
        )

        return ClearanceSheetExtractionResult(
            document_type=DocumentType.CLEARANCE_SHEET,
            metadata=metadata,
            fields=fields,
            overall_confidence=conf,
        )


class ClaudeDocumentExtractor(BaseExtractor):
    """Live Claude API vision/document extractor."""

    def __init__(self, api_key: str, flagger: Optional[PreCheckFlagger] = None):
        super().__init__(flagger=flagger)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_id = "claude-3-5-sonnet-20241022"

    def extract(
        self,
        file_bytes: bytes,
        file_name: str,
        doc_type: DocumentType,
        mime_type: str = "application/pdf",
    ) -> ExtractionResult:
        start_time = time.time()
        file_hash = compute_bytes_sha256(file_bytes)
        doc_id = f"doc-{uuid.uuid4().hex[:8]}"

        # Prepare base64
        b64_data = base64.b64encode(file_bytes).decode("utf-8")

        prompt = self._build_prompt(doc_type)

        content_blocks = []
        if mime_type == "application/pdf":
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64_data,
                },
            })
        else:
            # Assume image
            img_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/webp", "image/gif"] else "image/png"
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img_type,
                    "data": b64_data,
                },
            })

        content_blocks.append({"type": "text", "text": prompt})

        # Call Claude API
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=2048,
            messages=[{"role": "user", "content": content_blocks}],
        )

        response_text = response.content[0].text
        # Strip potential markdown backticks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        parsed_json = json.loads(response_text.strip())

        metadata = DocumentAuditMetadata(
            document_id=doc_id,
            file_name=file_name,
            file_hash_sha256=file_hash,
            mime_type=mime_type,
            processed_at=datetime.now(timezone.utc).isoformat(),
            model_id=self.model_id,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

        if doc_type == DocumentType.QUIT_CLAIM:
            result = QuitClaimExtractionResult(
                metadata=metadata,
                fields=QuitClaimFields.model_validate(parsed_json["fields"]),
                overall_confidence=parsed_json.get("overall_confidence", 0.90),
            )
        elif doc_type == DocumentType.BANK_ENROLLMENT:
            result = BankEnrollmentExtractionResult(
                metadata=metadata,
                fields=BankEnrollmentFields.model_validate(parsed_json["fields"]),
                overall_confidence=parsed_json.get("overall_confidence", 0.90),
            )
        elif doc_type == DocumentType.CLEARANCE_SHEET:
            result = ClearanceSheetExtractionResult(
                metadata=metadata,
                fields=ClearanceSheetFields.model_validate(parsed_json["fields"]),
                overall_confidence=parsed_json.get("overall_confidence", 0.90),
            )
        else:
            raise ValueError(f"Unknown document type: {doc_type}")

        self.flagger.evaluate(result)
        return result

    def _build_prompt(self, doc_type: DocumentType) -> str:
        base = (
            "You are an AI document extractor for HR clearance and payroll pre-checks. "
            "Extract all requested fields with their raw string value, normalized typed value, "
            "and a confidence score between 0.0 and 1.0. "
            "NEVER make an approval/rejection decision. Output ONLY raw valid JSON adhering to the schema.\n\n"
        )
        if doc_type == DocumentType.QUIT_CLAIM:
            return base + (
                "Extract Quit Claim fields into JSON format:\n"
                "{\n"
                '  "fields": {\n'
                '    "employee_name": {"field_name": "employee_name", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "employee_id": {"field_name": "employee_id", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "separation_date": {"field_name": "separation_date", "raw_value": str, "normalized_value": "YYYY-MM-DD", "confidence": float},\n'
                '    "settlement_amount_figures": {"field_name": "settlement_amount_figures", "raw_value": str, "normalized_value": float, "confidence": float},\n'
                '    "settlement_amount_words": {"field_name": "settlement_amount_words", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "amounts_match": {"field_name": "amounts_match", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "employee_signature_present": {"field_name": "employee_signature_present", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "witness_signature_present": {"field_name": "witness_signature_present", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "notary_present": {"field_name": "notary_present", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "waiver_clauses_intact": {"field_name": "waiver_clauses_intact", "raw_value": str, "normalized_value": bool, "confidence": float}\n'
                '  },\n'
                '  "overall_confidence": float\n'
                "}"
            )
        elif doc_type == DocumentType.BANK_ENROLLMENT:
            return base + (
                "Extract Bank / E-Wallet Enrollment fields into JSON format:\n"
                "{\n"
                '  "fields": {\n'
                '    "account_holder_name": {"field_name": "account_holder_name", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "institution": {"field_name": "institution", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "account_number": {"field_name": "account_number", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "account_number_format_valid": {"field_name": "account_number_format_valid", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "qr_code_detected": {"field_name": "qr_code_detected", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '    "proof_type": {"field_name": "proof_type", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "proof_legible": {"field_name": "proof_legible", "raw_value": str, "normalized_value": bool, "confidence": float}\n'
                '  },\n'
                '  "overall_confidence": float\n'
                "}"
            )
        elif doc_type == DocumentType.CLEARANCE_SHEET:
            return base + (
                "Extract Department Clearance Sheet fields into JSON format:\n"
                "{\n"
                '  "fields": {\n'
                '    "employee_name": {"field_name": "employee_name", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "employee_id": {"field_name": "employee_id", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '    "department_statuses": [\n'
                '      {\n'
                '        "department": "IT",\n'
                '        "is_cleared": {"field_name": "IT_is_cleared", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '        "approver_name": {"field_name": "IT_approver", "raw_value": str, "normalized_value": str, "confidence": float},\n'
                '        "signature_present": {"field_name": "IT_signature", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '        "sign_date": {"field_name": "IT_date", "raw_value": str, "normalized_value": "YYYY-MM-DD", "confidence": float},\n'
                '        "has_outstanding_accountability": {"field_name": "IT_accountability", "raw_value": str, "normalized_value": bool, "confidence": float},\n'
                '        "accountability_notes": {"field_name": "IT_notes", "raw_value": str, "normalized_value": str, "confidence": float}\n'
                '      }\n'
                '    ],\n'
                '    "all_departments_cleared": {"field_name": "all_departments_cleared", "raw_value": str, "normalized_value": bool, "confidence": float}\n'
                '  },\n'
                '  "overall_confidence": float\n'
                "}"
            )
        return base


def get_extractor(api_key: Optional[str] = None, force_mock: bool = False) -> BaseExtractor:
    """Factory creating the appropriate extractor based on environment and config."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    mock_mode = force_mock or os.environ.get("MOCK_EXTRACTION_MODE", "").lower() in ("true", "1")

    if not key or mock_mode:
        return DeterministicMockExtractor()
    return ClaudeDocumentExtractor(api_key=key)
