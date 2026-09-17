"""Pre-check and flagging engine for Clearance & Last Pay documents."""
import re
from typing import List, Optional
from pipeline.models import (
    DocumentType,
    FlagCode,
    FlagSeverity,
    ExtractionFlag,
    ExtractedField,
    ExtractionResult,
    QuitClaimExtractionResult,
    BankEnrollmentExtractionResult,
    ClearanceSheetExtractionResult,
)


def normalize_account_number(acc: str) -> str:
    """Strip spaces, dashes, and periods from account number."""
    if not acc:
        return ""
    return re.sub(r"[\s\-\.]", "", acc)


def validate_bank_account_format(institution: str, raw_account_number: str) -> bool:
    """Validates account number pattern against Philippine financial institution standards."""
    clean_acc = normalize_account_number(raw_account_number)
    if not clean_acc or not clean_acc.isdigit():
        return False

    inst = (institution or "").upper().strip()

    if "GCASH" in inst:
        return len(clean_acc) == 11 and clean_acc.startswith("09")
    elif "MAYA" in inst or "PAYMAYA" in inst:
        return len(clean_acc) == 11 and clean_acc.startswith("09")
    elif "BPI" in inst:
        return len(clean_acc) == 10
    elif "BDO" in inst:
        return len(clean_acc) in (10, 12)
    elif "METROBANK" in inst:
        return len(clean_acc) == 13
    elif "UNIONBANK" in inst:
        return len(clean_acc) == 12
    else:
        # Fallback for other banks: between 8 and 16 digits
        return 8 <= len(clean_acc) <= 16


class PreCheckFlagger:
    """Evaluates extracted document fields against verification rules and flags discrepancies."""

    def __init__(self, confidence_threshold: float = 0.80):
        self.confidence_threshold = confidence_threshold

    def evaluate(self, result: ExtractionResult) -> List[ExtractionFlag]:
        """Runs all applicable flagging rules, annotates fields, and returns detected flags."""
        flags: List[ExtractionFlag] = []

        if isinstance(result, QuitClaimExtractionResult):
            flags.extend(self._evaluate_quit_claim(result))
        elif isinstance(result, BankEnrollmentExtractionResult):
            flags.extend(self._evaluate_bank_enrollment(result))
        elif isinstance(result, ClearanceSheetExtractionResult):
            flags.extend(self._evaluate_clearance_sheet(result))

        # Attach flags to result
        result.flags = flags
        return flags

    def _check_field_confidence(self, field: ExtractedField, label: str) -> Optional[ExtractionFlag]:
        if field.confidence < self.confidence_threshold:
            field.is_flagged = True
            return ExtractionFlag(
                code=FlagCode.FLAG_LOW_CONFIDENCE,
                field_name=field.field_name,
                severity=FlagSeverity.WARNING,
                message=f"Confidence for {label} ({field.confidence:.2f}) is below threshold {self.confidence_threshold:.2f}",
                confidence=field.confidence,
            )
        return None

    def _evaluate_quit_claim(self, result: QuitClaimExtractionResult) -> List[ExtractionFlag]:
        flags: List[ExtractionFlag] = []
        fields = result.fields

        # 1. Confidence checks
        for field in (
            fields.employee_name,
            fields.employee_id,
            fields.separation_date,
            fields.settlement_amount_figures,
            fields.settlement_amount_words,
            fields.employee_signature_present,
            fields.notary_present,
        ):
            flag = self._check_field_confidence(field, field.field_name)
            if flag:
                flags.append(flag)

        # 2. Missing required fields
        if not fields.employee_name.raw_value:
            fields.employee_name.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_MISSING_FIELD,
                field_name="employee_name",
                severity=FlagSeverity.BLOCKER,
                message="Employee name is missing from Quit Claim",
            ))

        if not fields.employee_id.raw_value:
            fields.employee_id.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_MISSING_FIELD,
                field_name="employee_id",
                severity=FlagSeverity.BLOCKER,
                message="Employee ID is missing from Quit Claim",
            ))

        # 3. Amount consistency check
        if fields.amounts_match.normalized_value is False:
            fields.settlement_amount_figures.is_flagged = True
            fields.settlement_amount_words.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_AMOUNT_MISMATCH,
                field_name="settlement_amount_figures",
                severity=FlagSeverity.BLOCKER,
                message=(
                    f"Discrepancy detected: Settlement amount in figures ({fields.settlement_amount_figures.raw_value}) "
                    f"does not match words ({fields.settlement_amount_words.raw_value})"
                ),
            ))

        # 4. Signature presence check
        if not fields.employee_signature_present.normalized_value:
            fields.employee_signature_present.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_SIGNATURE_ABSENT,
                field_name="employee_signature_present",
                severity=FlagSeverity.BLOCKER,
                message="Employee signature is undetected or absent on the Quit Claim form",
            ))

        return flags

    def _evaluate_bank_enrollment(self, result: BankEnrollmentExtractionResult) -> List[ExtractionFlag]:
        flags: List[ExtractionFlag] = []
        fields = result.fields

        # 1. Confidence checks
        for field in (
            fields.account_holder_name,
            fields.institution,
            fields.account_number,
        ):
            flag = self._check_field_confidence(field, field.field_name)
            if flag:
                flags.append(flag)

        # 2. Account format check
        inst = fields.institution.raw_value or ""
        acc = fields.account_number.raw_value or ""
        is_valid_format = validate_bank_account_format(inst, acc)
        fields.account_number_format_valid.normalized_value = is_valid_format

        if not is_valid_format:
            fields.account_number.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_FORMAT_MISMATCH,
                field_name="account_number",
                severity=FlagSeverity.BLOCKER,
                message=(
                    f"Account number '{acc}' does not match the expected format for {inst}. "
                    "Please verify account number digits."
                ),
            ))

        # 3. Legibility check
        if fields.proof_legible.normalized_value is False:
            fields.proof_legible.is_flagged = True
            flags.append(ExtractionFlag(
                code=FlagCode.FLAG_IMAGE_BLURRY,
                field_name="proof_legible",
                severity=FlagSeverity.WARNING,
                message="Bank document proof is blurry, low-resolution, or partially occluded",
            ))

        return flags

    def _evaluate_clearance_sheet(self, result: ClearanceSheetExtractionResult) -> List[ExtractionFlag]:
        flags: List[ExtractionFlag] = []
        fields = result.fields

        for dept_status in fields.department_statuses:
            dept_name = dept_status.department

            # Check confidence
            flag = self._check_field_confidence(dept_status.is_cleared, f"{dept_name} clearance status")
            if flag:
                flags.append(flag)

            # Missing clearance or signature
            if not dept_status.is_cleared.normalized_value or not dept_status.signature_present.normalized_value:
                dept_status.is_cleared.is_flagged = True
                flags.append(ExtractionFlag(
                    code=FlagCode.FLAG_MISSING_FIELD,
                    field_name=f"{dept_name}_clearance",
                    severity=FlagSeverity.BLOCKER,
                    message=f"{dept_name} department has not completed clearance sign-off",
                ))

            # Outstanding accountabilities / deductions
            if dept_status.has_outstanding_accountability.normalized_value:
                dept_status.has_outstanding_accountability.is_flagged = True
                notes = dept_status.accountability_notes.normalized_value or "Outstanding accountability noted"
                flags.append(ExtractionFlag(
                    code=FlagCode.FLAG_ACCOUNTABILITY_NOTED,
                    field_name=f"{dept_name}_accountability",
                    severity=FlagSeverity.BLOCKER,
                    message=f"{dept_name} hold detected: {notes}",
                ))

        return flags
