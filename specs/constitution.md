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
