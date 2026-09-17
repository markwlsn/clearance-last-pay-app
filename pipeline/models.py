"""Pydantic data models matching specs/interface-contract.md."""
from __future__ import annotations

from enum import Enum
from typing import Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    QUIT_CLAIM = "QUIT_CLAIM"
    BANK_ENROLLMENT = "BANK_ENROLLMENT"
    CLEARANCE_SHEET = "CLEARANCE_SHEET"


class FlagSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


class FlagCode(str, Enum):
    FLAG_LOW_CONFIDENCE = "FLAG_LOW_CONFIDENCE"
    FLAG_MISSING_FIELD = "FLAG_MISSING_FIELD"
    FLAG_FORMAT_MISMATCH = "FLAG_FORMAT_MISMATCH"
    FLAG_SIGNATURE_ABSENT = "FLAG_SIGNATURE_ABSENT"
    FLAG_AMOUNT_MISMATCH = "FLAG_AMOUNT_MISMATCH"
    FLAG_NAME_MISMATCH = "FLAG_NAME_MISMATCH"
    FLAG_ACCOUNTABILITY_NOTED = "FLAG_ACCOUNTABILITY_NOTED"
    FLAG_IMAGE_BLURRY = "FLAG_IMAGE_BLURRY"


class FinancialInstitution(str, Enum):
    BDO = "BDO"
    BPI = "BPI"
    METROBANK = "METROBANK"
    UNIONBANK = "UNIONBANK"
    GCASH = "GCASH"
    MAYA = "MAYA"
    OTHER = "OTHER"


T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[T] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_flagged: bool = False

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence score {v} must be between 0.0 and 1.0")
        return round(v, 4)


class ExtractionFlag(BaseModel):
    code: FlagCode
    field_name: str
    severity: FlagSeverity
    message: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class DocumentAuditMetadata(BaseModel):
    document_id: str
    file_name: str
    file_hash_sha256: str
    mime_type: str
    processed_at: str  # ISO 8601 UTC
    model_id: str
    processing_time_ms: int


# --- 1. Quit Claim Models ---

class QuitClaimFields(BaseModel):
    employee_name: ExtractedField[str]
    employee_id: ExtractedField[str]
    separation_date: ExtractedField[str]  # YYYY-MM-DD
    settlement_amount_figures: ExtractedField[float]
    settlement_amount_words: ExtractedField[str]
    amounts_match: ExtractedField[bool]
    employee_signature_present: ExtractedField[bool]
    witness_signature_present: ExtractedField[bool]
    notary_present: ExtractedField[bool]
    waiver_clauses_intact: ExtractedField[bool]


class QuitClaimExtractionResult(BaseModel):
    document_type: DocumentType = DocumentType.QUIT_CLAIM
    metadata: DocumentAuditMetadata
    fields: QuitClaimFields
    flags: List[ExtractionFlag] = Field(default_factory=list)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)


# --- 2. Bank / E-Wallet Models ---

class BankEnrollmentFields(BaseModel):
    account_holder_name: ExtractedField[str]
    institution: ExtractedField[str]  # e.g. BDO, BPI, GCASH, MAYA
    account_number: ExtractedField[str]
    account_number_format_valid: ExtractedField[bool]
    qr_code_detected: ExtractedField[bool]
    proof_type: ExtractedField[str]  # PASSBOOK, DEPOSIT_SLIP, SCREENSHOT, etc.
    proof_legible: ExtractedField[bool]


class BankEnrollmentExtractionResult(BaseModel):
    document_type: DocumentType = DocumentType.BANK_ENROLLMENT
    metadata: DocumentAuditMetadata
    fields: BankEnrollmentFields
    flags: List[ExtractionFlag] = Field(default_factory=list)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)


# --- 3. Clearance Sheet Models ---

class DepartmentClearanceStatus(BaseModel):
    department: str
    is_cleared: ExtractedField[bool]
    approver_name: ExtractedField[str]
    signature_present: ExtractedField[bool]
    sign_date: ExtractedField[str]  # YYYY-MM-DD
    has_outstanding_accountability: ExtractedField[bool]
    accountability_notes: ExtractedField[str]


class ClearanceSheetFields(BaseModel):
    employee_name: ExtractedField[str]
    employee_id: ExtractedField[str]
    department_statuses: List[DepartmentClearanceStatus]
    all_departments_cleared: ExtractedField[bool]


class ClearanceSheetExtractionResult(BaseModel):
    document_type: DocumentType = DocumentType.CLEARANCE_SHEET
    metadata: DocumentAuditMetadata
    fields: ClearanceSheetFields
    flags: List[ExtractionFlag] = Field(default_factory=list)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)


ExtractionResult = Union[
    QuitClaimExtractionResult,
    BankEnrollmentExtractionResult,
    ClearanceSheetExtractionResult,
]
