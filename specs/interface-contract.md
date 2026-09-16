# Interface Contract — Clearance & Last Pay Companion Web App
*The single source of truth for cross-agent contracts, schemas, and endpoints*

**Version:** 0.1.0 (Draft) · **Date:** 2026-09-18
**Applies to:** Agent A (Backend), Agent B (Frontend), Agent C (AI/Document Pipeline)

---

## 1. Overview & Governance Rules

1. **Strict Spec Fidelity**: No agent may modify this file without a dated entry in the [Change Log](#change-log) and orchestrator approval.
2. **Never Infer**: If a field shape, enum, or endpoint is not defined here, agents must NOT guess or infer from other agents' code — stop and ask.
3. **No Auto-Approve**: No data shape in this contract shall represent an AI "Approval" or "Final Decision". The AI pipeline returns only `extractions`, `confidences`, and `flags`.

---

## 2. Agent C — Document Extraction Schema (Output)

Agent C processes uploaded files and outputs structured JSON conforming to the following Pydantic / TypeScript types.

### 2.1 Common Extraction Types

```typescript
export type DocumentType = 
  | "QUIT_CLAIM"
  | "BANK_ENROLLMENT"
  | "CLEARANCE_SHEET";

export type FlagSeverity = "INFO" | "WARNING" | "BLOCKER";

export type FlagCode =
  | "FLAG_LOW_CONFIDENCE"
  | "FLAG_MISSING_FIELD"
  | "FLAG_FORMAT_MISMATCH"
  | "FLAG_SIGNATURE_ABSENT"
  | "FLAG_AMOUNT_MISMATCH"
  | "FLAG_NAME_MISMATCH"
  | "FLAG_ACCOUNTABILITY_NOTED"
  | "FLAG_IMAGE_BLURRY";

export interface ExtractionFlag {
  code: FlagCode;
  field_name: string;
  severity: FlagSeverity;
  message: string;
  confidence: number; // 0.0 - 1.0
}

export interface ExtractedField<T = string | number | boolean> {
  field_name: string;
  raw_value: string | null;
  normalized_value: T | null;
  confidence: number; // 0.0 - 1.0 (threshold: < 0.80 triggers flag)
  is_flagged: boolean;
}

export interface DocumentAuditMetadata {
  document_id: string;
  file_name: string;
  file_hash_sha256: string;
  mime_type: string;
  processed_at: string; // ISO 8601 UTC
  model_id: string;
  processing_time_ms: number;
}
```

### 2.2 Quit Claim Extraction Payload (`QUIT_CLAIM`)

```typescript
export interface QuitClaimFields {
  employee_name: ExtractedField<string>;
  employee_id: ExtractedField<string>;
  separation_date: ExtractedField<string>; // YYYY-MM-DD
  settlement_amount_figures: ExtractedField<number>;
  settlement_amount_words: ExtractedField<string>;
  amounts_match: ExtractedField<boolean>;
  employee_signature_present: ExtractedField<boolean>;
  witness_signature_present: ExtractedField<boolean>;
  notary_present: ExtractedField<boolean>;
  waiver_clauses_intact: ExtractedField<boolean>;
}

export interface QuitClaimExtractionResult {
  document_type: "QUIT_CLAIM";
  metadata: DocumentAuditMetadata;
  fields: QuitClaimFields;
  flags: ExtractionFlag[];
  overall_confidence: number;
}
```

### 2.3 Bank / E-Wallet Enrollment Payload (`BANK_ENROLLMENT`)

```typescript
export type FinancialInstitution = 
  | "BDO"
  | "BPI"
  | "METROBANK"
  | "UNIONBANK"
  | "GCASH"
  | "MAYA"
  | "OTHER";

export interface BankEnrollmentFields {
  account_holder_name: ExtractedField<string>;
  institution: ExtractedField<FinancialInstitution>;
  account_number: ExtractedField<string>;
  account_number_format_valid: ExtractedField<boolean>;
  qr_code_detected: ExtractedField<boolean>;
  proof_type: ExtractedField<"PASSBOOK" | "DEPOSIT_SLIP" | "SCREENSHOT" | "BANK_CERTIFICATE" | "UNKNOWN">;
  proof_legible: ExtractedField<boolean>;
}

export interface BankEnrollmentExtractionResult {
  document_type: "BANK_ENROLLMENT";
  metadata: DocumentAuditMetadata;
  fields: BankEnrollmentFields;
  flags: ExtractionFlag[];
  overall_confidence: number;
}
```

### 2.4 Department Clearance Sign-Off Payload (`CLEARANCE_SHEET`)

```typescript
export type ClearanceDept = "IT" | "ADMIN" | "FINANCE" | "HR" | "IMMEDIATE_SUPERVISOR";

export interface DepartmentClearanceStatus {
  department: ClearanceDept;
  is_cleared: ExtractedField<boolean>;
  approver_name: ExtractedField<string>;
  signature_present: ExtractedField<boolean>;
  sign_date: ExtractedField<string>; // YYYY-MM-DD
  has_outstanding_accountability: ExtractedField<boolean>;
  accountability_notes: ExtractedField<string>;
}

export interface ClearanceSheetFields {
  employee_name: ExtractedField<string>;
  employee_id: ExtractedField<string>;
  department_statuses: DepartmentClearanceStatus[];
  all_departments_cleared: ExtractedField<boolean>;
}

export interface ClearanceSheetExtractionResult {
  document_type: "CLEARANCE_SHEET";
  metadata: DocumentAuditMetadata;
  fields: ClearanceSheetFields;
  flags: ExtractionFlag[];
  overall_confidence: number;
}
```

---

## 3. Agent A — Backend REST API Specifications

All endpoints require standard Bearer token authentication (Lark User OAuth or Service Token) and enforce strict RBAC.

### 3.1 Endpoints

#### `POST /api/v1/documents/precheck`
Directly calls Agent C pipeline to pre-check an uploaded document before submission.
- **Request**: `multipart/form-data` with `file: UploadFile`, `document_type: DocumentType`
- **Response**: `200 OK` with `QuitClaimExtractionResult | BankEnrollmentExtractionResult | ClearanceSheetExtractionResult`

#### `POST /api/v1/clearance/submissions`
Creates or updates a clearance dossier with pre-checked documents.
- **Request Body**:
```json
{
  "employee_id": "EMP-94812",
  "employee_name": "Juan Dela Cruz",
  "separation_date": "2026-09-30",
  "attached_documents": [
    {
      "document_id": "doc-uuid-1",
      "document_type": "QUIT_CLAIM",
      "file_url": "lark-drive-token",
      "precheck_result": { "..." : "..." }
    }
  ]
}
```
- **Response**: `201 Created` with `dossier_id: string`, `lark_approval_instance_id: string`

#### `GET /api/v1/clearance/dossiers/{id}`
Returns complete clearance dossier, including AI pre-check summaries and current approval state.
- **RBAC**: Requester can view own; Approvers can view assigned; Admins view all. Sensitive bank fields masked unless role = `FINANCE_APPROVER` or `PAYROLL_ADMIN`.

#### `POST /api/v1/clearance/approvals/{id}/action`
Approver takes explicit human action (Approve, Reject, Request Clarification).
- **Request Body**:
```json
{
  "action": "APPROVE" | "REJECT" | "REQUEST_REVISION",
  "comments": "Verified quit claim signature matches signature card.",
  "flags_reviewed": ["FLAG_AMOUNT_MISMATCH"],
  "override_justification": "Discrepancy of 50 centavos due to tax rounding."
}
```
- **Response**: `200 OK`, emits audit log and updates Lark Approval instance.

---

## 4. Bitable & Database Schema

Primary store: Lark Bitable.

### Table: `clearance_dossiers`
| Field Name | Type | Notes |
|---|---|---|
| `dossier_id` | Text (Primary) | Internal UUID |
| `employee_id` | Text | HRIS Employee ID |
| `employee_name` | Text | Full Name |
| `lark_approval_id` | Text | Lark Approval Instance ID |
| `stage` | SingleSelect | Clearance, Last Pay Calc, Final Release, Closed |
| `overall_status` | SingleSelect | Pending, In Review, Needs Revision, Approved, Rejected |
| `ai_flags_count` | Number | Count of active pre-check flags |
| `created_at` | DateTime | Timestamp |
| `updated_at` | DateTime | Timestamp |

### Table: `document_extractions_audit`
| Field Name | Type | Notes |
|---|---|---|
| `audit_id` | Text (Primary) | UUID |
| `dossier_id` | Text | Link to dossier |
| `document_type` | SingleSelect | QUIT_CLAIM, BANK_ENROLLMENT, CLEARANCE_SHEET |
| `file_hash` | Text | SHA-256 hash |
| `ai_confidence` | Number | 0.0 - 1.0 |
| `flags_detected` | MultiSelect | List of flag codes |
| `raw_extraction_json` | Text | Complete structured JSON payload |
| `logged_at` | DateTime | ISO Timestamp |

### Table: `human_decisions_audit`
| Field Name | Type | Notes |
|---|---|---|
| `decision_id` | Text (Primary) | UUID |
| `dossier_id` | Text | Link to dossier |
| `approver_lark_id` | Text | Lark open_id of human approver |
| `role` | SingleSelect | HR, IT, Finance, Admin, Executive |
| `action` | SingleSelect | APPROVE, REJECT, REQUEST_REVISION |
| `override_notes` | Text | Rationale if overriding an AI flag |
| `decided_at` | DateTime | Timestamp |

---

## Change Log

| Date | Author | Version | Description |
|---|---|---|---|
| 2026-09-18 | System Architect | 0.1.0 | Initial cross-agent interface contract created for Milestone 1. |
