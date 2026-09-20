"""Local test harness for Clearance & Last Pay document pre-check pipeline.
Supports:
1. Employee Submission View (Faithfully recreating the Lark Approval Form in Apple Minimalist style)
2. Role-Based Approver Desk (Ultra-refined Apple minimalist workstation with multi-doc tabs & SLA tracker)
3. Developer Quick-Test Harness with 1-click synthetic fixtures
4. Apple Minimalist aesthetic with default Light Mode and Dark Mode toggle
"""
import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.audit import AuditLogger
from pipeline.extractor import BaseExtractor, get_extractor
from pipeline.models import DocumentType, ExtractionResult

app = FastAPI(
    title="Clearance & Last Pay — Lark Companion App",
    description="Apple-minimalist Lark Clearance Form and Role-Based Approver Dashboard.",
    version="2.1.0",
)

# Shared singletons on app state
app.state.audit_logger = AuditLogger(log_path=os.environ.get("AUDIT_LOG_PATH", "logs/audit_log.jsonl"))
app.state.extractor = get_extractor()

# Mount static samples directory for direct serving and previews
samples_dir = Path(__file__).resolve().parent.parent / "samples"
if samples_dir.exists():
    app.mount("/samples", StaticFiles(directory=str(samples_dir)), name="samples")


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



class HumanActionRequest(BaseModel):
    document_id: str
    approver_id: str
    role: str
    action: str  # APPROVE, REJECT, REQUEST_REVISION
    flags_reviewed: List[str] = []
    override_justification: str = ""


class LarkNotificationRequest(BaseModel):
    dossier_id: str
    employee_name: str
    recipient: str
    message: str
    sender_role: str


class NudgeRequest(BaseModel):
    dossier_id: str
    target_role: str
    target_name: str
    sender_role: str
    reason: str


class TransactionCommentRequest(BaseModel):
    dossier_id: str
    author: str
    role: str
    message: str


class EscalateRequest(BaseModel):
    dossier_id: str
    employee_name: str
    escalate_to: str
    sender_role: str
    hours_idle: int


class NodeSignRequest(BaseModel):
    dossier_id: str
    node_key: str  # "IT", "ADMIN", "FINANCE", "HR"
    approver_name: str
    role: str
    action: str = "CLEARED"  # "CLEARED", "FLAGGED"
    notes: str = ""


class TimeoutForwardRequest(BaseModel):
    dossier_id: str
    current_role: str
    timeout_hours: int = 48
    new_assignee: str = "Carlo Mendoza (Designated OIC / Peer Lead)"


class SplitEscrowRequest(BaseModel):
    dossier_id: str
    undisputed_amount: float
    escrow_amount: float
    escrow_reason: str
    approver_name: str
    role: str = "FINANCE_APPROVER"


class RoutingModeRequest(BaseModel):
    mode: str  # "PARALLEL" or "SEQUENTIAL"


class SubmissionPayload(BaseModel):
    department: str
    employee_name: str
    date_hired: str
    job_level: str
    company: str
    unit_channel: str
    branch: str
    employee_status: str
    eoc_date: str
    with_clearance_already: str
    reason_for_separation: str
    accountability_form_name: Optional[str] = None
    accountability_precheck: Optional[Dict[str, Any]] = None
    id_form_name: Optional[str] = None
    id_precheck: Optional[Dict[str, Any]] = None


from pipeline.dossiers import get_initial_dossiers

# In-memory dossier store containing 15 seeded tester accounts
# (5 Pending, 5 For Review, 5 Ready for Release)
app.state.dossiers = get_initial_dossiers()


def run_cli_extraction(
    file_path: str,
    doc_type: DocumentType,
    extractor: Optional[BaseExtractor] = None,
    audit_logger: Optional[AuditLogger] = None,
) -> ExtractionResult:
    """Executes extraction on a single local file via CLI."""
    ext = extractor or app.state.extractor
    logger = audit_logger or app.state.audit_logger

    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_bytes = p.read_bytes()
    mime = "application/pdf" if p.suffix.lower() == ".pdf" else "image/png"

    result = ext.extract(
        file_bytes=file_bytes,
        file_name=p.name,
        doc_type=doc_type,
        mime_type=mime,
    )

    logger.log_extraction(result, caller_id="cli-runner")
    return result


@app.get("/api/samples")
def list_samples():
    """Lists available synthetic sample fixtures for easy 1-click testing."""
    if not samples_dir.exists():
        return []

    samples = []
    for f in samples_dir.iterdir():
        if f.name.startswith("."):
            continue
        doc_type = "QUIT_CLAIM"
        if "bank" in f.name:
            doc_type = "BANK_ENROLLMENT"
        elif "clearance" in f.name:
            doc_type = "CLEARANCE_SHEET"
        samples.append({
            "file_name": f.name,
            "document_type": doc_type,
            "size_bytes": f.stat().st_size,
            "url": f"/samples/{f.name}",
        })
    return sorted(samples, key=lambda x: x["file_name"])


@app.get("/api/clearance/dossiers")
def get_dossiers():
    """Returns active clearance dossiers for approver dashboards."""
    return app.state.dossiers


@app.post("/api/clearance/submit")
def submit_clearance_form(data: SubmissionPayload):
    """Handles submission of the Lark Clearance form."""
    dossier_id = f"DOS-2026-{uuid.uuid4().hex[:4].upper()}"
    new_dossier = {
        "dossier_id": dossier_id,
        "employee_name": data.employee_name,
        "employee_id": f"EMP-{uuid.uuid4().hex[:5].upper()}",
        "department": data.department,
        "company": data.company,
        "unit_channel": data.unit_channel,
        "job_level": data.job_level,
        "branch": data.branch,
        "date_hired": data.date_hired,
        "eoc_date": data.eoc_date,
        "employee_status": data.employee_status,
        "reason_for_separation": data.reason_for_separation,
        "with_clearance_already": data.with_clearance_already,
        "current_stage": "IT_CLEARANCE",
        "stage_step": 1,
        "overall_status": "PENDING_REVIEW",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "sample_file": data.accountability_form_name or "uploaded_form.pdf",
        "sample_type": "CLEARANCE_SHEET",
        "ai_flags_count": 0,
        "flags_summary": [],
        "nodes": {
            "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "PENDING", "summary": "Asset surrender pending inspection"},
            "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "PENDING", "summary": "Facilities clearance pending"},
            "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Final ledger pending"},
            "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting department clearances"}
        },
        "timeline": [
            {
                "milestone": "Clearance Request Lodged",
                "actor": f"{data.employee_name} (Employee)",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p"),
                "status": "COMPLETED",
                "details": f"Clearance request lodged via Lark Form for {data.company} - {data.department}.",
                "icon": "fa-file-lines"
            },
            {
                "milestone": "Asset Hand-Off & IT Turnover",
                "actor": "Alex Tan (IT Clearance Lead)",
                "date": "Pending turnover",
                "status": "IN_PROGRESS",
                "details": "Surrender company laptop, charger, and hardware assets at Taguig HQ reception.",
                "icon": "fa-laptop"
            },
            {
                "milestone": "Facilities & Physical Locker Turnover",
                "actor": "Elena Cruz (Facilities Lead)",
                "date": "Pending turnover",
                "status": "PENDING",
                "details": "Locker padlock return and security turnstile RFID deactivation.",
                "icon": "fa-key"
            },
            {
                "milestone": "Finance & Payroll Computation",
                "actor": "Roberto Ong (Finance Lead)",
                "date": "Pending audit",
                "status": "PENDING",
                "details": "Pro-rated salary, 13th month computation, and deductions ledger audit.",
                "icon": "fa-calculator"
            },
            {
                "milestone": "Quit Claim & Waiver Sign-Off",
                "actor": f"{data.employee_name} (Employee)",
                "date": "Pending release",
                "status": "PENDING",
                "details": "Review itemized final pay and sign legally binding waiver & quit claim.",
                "icon": "fa-signature"
            },
            {
                "milestone": "HR Final Pay Release & COE",
                "actor": "Grace Diaz (HR Operations)",
                "date": "Pending release",
                "status": "PENDING",
                "details": "Final payout crediting to bank/e-wallet and automated Certificate of Employment release.",
                "icon": "fa-money-bill-transfer"
            }
        ],
        "comments": [
            {
                "id": f"cmt-{uuid.uuid4().hex[:6]}",
                "author": data.employee_name,
                "role": "EMPLOYEE",
                "text": f"Submitted resignation clearance documents. Scheduled for hardware turnover.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "docs": [
            {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
            {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
            {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
        ]
    }
    app.state.dossiers.insert(0, new_dossier)
    app.state.audit_logger.log_human_action(
        dossier_id=dossier_id,
        approver_id=data.employee_name,
        role="REQUESTER",
        action="SUBMIT_APPLICATION",
        flags_reviewed=[],
        override_justification="Initial employee submission via Lark Form",
    )
    return {"status": "SUCCESS", "dossier": new_dossier}


@app.post("/api/precheck")
async def precheck_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
):
    """Processes an uploaded file through the extraction and pre-check engine."""
    try:
        doc_type_enum = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_type '{document_type}'. Valid options: {[e.value for e in DocumentType]}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    mime_type = file.content_type or "application/octet-stream"
    if file.filename and file.filename.lower().endswith(".pdf"):
        mime_type = "application/pdf"

    result = app.state.extractor.extract(
        file_bytes=file_bytes,
        file_name=file.filename or "uploaded_document",
        doc_type=doc_type_enum,
        mime_type=mime_type,
    )

    app.state.audit_logger.log_extraction(result, caller_id="web-dashboard")
    return result.model_dump()


@app.post("/api/approvals/action")
def log_approver_decision(req: HumanActionRequest):
    """Logs human approver decision to the immutable audit trail."""
    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.document_id,
        approver_id=req.approver_id,
        role=req.role,
        action=req.action,
        flags_reviewed=req.flags_reviewed,
        override_justification=req.override_justification,
    )
    # Update in-memory dossier status
    for d in app.state.dossiers:
        if d["dossier_id"] == req.document_id:
            if req.action == "APPROVE":
                d["overall_status"] = "APPROVED"
                d["stage_step"] = min(4, d.get("stage_step", 1) + 1)
            elif req.action == "REJECT":
                d["overall_status"] = "REJECTED"
            else:
                d["overall_status"] = "REVISION_REQUESTED"
            break

    return {"status": "SUCCESS", "audit_entry": entry}


@app.post("/api/approvals/notify-lark")
def send_lark_notification(req: LarkNotificationRequest):
    """Simulates sending an interactive Lark Bot message card to the employee."""
    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=f"LARK-BOT-{req.sender_role}",
        role=req.sender_role,
        action="LARK_NOTIFICATION_DISPATCHED",
        flags_reviewed=[],
        override_justification=f"To {req.employee_name} ({req.recipient}): {req.message}",
    )
    return {
        "status": "SENT",
        "channel": "Lark Workplace Bot",
        "recipient": req.recipient,
        "dossier_id": req.dossier_id,
        "message": req.message,
        "timestamp": entry["timestamp"],
    }


@app.post("/api/approvals/nudge")
def nudge_pending_signer(req: NudgeRequest):
    """Dispatches high-priority Lark reminder to the signer currently holding up the ticket."""
    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=f"NUDGE-{req.sender_role}",
        role=req.sender_role,
        action="LARK_NUDGE_DISPATCHED",
        flags_reviewed=[],
        override_justification=f"Nudged {req.target_name} ({req.target_role}): {req.reason}",
    )
    return {
        "status": "SENT",
        "target": req.target_name,
        "role": req.target_role,
        "dossier_id": req.dossier_id,
        "timestamp": entry["timestamp"],
    }


@app.post("/api/approvals/transaction-comment")
def post_transaction_comment(req: TransactionCommentRequest):
    """Appends an in-dossier transparency comment/update strictly restricted to the requesting user and approvers."""
    dossier = next((d for d in app.state.dossiers if d["dossier_id"] == req.dossier_id), None)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    allowed_roles = {"REQUESTER", "EMPLOYEE", "IT_APPROVER", "FINANCE_APPROVER", "HR_APPROVER", "ADMIN_APPROVER"}
    if req.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Clearance transaction discussion is strictly restricted to the requesting employee and authorized approvers only."
        )

    new_comment = {
        "id": f"cmt-{uuid.uuid4().hex[:6]}",
        "author": req.author,
        "role": req.role,
        "text": req.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if "comments" not in dossier:
        dossier["comments"] = []
    dossier["comments"].append(new_comment)

    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=req.author,
        role=req.role,
        action="TRANSACTION_COMMENT_POSTED",
        flags_reviewed=[],
        override_justification=req.message,
    )
    return {
        "status": "SUCCESS",
        "comment": new_comment,
        "comments": dossier["comments"],
        "timestamp": entry["timestamp"],
    }


@app.get("/api/approvals/metrics")
def get_approval_metrics():
    """Returns live KPI metric numbers for the Executive Clearance Dashboard."""
    total = len(app.state.dossiers)
    pending = sum(1 for d in app.state.dossiers if d.get("category") == "PENDING" or d.get("overall_status") == "PENDING")
    flagged = sum(1 for d in app.state.dossiers if d.get("category") == "FOR_REVIEW" or d.get("overall_status") == "FLAGGED")
    ready = sum(1 for d in app.state.dossiers if d.get("category") == "FOR_RELEASE" or d.get("overall_status") in ("APPROVED", "CLEARED"))
    return {
        "total_requests": total,
        "pending": pending,
        "action_needed": flagged,
        "ready_for_release": ready,
        "avg_sla_days": 4.2,
    }


@app.post("/api/approvals/escalate")
def escalate_ticket(req: EscalateRequest):
    """Escalates idle ticket to Division VP / HR Director to break approval bottlenecks."""
    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=f"ESCALATE-{req.sender_role}",
        role=req.sender_role,
        action="LARK_ESCALATION_DISPATCHED",
        flags_reviewed=[],
        override_justification=f"Escalated to {req.escalate_to} after {req.hours_idle}h idle on {req.employee_name}",
    )
    return {
        "status": "ESCALATED",
        "escalate_to": req.escalate_to,
        "dossier_id": req.dossier_id,
        "timestamp": entry["timestamp"],
    }


@app.post("/api/approvals/batch-approve-clean")
def batch_approve_clean(role: str = "HR_APPROVER"):
    """Fast-tracks all dossiers with 0 AI flags and signs them off in one audited action."""
    approved_ids = []
    for d in app.state.dossiers:
        if d.get("ai_flags_count", 0) == 0 and d.get("overall_status") != "APPROVED":
            d["overall_status"] = "APPROVED"
            d["stage_step"] = 4
            approved_ids.append(d["dossier_id"])
            app.state.audit_logger.log_human_action(
                dossier_id=d["dossier_id"],
                approver_id="BATCH-FAST-TRACK",
                role=role,
                action="BATCH_APPROVE_HUMAN",
                flags_reviewed=[],
                override_justification="Batch 1-click fast-track sign-off for 0-flag verified clean dossier",
            )
    return {
        "status": "SUCCESS",
        "approved_count": len(approved_ids),
        "dossier_ids": approved_ids,
    }


@app.post("/api/approvals/toggle-routing-mode")
def toggle_routing_mode(req: RoutingModeRequest):
    """Toggles global simulation routing between PARALLEL and SEQUENTIAL."""
    for d in app.state.dossiers:
        d["routing_mode"] = req.mode
    return {"status": "SUCCESS", "routing_mode": req.mode}


@app.post("/api/approvals/node-sign")
def sign_department_node(req: NodeSignRequest):
    """Signs off an individual parallel clearance node (IT, Admin, Finance, HR)."""
    target = None
    for d in app.state.dossiers:
        if d["dossier_id"] == req.dossier_id:
            target = d
            break
    if not target:
        raise HTTPException(status_code=404, detail="Dossier not found")

    if "nodes" not in target:
        target["nodes"] = {}

    if req.node_key in target["nodes"]:
        target["nodes"][req.node_key]["status"] = req.action
        target["nodes"][req.node_key]["signer"] = req.approver_name

    # Check parallel convergence across IT, Admin, and Finance
    nodes = target.get("nodes", {})
    it_clear = nodes.get("IT", {}).get("status") == "CLEARED"
    admin_clear = nodes.get("ADMIN", {}).get("status") == "CLEARED"
    fin_clear = nodes.get("FINANCE", {}).get("status") == "CLEARED"
    all_dept_cleared = it_clear and admin_clear and fin_clear

    if all_dept_cleared:
        if nodes.get("HR", {}).get("status") == "LOCKED":
            nodes["HR"]["status"] = "READY"
            nodes["HR"]["summary"] = "All 3 parallel nodes cleared. Ready for final disbursement."
    else:
        if nodes.get("HR", {}).get("status") == "READY":
            nodes["HR"]["status"] = "LOCKED"

    # Advance linear turn sequence if matching active node
    seq = ["IT", "ADMIN", "FINANCE", "HR"]
    if target.get("current_turn_node") == req.node_key and req.action == "CLEARED":
        idx = seq.index(req.node_key)
        if idx + 1 < len(seq):
            nxt = seq[idx + 1]
            target["current_turn_node"] = nxt
            if nxt == "ADMIN":
                target["current_turn_role"] = "ADMIN_APPROVER"
                target["current_turn_name"] = "Elena Cruz (Facilities Lead)"
                target["current_turn_action"] = "Surrender physical office keys, locker padlocks, and RFID transponder."
                target["current_stage"] = "STAGE_1_ASSET"
                target["stage_step"] = 1
            elif nxt == "FINANCE":
                target["current_turn_role"] = "FINANCE_APPROVER"
                target["current_turn_name"] = "Roberto Ong (Finance Lead)"
                target["current_turn_action"] = "Audit pro-rated payroll ledger, tax adjustments, and deductions."
                target["current_stage"] = "STAGE_2_FINANCE"
                target["stage_step"] = 2
            elif nxt == "HR":
                target["current_turn_role"] = "HR_APPROVER"
                target["current_turn_name"] = "Grace Diaz (HR Operations Lead)"
                target["current_turn_action"] = "Execute final DOLE-compliant disbursement and release COE."
                target["current_stage"] = "STAGE_4_HR_RELEASE"
                target["stage_step"] = 4
        else:
            target["current_turn_node"] = "HR"
            target["current_turn_action"] = "All departmental sign-offs completed. Final pay and COE released."
            target["category"] = "FOR_RELEASE"
            target["overall_status"] = "CLEARED"
            target["stage_step"] = 4

    if req.node_key == "HR" and req.action == "CLEARED":
        target["overall_status"] = "APPROVED"
        target["category"] = "FOR_RELEASE"
        target["stage_step"] = 4

    if "timeline" in target:
        target["timeline"].append({
            "milestone": f"{req.node_key} Clearance Cleared",
            "actor": f"{req.approver_name} ({req.role})",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %I:%M %p"),
            "status": "COMPLETED",
            "details": f"Node {req.node_key} signed as {req.action}. Notes: {req.notes or 'Turnover verified.'}",
            "icon": "fa-check"
        })

    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=req.approver_name,
        role=req.role,
        action=f"PARALLEL_NODE_SIGN_{req.node_key}_{req.action}",
        flags_reviewed=[],
        override_justification=f"Parallel node {req.node_key} signed as {req.action} by {req.approver_name}. Notes: {req.notes}",
    )

    return {
        "status": "SUCCESS",
        "dossier": target,
        "all_dept_cleared": all_dept_cleared,
        "audit_entry": entry,
    }


@app.post("/api/approvals/simulate-timeout-forward")
def simulate_timeout_forward(req: TimeoutForwardRequest):
    """Simulates 48h SLA inactivity and auto-forwards signing authority to OIC/Director."""
    target = None
    for d in app.state.dossiers:
        if d["dossier_id"] == req.dossier_id:
            target = d
            break
    if not target:
        raise HTTPException(status_code=404, detail="Dossier not found")

    target["assigned_signer"] = req.new_assignee
    target["sla_auto_forwarded"] = True
    target["sla_forward_reason"] = f"Inactivity timeout ({req.timeout_hours}h SLA limit exceeded). Auto-forwarded from {req.current_role} to {req.new_assignee}."

    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id="SLA-WATCHDOG-ENGINE",
        role="SYSTEM_DELEGATOR",
        action="SLA_TIMEOUT_AUTO_FORWARD",
        flags_reviewed=[],
        override_justification=target["sla_forward_reason"],
    )

    return {
        "status": "AUTO_FORWARDED",
        "dossier_id": req.dossier_id,
        "new_assignee": req.new_assignee,
        "timestamp": entry["timestamp"],
        "reason": target["sla_forward_reason"],
    }


@app.post("/api/approvals/split-escrow")
def execute_split_escrow(req: SplitEscrowRequest):
    """Disburses undisputed final pay immediately while escrowing disputed amounts."""
    target = None
    for d in app.state.dossiers:
        if d["dossier_id"] == req.dossier_id:
            target = d
            break
    if not target:
        raise HTTPException(status_code=404, detail="Dossier not found")

    target["overall_status"] = "PARTIALLY_DISBURSED"
    target["stage_step"] = 3
    target["escrow_details"] = {
        "undisputed_amount": req.undisputed_amount,
        "escrow_amount": req.escrow_amount,
        "reason": req.escrow_reason,
        "status": "ESCROW_ACTIVE",
        "arbitration_window_days": 7,
        "disbursed_at": datetime.now(timezone.utc).isoformat(),
        "approver": req.approver_name,
    }

    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=req.approver_name,
        role=req.role,
        action="SPLIT_ESCROW_DISBURSEMENT",
        flags_reviewed=[],
        override_justification=(
            f"DOLE Compliance Safeguard: Disbursed undisputed ₱{req.undisputed_amount:,.2f} to employee. "
            f"Placed disputed ₱{req.escrow_amount:,.2f} into 7-day arbitration escrow. Reason: {req.escrow_reason}"
        ),
    )

    return {
        "status": "SPLIT_DISBURSED",
        "dossier_id": req.dossier_id,
        "undisputed_amount": req.undisputed_amount,
        "escrow_amount": req.escrow_amount,
        "timestamp": entry["timestamp"],
    }


@app.get("/api/audit-logs")
def get_audit_logs(limit: int = 30):
    """Fetches recent immutable audit log entries."""
    return app.state.audit_logger.get_recent_logs(limit=limit)


template_path = Path(__file__).resolve().parent / "templates" / "dashboard.html"
if template_path.exists():
    HTML_DASHBOARD = template_path.read_text(encoding="utf-8")
else:
    HTML_DASHBOARD = "<html><body><h1>Clearance Dashboard</h1></body></html>"


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Interactive Apple-minimalist dashboard for clearance and last pay testing."""
    if template_path.exists():
        return HTMLResponse(template_path.read_text(encoding="utf-8"))
    return HTMLResponse(HTML_DASHBOARD)


def main():
    parser = argparse.ArgumentParser(description="Clearance & Last Pay Local Test Harness")
    parser.add_argument("--file", type=str, help="Path to document file for CLI extraction")
    parser.add_argument(
        "--type",
        type=str,
        choices=[e.value for e in DocumentType],
        default="QUIT_CLAIM",
        help="Document type to extract",
    )
    parser.add_argument("--web", action="store_true", help="Launch local browser test dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port for web dashboard")
    parser.add_argument("--mock", action="store_true", help="Force deterministic mock extractor")

    args = parser.parse_args()

    if args.mock:
        app.state.extractor = get_extractor(force_mock=True)

    if args.web:
        print(f"\n========================================================")
        print(f" Clearance & Last Pay AI Pre-Check Local Web Harness")
        print(f" Running at: http://localhost:{args.port}")
        print(f" Press CTRL+C to stop.")
        print(f"========================================================\n")
        uvicorn.run(app, host="127.0.0.1", port=args.port)
    elif args.file:
        res = run_cli_extraction(
            file_path=args.file,
            doc_type=DocumentType(args.type),
        )
        print(f"\n--- EXTRACTION RESULT: {res.document_type.value} ---")
        print(f"File: {res.metadata.file_name} (SHA-256: {res.metadata.file_hash_sha256[:16]}...)")
        print(f"Overall Confidence: {res.overall_confidence:.2f}")
        print(f"Flags ({len(res.flags)}):")
        for f in res.flags:
            print(f"  [{f.severity.value}] {f.code.value}: {f.message}")
        print(f"Fields extracted: {len(res.fields.model_dump())}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
