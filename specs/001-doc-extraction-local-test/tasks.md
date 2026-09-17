# Tasks: Local Document-Extraction Test Run

**Spec ID:** 001-doc-extraction-local-test
**Derived from:** `specs/001-doc-extraction-local-test/requirements.md` v1.0, `design.md` v1.0

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked · `[parallel-safe]`

- [x] **T1** — Project environment setup & dependency scaffolding
  Refs: FR-10 · Design §2
  Acceptance: `requirements.txt`, `.env.example`, directory structure (`pipeline/`, `samples/`, `tests/`, `logs/`) initialized, dependencies installed cleanly in virtualenv or local environment.
  Depends on: none

- [x] **T2** — Implement Pydantic data models matching interface contract
  Refs: FR-1, FR-3 · Design §2.1
  Acceptance: `pipeline/models.py` validates all 3 document types; unit tests in `tests/test_schemas.py` pass cleanly.
  Depends on: T1

- [x] **T3** — Implement pre-check & flagging engine
  Refs: FR-2, FR-5, FR-6, FR-7, FR-8 · Design §2.2
  Acceptance: `pipeline/flagger.py` correctly detects missing fields, low confidence, format mismatches, amount discrepancies, and accountability notes; unit tests in `tests/test_flagger.py` pass.
  Depends on: T2

- [x] **T4** — Implement append-only structured audit logger
  Refs: FR-4 · Design §2.4
  Acceptance: `pipeline/audit.py` records every extraction attempt with SHA-256 file hash, model version, and flags into `logs/audit_log.jsonl`; unit tests in `tests/test_audit.py` pass.
  Depends on: T2

- [x] **T5** — Implement document extractor (Deterministic Mock + Claude API)
  Refs: FR-1, FR-9, FR-10 · Design §2.3
  Acceptance: `pipeline/extractor.py` handles PDF/image inputs, dispatches to Claude API or deterministic mock fallback; unit tests in `tests/test_extractor.py` pass.
  Depends on: T3, T4

- [x] **T6** — Assemble synthetic sample document suite
  Refs: FR-1 · Design §5
  Acceptance: 6 synthetic test fixtures created in `samples/` (valid + flawed for Quit Claim, Bank Enrollment, and Clearance Sheet).
  Depends on: T1

- [x] **T7** — Implement CLI runner and local web test harness
  Refs: FR-1, FR-3, FR-4 · Design §2.5
  Acceptance: `pipeline/local_harness.py` runs both in CLI mode and as a FastAPI local web dashboard on `http://localhost:8000`. End-to-end integration tests in `tests/test_pipeline_e2e.py` pass 100%.
  Depends on: T5, T6

---

## Discovered work
*(Noticed mid-implementation, out of scope — triage later, don't fold in silently)*
- None.
