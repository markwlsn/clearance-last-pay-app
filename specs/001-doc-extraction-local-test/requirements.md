# Requirements: Local Document-Extraction Test Run

**Spec ID:** 001-doc-extraction-local-test
**Status:** In Review
**Author:** Agent C (AI / Document Pipeline)
**Approved by / date:** Pending Orchestrator / User Sign-Off · 2026-09-18
**Traces to:** `clearance-last-pay-webapp-readme.md` §4, `specs/constitution.md`

---

## 1. Problem Statement

Manual investigation and re-keying of documents (Quit Claims, Bank/E-Wallet enrollments, Department Clearance sign-offs) in the current Clearance and Last Pay workflow causes 10–20 days of turnaround time. Approvers spend substantial time manually verifying whether signatures are present, account numbers match bank standards, and settlement amounts in words match numbers.

We need an automated document pre-check pipeline that extracts fields, flags discrepancies, and presents structured findings to human approvers *without ever making an automated approval decision*.

---

## 2. Goals

1. Ingest PDF and image documents locally (offline mock or Claude API).
2. Extract all mandatory fields defined in `specs/interface-contract.md` §2 for:
   - Quit Claim
   - Bank / E-Wallet Enrollment
   - Department Clearance Sheet
3. Pre-check fields against format rules, signature presence, and numerical/text consistency.
4. Flag any missing fields, format mismatches, and low-confidence extractions (`confidence < 0.80`).
5. Guarantee zero auto-approvals: output contains only extractions, confidences, and flags.
6. Record every extraction attempt in an append-only structured audit log (`audit_log.jsonl`).
7. Provide a CLI runner and local web test harness (`localhost:8000`) for manual verification.

---

## 3. Non-Goals

1. No Lark OAuth, Approval API, or webhook integration in this milestone (deferred to Milestone 2 / Agent A).
2. No live production HRIS or banking API verification in this milestone.
3. No final approve/reject decisions by AI (strictly prohibited by Constitution).

---

## 4. User Stories

- **As an Approver**, I want all key fields pre-extracted and any discrepancies (e.g., missing signature, illegible account number, amount mismatch) flagged with high visibility so I can make confident approval decisions in minutes instead of manual cross-referencing.
- **As an Auditor / Compliance Officer**, I want every automated extraction and flag to be immutably logged with document hash, model metadata, and timestamp so we maintain complete auditability.
- **As a Developer**, I want to run the pipeline locally against synthetic test documents with or without a Claude API key so the test suite can execute deterministically.

---

## 5. Functional Requirements (EARS)

| ID | Requirement (EARS Pattern) |
|---|---|
| **FR-1** | **WHEN** a document is uploaded, **THE** pipeline **SHALL** attempt extraction of the fields defined in `specs/interface-contract.md` §2 for that document type. |
| **FR-2** | **IF** the pipeline's confidence score for any field is below `0.80`, **THEN THE** pipeline **SHALL** flag that field with `FLAG_LOW_CONFIDENCE` rather than returning an unflagged guess. |
| **FR-3** | **THE** pipeline **SHALL NOT** return a decision (approve/reject/pass/fail) under any circumstances — only extracted fields, confidence scores, and flags. |
| **FR-4** | **THE** pipeline **SHALL** log every extraction attempt to an append-only JSONL audit log including document hash, document type, fields, flags, timestamp, and model metadata. |
| **FR-5** | **WHEN** a Quit Claim document is processed, **THE** pipeline **SHALL** verify whether `settlement_amount_figures` matches `settlement_amount_words`, and **IF** they mismatch, **THEN THE** pipeline **SHALL** raise `FLAG_AMOUNT_MISMATCH`. |
| **FR-6** | **WHEN** a Quit Claim document is processed, **IF** employee signature is undetected or confidence is `< 0.80`, **THEN THE** pipeline **SHALL** raise `FLAG_SIGNATURE_ABSENT`. |
| **FR-7** | **WHEN** a Bank/E-Wallet Enrollment is processed, **THE** pipeline **SHALL** validate the account or mobile number format against the standard institution patterns, and **IF** invalid, **THEN THE** pipeline **SHALL** raise `FLAG_FORMAT_MISMATCH`. |
| **FR-8** | **WHEN** a Department Clearance Sheet is processed, **IF** any department is uncleared, has missing signature, or has outstanding liabilities, **THEN THE** pipeline **SHALL** raise `FLAG_MISSING_FIELD` or `FLAG_ACCOUNTABILITY_NOTED`. |
| **FR-9** | **IF** an uploaded file is illegible, corrupted, or unparseable, **THEN THE** pipeline **SHALL** raise `FLAG_IMAGE_BLURRY` or return a structured extraction error without crashing. |
| **FR-10** | **WHERE** `ANTHROPIC_API_KEY` is not present in environment or `.env`, **THE** pipeline **SHALL** fall back to a deterministic mock extraction engine to facilitate offline development and automated testing. |

---

## 6. Non-Functional Requirements

- **NFR-1 (Latency)**: Extraction processing time under local mock `< 100ms`; under live Claude API `< 5000ms`.
- **NFR-2 (Determinism)**: Given identical mock input documents, extraction output JSON must be 100% reproducible.
- **NFR-3 (Privacy)**: Raw file data is not stored in plain text inside git or chat; audit logs store document hashes and sanitized metadata.

---

## 7. Edge Cases & Error States

- **EC-1**: File upload is not a valid PDF or supported image format (`.png`, `.jpg`, `.jpeg`). Handled with clear `400 Bad Request` or validation error.
- **EC-2**: Hand-written text on photographed phone screenshot with partial glare. Handled with `FLAG_LOW_CONFIDENCE` on illegible fields.
- **EC-3**: Currency symbol mismatch (e.g. PHP vs USD). Handled with normalized numeric value and currency flag if unexpected.

---

## 8. Open Questions

- None blocking this milestone (all clarified in Phase 1 Intake).

---

## Change Log

| Date | Change | Reason |
|---|---|---|
| 2026-09-18 | Initial requirements drafted for Milestone 1 | Conforming to SDD Phase 2 |
