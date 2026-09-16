# Clearance & Last Pay Web App — Multi-Agent Build README
*One-time kickoff document for an agentic AI coding assistant*

**Version:** 1.0 · **Last updated:** 2026-09-18
**Companion doc:** `spec-driven-development.md` (this README assumes that playbook is loaded alongside it — see §0)

---

## 0. How to use this document

This is the single document to paste into your agentic coding tool (Claude Code, Cursor, etc.) at the start of the build. It assumes the **Spec-Driven Development Playbook** is also loaded in the same session — everything here maps onto that playbook's phases and rules rather than replacing them.

Structure of what follows:
- §1–2: what we're building and how the work is split across **3 sub-agents in one chat**
- §3: the constitution (non-negotiables) all three agents inherit
- §4: what actually gets built first — a **local test run**, before anything touches Lark
- §5–6: the full build sequence after the local test passes
- §7: open items that still block the full build
- §8: literal kickoff prompt to paste to the orchestrator

---

## 1. Objective (recap)

Build a companion web app — embedded in Lark Workplace alongside the existing "Clearance and Last Pay Approval" flow, not replacing it — that removes manual investigation/re-keying work and speeds up approver decisions, as part of getting the process from its current 10–20 days down toward a realistic 5–7 day target (see prior conversation for the full time-savings breakdown; §7 below carries forward the still-unverified assumptions behind that number).

**Guardrail that overrides everything else:** the AI never auto-approves a clearance or last-pay release decision. It pre-checks, extracts, flags, and summarizes. A human always makes the actual approve/reject call.

---

## 2. Operating model — 3 sub-agents, one chat

Rather than one agent doing backend → frontend → AI pipeline sequentially, split into three sub-agents that can work in parallel once the shared contract (§2.2) is fixed.

### 2.1 The three agents

**Agent A — Backend / Integration**
- Owns: Lark OAuth, Approval API (read/write), Bitable schema, webhook receiver, event subscriptions
- Stack: Python + FastAPI, `lark-oapi` SDK
- Does NOT touch: React components, extraction prompt design

**Agent B — Frontend**
- Owns: requester submission form, approver review dashboard, (optional) natural-language status widget, Lark Web SDK embed/SSO handling
- Stack: React + TypeScript
- Does NOT touch: Lark API calls directly — talks only to Agent A's API, per the interface contract

**Agent C — AI / Document Pipeline**
- Owns: OCR + Claude API extraction of quit claims, bank details, clearance attachments; pre-check/flagging logic; prompt design and validation
- Does NOT touch: the Approval API or the UI — outputs structured JSON that Agent A's backend consumes

### 2.2 Coordination rules (binding on all three agents)

1. All three inherit one shared `constitution.md` (§3 below — copy it in verbatim as Phase 0).
2. All three treat one shared `interface-contract.md` as ground truth: API endpoints, request/response shapes, Bitable field names, webhook payloads, and the JSON shape Agent C outputs to Agent A. This file is created once, during Phase 2–3, before any agent starts implementation.
3. **No agent edits the interface contract silently.** Per the playbook's spec-fidelity rule, a proposed change to `interface-contract.md` stops for a checkpoint and gets logged in that file's Change Log — it is not treated as "just a small tweak while I was in there."
4. Each agent keeps its own `/specs/00X-*` folder for its own requirements/design/tasks, but Phase 1–2 (Intake, Requirements) for the first milestone (§4) is done once and shared, since backend, frontend, and AI pipeline requirements for that milestone overlap heavily.
5. Agents proceed to their own Task Breakdown and Implementation Loop **in parallel** once Requirements + Design for a milestone are approved — but only on tasks marked `[parallel-safe]`. Anything one agent needs from another (e.g., Agent B needs a real endpoint from Agent A, not a mock) is called out as a dependency in that task's `tasks.md` entry, per the playbook's task template.
6. Default operating mode for all three agents: **checkpoint mode**. This touches payroll-adjacent data — don't run any agent autonomous by default (playbook §6 already flags this as a case where checkpoint mode is expected).

---

## 3. Constitution — non-negotiables (Phase 0, shared)

Copy this into `/specs/constitution.md` before any agent starts.

```markdown
# Project Constitution — Clearance & Last Pay Web App

## Stack & Conventions
- Backend: Python + FastAPI, lark-oapi SDK
- Frontend: React + TypeScript, Lark Web SDK for embed/SSO
- Database: Lark Bitable (primary); fall back to Postgres only if volume/complexity
  outgrows Bitable's API limits — this decision needs explicit sign-off, not a
  silent switch by an agent
- AI: Claude API for document extraction/pre-check logic

## Testing Philosophy
- Every extraction rule and every API endpoint gets a test before it's considered done
- The document-extraction pipeline (Agent C) is tested against a fixed local sample
  set (§4.2) before any live document touches it

## Non-Negotiables
- AI NEVER auto-approves a clearance or last-pay release decision. Human approval
  is the only mechanism that finalizes a step.
- Every AI pre-check and every human override is audit-logged (who, what, when,
  what the AI flagged, what the human decided).
- RBAC is enforced at the API layer (Agent A), not just hidden in the UI (Agent B)
  — a role that shouldn't see a field shouldn't receive it in the API response.
- No real secrets, tokens, or credentials in code, commits, logs, or chat — ever,
  including in test fixtures.
- The existing Lark Approval flow is never torn down or bypassed. This app reads/
  writes to the same Approval instances via API; it does not create a parallel
  approval path.

## Style Guide
- Backend: follow FastAPI + Pydantic idioms, type-annotate everything
- Frontend: functional components + hooks, no class components
- Shared: interface-contract.md is the single source of truth for any cross-agent
  data shape — do not infer a shape from another agent's code if the contract
  doesn't cover it; stop and ask instead
```

---

## 4. First milestone: local test run (no Lark connection yet)

Lark Developer Console registration and API scopes are not yet confirmed (see §7). Rather than blocking the whole build on that, prove out the **riskiest and most novel** part of Track B first, entirely locally: can the AI pipeline actually extract and pre-check the documents reliably enough to trust as a pre-check?

### 4.1 Scope of this milestone

- **Agent C only** for the actual build. Agent A and Agent B can start their own Phase 1–2 (Requirements/Design) in parallel, but their implementation work for this milestone is limited to a local mock harness, not real Lark calls.
- No Lark OAuth, no Approval API, no webhooks, no RBAC dashboard yet. Those come in §5–6.

### 4.2 What "local test run of documents" means concretely

1. Assemble 3–5 representative sample documents — anonymized or synthetic versions of:
   - a quit claim form
   - a bank details / e-wallet enrollment form (scanned or photographed, matching real conditions)
   - a department clearance sign-off sheet
2. Build a small local script or minimal local-only web page (not embedded in Lark) that:
   - accepts an uploaded document
   - runs OCR / document parsing
   - calls the Claude API to extract structured fields and flag anything ambiguous or missing
   - outputs structured JSON: extracted fields, a confidence indicator per field, and explicit flags for anything the pipeline is unsure about (never a silent guess)
3. Log every extraction result locally (this becomes the seed of the audit-logging requirement in §3 once it's wired to the real app).

### 4.3 Success criteria for this milestone

- The pipeline correctly extracts the specific fields you actually need pre-checked (e.g., bank account number format and presence, quit claim amount, signature presence/absence) at an accuracy you're willing to trust as a *pre-check* — not a final decision.
- When the pipeline is unsure, it flags rather than guesses. A flagged-but-wrong result is fine; a confident-and-wrong result is not.
- This milestone does **not** need to be perfect before moving to §5 — it needs to be good enough to justify building the integration around it, with known failure modes written down.

### 4.4 Requirements for this milestone (Phase 2, EARS notation)

Have Agent C draft `requirements.md` for this milestone using the playbook's EARS table before writing any extraction code. At minimum it should cover:

| ID | Requirement |
|---|---|
| FR-1 | WHEN a document is uploaded, THE pipeline SHALL attempt extraction of the fields defined in the interface contract for that document type. |
| FR-2 | IF the pipeline's confidence for a field is below the agreed threshold, THEN THE pipeline SHALL flag that field rather than returning an unflagged value. |
| FR-3 | THE pipeline SHALL NOT return a decision (approve/reject/pass/fail) — only extracted fields and flags. |
| FR-4 | THE pipeline SHALL log every extraction attempt, its inputs (document type, not raw sensitive content beyond what's needed), and its outputs for later audit. |

---

## 5. Full build sequence (after the local test run passes)

1. **Local doc-extraction validation** (Agent C) — §4, above.
2. **Lark Developer Console registration** — human/orchestrator task, not an agent task. Needs scopes confirmed first (§7).
3. **Backend build** (Agent A) — Approval API read/write, Bitable schema, webhook receiver. Can start Design/Task Breakdown in parallel with step 1; implementation against real Lark credentials waits on step 2.
4. **Frontend build** (Agent B) — submission form + approver dashboard shell, built against the interface contract with Agent A's endpoints mocked. Can start in parallel with steps 1 and 3.
5. **Integration pass** — wire Agent A + B + C together, only after each has proven out independently against the shared contract. This is a checkpoint-mode milestone regardless of what mode individual agents used before.
6. **SLA / escalation logic + status-node automation** (courier/bank/e-wallet APIs) — last, since it depends on Open Item confirmation in §7.

---

## 6. What NOT to do

- Don't let any agent start writing implementation code before its Requirements + Design are marked Approved (trivial fixes excepted, per playbook rule A.1).
- Don't let Agent B call Lark APIs directly — everything routes through Agent A, so RBAC and audit logging stay centralized.
- Don't let Agent C's extraction output be treated as a decision anywhere downstream — if you ever see code that auto-sets an approval status from Agent C's output without a human action in between, that's a constitution violation, stop and flag it.
- Don't skip the local test run (§4) to "save time" by going straight to Lark integration — the extraction pipeline's real-world reliability is the biggest unknown in Track B, and it's the one piece you can validate without needing Lark credentials at all.

---

## 7. Open items still blocking the full build (carried forward)

1. Node-by-node classification of the existing flowchart (full-automation vs. AI-assisted vs. human-only) — not yet done.
2. Whether courier tracking, bank transfer, and e-wallet systems actually expose callable APIs — assumed, not verified.
3. HRIS system and whether it exposes an API for auto-pulling Unit/Channel/Job Level/bank details at submission — not confirmed.
4. Whether Clearance → Last Pay can be partially parallelized (Last Pay Computation starting before 100% of Clearance completes) — this is a policy question for whoever owns the clearance process, not a technical one, and it's the single biggest lever on total turnaround time.
5. Formal Lark scopes/app registration — blocked on confirming which of the above integrations are actually happening.

None of these block §4 (the local test run). All of them block §5 steps 2–6.

---

## 8. Kickoff prompt — paste this to the orchestrator

```
New multi-agent build: Clearance & Last Pay companion web app for Lark.

Load spec-driven-development.md as the working process and
clearance-last-pay-webapp-readme.md (this file) as the project brief.

Spin up 3 sub-agents per README §2:
  - Agent A: Backend/Integration
  - Agent B: Frontend
  - Agent C: AI/Document Pipeline

All three inherit constitution.md (README §3). Create interface-contract.md
before any implementation starts.

Start with Agent C only. Phase 1 — Intake & Clarify for the local
document-extraction test run described in README §4. Ask me anything
ambiguous about the sample documents or extraction fields before drafting
requirements.md. Checkpoint mode.

Agents A and B: begin your own Phase 1 in parallel, scoped to design only —
no implementation until the interface contract exists and Agent C's local
test run has a result.
```
