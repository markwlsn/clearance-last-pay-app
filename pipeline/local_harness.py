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


class HuddleRequest(BaseModel):
    dossier_id: str
    employee_name: str
    sender_role: str
    topic: str


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


# In-memory dossier store for demonstration
app.state.dossiers = [
    {
        "dossier_id": "DOS-2026-001",
        "employee_name": "Juan Dela Cruz",
        "employee_id": "EMP-94812",
        "department": "Information Technology",
        "company": "CMG Group of Companies",
        "unit_channel": "Corporate HQ",
        "job_level": "Senior Specialist",
        "branch": "Taguig HQ - 24th Floor",
        "date_hired": "2022-03-15",
        "eoc_date": "2026-08-31",
        "employee_status": "Regular",
        "reason_for_separation": "Resignation",
        "with_clearance_already": "In Progress",
        "current_stage": "IT_CLEARANCE",
        "stage_step": 1,
        "overall_status": "FLAGGED",
        "submitted_at": "2026-09-18T08:30:00Z",
        "sample_file": "clearance_missing_it.pdf",
        "sample_type": "CLEARANCE_SHEET",
        "ai_flags_count": 2,
        "flags_summary": ["FLAG_MISSING_FIELD", "FLAG_ACCOUNTABILITY_NOTED"],
        "routing_mode": "PARALLEL",
        "assigned_signer": "Alex Tan (IT Clearance Lead)",
        "nodes": {
            "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "FLAGGED", "summary": "Unreturned ThinkPad S/N 20WM-0045PH"},
            "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Locker #24 & Parking Tag Cleared"},
            "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "No cash advances outstanding"},
            "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting IT hardware clearance"}
        },
        "escrow_details": None,
        "docs": [
            {"title": "Clearance Sign-Off Sheet", "file": "clearance_missing_it.pdf", "type": "CLEARANCE_SHEET", "has_flags": True},
            {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
            {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
        ]
    },
    {
        "dossier_id": "DOS-2026-002",
        "employee_name": "Maria Clara Santos",
        "employee_id": "EMP-10294",
        "department": "Finance & Accounting",
        "company": "CMG Retail Inc.",
        "unit_channel": "Retail Stores Network",
        "job_level": "Team Lead",
        "branch": "Makati Central Hub",
        "date_hired": "2020-06-01",
        "eoc_date": "2026-09-15",
        "employee_status": "Regular",
        "reason_for_separation": "End of Contract",
        "with_clearance_already": "Yes",
        "current_stage": "LAST_PAY_CALC",
        "stage_step": 2,
        "overall_status": "FLAGGED",
        "submitted_at": "2026-09-17T11:20:00Z",
        "sample_file": "quit_claim_mismatch.pdf",
        "sample_type": "QUIT_CLAIM",
        "ai_flags_count": 2,
        "flags_summary": ["FLAG_AMOUNT_MISMATCH", "FLAG_SIGNATURE_ABSENT"],
        "routing_mode": "PARALLEL",
        "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
        "nodes": {
            "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "ThinkPad & IAM access revoked"},
            "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Store keys surrendered"},
            "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "₱3,500 Quitclaim vs Payroll Ledger disparity"},
            "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting Finance audit resolution"}
        },
        "escrow_details": {
            "undisputed_amount": 48500.0,
            "escrow_amount": 3500.0,
            "reason": "Disputed adapter deduction: Quitclaim stated amount (₱52,000) vs Computed Final Pay (₱48,500)",
            "status": "PENDING",
            "active": False
        },
        "docs": [
            {"title": "Quit Claim & Waiver", "file": "quit_claim_mismatch.pdf", "type": "QUIT_CLAIM", "has_flags": True},
            {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
            {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
        ]
    },
    {
        "dossier_id": "DOS-2026-003",
        "employee_name": "Pedro Penduko",
        "employee_id": "EMP-88419",
        "department": "Logistics & Supply Chain",
        "company": "CMG Distribution Corp.",
        "unit_channel": "Logistics Hub",
        "job_level": "Rank & File",
        "branch": "Cebu Distribution Center",
        "date_hired": "2023-01-10",
        "eoc_date": "2026-09-30",
        "employee_status": "Regular",
        "reason_for_separation": "Resignation",
        "with_clearance_already": "No",
        "current_stage": "FINANCE_DISBURSEMENT",
        "stage_step": 3,
        "overall_status": "FLAGGED",
        "submitted_at": "2026-09-19T14:45:00Z",
        "sample_file": "bank_bad_format.png",
        "sample_type": "BANK_ENROLLMENT",
        "ai_flags_count": 1,
        "flags_summary": ["FLAG_FORMAT_MISMATCH"],
        "routing_mode": "PARALLEL",
        "assigned_signer": "Roberto Ong (Finance & Payroll Lead)",
        "nodes": {
            "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "No IT assets issued"},
            "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Safety gear & uniform returned"},
            "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "FLAGGED", "summary": "Truncated bank account number (091712)"},
            "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Awaiting bank proof update"}
        },
        "escrow_details": None,
        "docs": [
            {"title": "Bank / E-Wallet Proof", "file": "bank_bad_format.png", "type": "BANK_ENROLLMENT", "has_flags": True},
            {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
            {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False}
        ]
    },
    {
        "dossier_id": "DOS-2026-004",
        "employee_name": "Elena Cruz",
        "employee_id": "EMP-77102",
        "department": "Retail Operations",
        "company": "CMG Retail Inc.",
        "unit_channel": "Retail Stores Network",
        "job_level": "Junior Associate",
        "branch": "Davao Regional Hub",
        "date_hired": "2023-08-01",
        "eoc_date": "2026-09-25",
        "employee_status": "Regular",
        "reason_for_separation": "Resignation",
        "with_clearance_already": "Yes",
        "current_stage": "FINAL_RELEASE",
        "stage_step": 4,
        "overall_status": "CLEARED",
        "submitted_at": "2026-09-20T09:10:00Z",
        "sample_file": "clearance_sheet_valid.pdf",
        "sample_type": "CLEARANCE_SHEET",
        "ai_flags_count": 0,
        "flags_summary": [],
        "routing_mode": "PARALLEL",
        "assigned_signer": "Grace Diaz (HR Operations Manager)",
        "nodes": {
            "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "CLEARED", "summary": "POS login revoked"},
            "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Store key returned"},
            "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "CLEARED", "summary": "Final computation balanced"},
            "HR": {"name": "HR Final Release & COE", "signer": "Grace Diaz", "status": "CLEARED", "summary": "COE issued, final pay release ready"}
        },
        "escrow_details": None,
        "docs": [
            {"title": "Clearance Sign-Off Sheet", "file": "clearance_sheet_valid.pdf", "type": "CLEARANCE_SHEET", "has_flags": False},
            {"title": "Quit Claim & Waiver", "file": "quit_claim_valid.pdf", "type": "QUIT_CLAIM", "has_flags": False},
            {"title": "Bank / E-Wallet Proof", "file": "bank_gcash_valid.png", "type": "BANK_ENROLLMENT", "has_flags": False}
        ]
    },
]


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


@app.post("/api/approvals/huddle")
def create_lark_huddle(req: HuddleRequest):
    """Creates a temporary 3-way Lark group chat room [Employee, Dept Head, HR] for rapid resolution."""
    entry = app.state.audit_logger.log_human_action(
        dossier_id=req.dossier_id,
        approver_id=f"HUDDLE-{req.sender_role}",
        role=req.sender_role,
        action="LARK_HUDDLE_CREATED",
        flags_reviewed=[],
        override_justification=f"3-way group created for {req.employee_name}: {req.topic}",
    )
    return {
        "status": "CREATED",
        "chat_name": f"⚡ Clearance Huddle · {req.dossier_id} ({req.employee_name})",
        "members": [req.employee_name, "Department Head", "HR Operations Lead"],
        "dossier_id": req.dossier_id,
        "timestamp": entry["timestamp"],
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

    if req.node_key == "HR" and req.action == "CLEARED":
        target["overall_status"] = "APPROVED"
        target["stage_step"] = 4

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


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Interactive Apple-minimalist dashboard for document extraction testing."""
    return HTML_DASHBOARD


HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en" class="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Clearance & Last Pay — Lark Companion App</title>
  
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: [
              '-apple-system',
              'BlinkMacSystemFont',
              '"SF Pro Display"',
              '"SF Pro Text"',
              '"Helvetica Neue"',
              'Arial',
              'sans-serif'
            ],
            mono: ['"SF Mono"', 'Menlo', 'Monaco', 'monospace'],
          },
          colors: {
            lark: {
              blue: '#3370FF',
              blueHover: '#295ECC',
              border: '#DEE0E3',
              bgGray: '#F5F6F7',
              textDark: '#1F2329',
              textMuted: '#646A73',
              redStar: '#F54A45',
            },
            apple: {
              blue: '#0071E3',
              blueHover: '#0077ED',
              green: '#34C759',
              amber: '#FF9500',
              red: '#FF3B30',
              canvasLight: '#F5F5F7',
              surfaceLight: '#FFFFFF',
              canvasDark: '#000000',
              surfaceDark: '#1C1C1E',
              elevatedDark: '#2C2C2E',
            }
          }
        }
      }
    };
  </script>
  
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  
  <style>
    html { -webkit-font-smoothing: antialiased; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: rgba(140, 140, 145, 0.25); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(140, 140, 145, 0.45); }
    
    .lark-input {
      width: 100%;
      font-size: 13px;
      color: #1F2329;
      background-color: #FFFFFF;
      border: 1px solid #DEE0E3;
      border-radius: 8px;
      padding: 9px 12px;
      outline: none;
      transition: all 0.2s ease;
    }
    .dark .lark-input {
      color: #F5F5F7;
      background-color: #1C1C1E;
      border-color: rgba(255, 255, 255, 0.12);
    }
    .lark-input:focus {
      border-color: #3370FF;
      box-shadow: 0 0 0 2px rgba(51, 112, 255, 0.15);
    }
    .lark-label {
      display: block;
      font-size: 13px;
      font-weight: 500;
      color: #1F2329;
      margin-bottom: 6px;
    }
    .dark .lark-label { color: #E5E5EA; }
    .lark-required { color: #F54A45; margin-left: 2px; }

    /* Apple Workstation UI Tokens */
    .apple-glass {
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
    }
    
    @keyframes apple-shimmer {
      0% { background-position: 0% 50%; }
      50% { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    
    .apple-intelligence-glow {
      background: linear-gradient(135deg, rgba(0,113,227,0.15), rgba(175,82,222,0.15), rgba(255,45,85,0.15));
      background-size: 200% 200%;
      animation: apple-shimmer 6s ease infinite;
    }

    .apple-pulse-green {
      box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.7);
      animation: pulseGreen 2s infinite;
    }
    @keyframes pulseGreen {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(52, 199, 89, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52, 199, 89, 0); }
    }

    .apple-pulse-red {
      box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7);
      animation: pulseRed 2s infinite;
    }
    @keyframes pulseRed {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(255, 59, 48, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
    }
  </style>
</head>
<body class="bg-apple-canvasLight dark:bg-apple-canvasDark text-neutral-900 dark:text-neutral-100 min-h-screen transition-colors duration-300">
  
  <!-- Apple Dynamic Island Floating Toast Notification -->
  <div id="dynamicIslandToast" class="fixed top-5 left-1/2 -translate-x-1/2 z-[100] transform -translate-y-24 opacity-0 transition-all duration-300 pointer-events-none">
    <div class="px-5 py-3 rounded-full bg-neutral-900/90 dark:bg-white/95 text-white dark:text-neutral-900 shadow-2xl apple-glass border border-white/20 dark:border-black/10 flex items-center space-x-3.5 text-xs font-semibold">
      <div id="toastIcon" class="w-6 h-6 rounded-full bg-apple-green text-white flex items-center justify-center text-xs shrink-0 shadow-sm">
        <i class="fa-solid fa-check"></i>
      </div>
      <div>
        <div id="toastTitle" class="font-bold text-xs tracking-tight">Action Completed</div>
        <div id="toastMessage" class="text-[11px] text-neutral-300 dark:text-neutral-600 font-normal">Recorded to immutable audit trail.</div>
      </div>
    </div>
  </div>
  
  <!-- Apple Frosted Glass Top Navigation -->
  <header class="sticky top-0 z-50 bg-white/85 dark:bg-neutral-900/85 backdrop-blur-xl border-b border-black/[0.06] dark:border-white/[0.08] transition-colors duration-300">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      
      <!-- Brand & Title -->
      <div class="flex items-center space-x-3.5">
        <div class="w-8 h-8 rounded-xl bg-lark-blue text-white flex items-center justify-center shadow-sm">
          <i class="fa-solid fa-file-signature text-sm"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-sm font-semibold tracking-tight">Clearance & Last Pay Approval</h1>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-blue-500/10 text-lark-blue border border-blue-500/20">
              Lark Companion
            </span>
          </div>
          <p class="text-[11px] text-neutral-500 dark:text-neutral-400">CMG Group of Companies · Automated Pre-Checks</p>
        </div>
      </div>

      <!-- Center Segmented View Switcher -->
      <nav class="hidden md:flex items-center p-1 bg-neutral-200/60 dark:bg-neutral-800 rounded-xl space-x-1">
        <button id="tabBtnForm" onclick="switchView('form')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition">
          <i class="fa-regular fa-pen-to-square mr-1.5 text-lark-blue"></i> Requester Form
        </button>
        <button id="tabBtnApprover" onclick="switchView('approver')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition">
          <i class="fa-solid fa-user-check mr-1.5 text-apple-green"></i> Approver Review Desk
        </button>
        <button id="tabBtnHarness" onclick="switchView('harness')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition">
          <i class="fa-solid fa-flask-vial mr-1.5 text-apple-amber"></i> Developer Harness
        </button>
      </nav>

      <!-- Right Actions: Guardrail & Theme Switcher -->
      <div class="flex items-center space-x-3.5">
        <div class="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
          <i class="fa-solid fa-shield-halved text-[11px]"></i>
          <span>Human Sign-Off Required</span>
        </div>

        <button id="themeToggle" onclick="toggleTheme()" class="p-2 w-9 h-9 rounded-full bg-neutral-200/70 dark:bg-neutral-800 hover:bg-neutral-300/70 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 transition flex items-center justify-center focus:outline-none" title="Toggle Light / Dark Mode">
          <i id="themeIconSun" class="fa-solid fa-sun text-sm hidden"></i>
          <i id="themeIconMoon" class="fa-solid fa-moon text-sm"></i>
        </button>
      </div>

    </div>
  </header>

  <!-- Mobile View Selector Bar -->
  <div class="md:hidden bg-white dark:bg-neutral-900 border-b border-black/[0.06] dark:border-white/[0.08] px-4 py-2 flex justify-around">
    <button onclick="switchView('form')" class="text-xs font-semibold text-neutral-500 py-1">Requester Form</button>
    <button onclick="switchView('approver')" class="text-xs font-semibold text-lark-blue py-1">Approver Desk</button>
    <button onclick="switchView('harness')" class="text-xs font-medium text-neutral-500 py-1">Dev Harness</button>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8">

    <!-- ================================================================= -->
    <!-- VIEW 1: REQUESTER FORM (LARK APPROVAL RECREATION) -->
    <!-- ================================================================= -->
    <section id="viewForm" class="hidden max-w-3xl mx-auto space-y-6">
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-8 sm:p-10 shadow-[0_4px_20px_rgba(0,0,0,0.04)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.25)] border border-black/[0.06] dark:border-white/[0.08] transition">
        <div class="mb-6">
          <h2 class="text-xl font-bold tracking-tight text-neutral-900 dark:text-white">Application Details</h2>
        </div>
        <div class="mb-6 p-3 rounded-lg bg-neutral-100/80 dark:bg-neutral-800/60 border border-neutral-200/70 dark:border-neutral-700/60 flex items-center space-x-2 text-xs text-neutral-700 dark:text-neutral-300">
          <i class="fa-solid fa-table-list text-lark-blue text-sm"></i>
          <span class="font-medium text-lark-blue hover:underline cursor-pointer">CMG Group SOA Records</span>
        </div>
        <form id="larkClearanceForm" class="space-y-5" onsubmit="handleLarkSubmit(event)">
          <div>
            <label class="lark-label">Department<span class="lark-required">*</span></label>
            <select id="formDept" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Information Technology">Information Technology</option>
              <option value="Finance & Accounting">Finance & Accounting</option>
              <option value="Human Resources">Human Resources</option>
              <option value="Logistics & Supply Chain">Logistics & Supply Chain</option>
              <option value="Retail Operations">Retail Operations</option>
              <option value="Marketing & Brand">Marketing & Brand</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Employee Name<span class="lark-required">*</span></label>
            <select id="formEmployeeName" required class="lark-input" onchange="autoFillEmployee(this.value)">
              <option value="" disabled selected>Select</option>
              <option value="Juan Dela Cruz">Juan Dela Cruz (EMP-94812)</option>
              <option value="Maria Santos">Maria Santos (EMP-10294)</option>
              <option value="Pedro Penduko">Pedro Penduko (EMP-88419)</option>
              <option value="Elena Cruz">Elena Cruz (EMP-77102)</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Date Hired<span class="lark-required">*</span></label>
            <input type="date" id="formDateHired" required value="2026-09-21" class="lark-input" />
          </div>
          <div>
            <label class="lark-label">Job Level<span class="lark-required">*</span></label>
            <select id="formJobLevel" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Rank & File">Rank & File</option>
              <option value="Junior Associate">Junior Associate</option>
              <option value="Senior Associate">Senior Associate</option>
              <option value="Specialist / Professional">Specialist / Professional</option>
              <option value="Team Lead">Team Lead</option>
              <option value="Manager">Manager</option>
              <option value="Senior Manager / Director">Senior Manager / Director</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Company<span class="lark-required">*</span></label>
            <select id="formCompany" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="CMG Group of Companies">CMG Group of Companies</option>
              <option value="CMG Retail Inc.">CMG Retail Inc.</option>
              <option value="CMG Distribution Corp.">CMG Distribution Corp.</option>
              <option value="CMG Logistics Philippines">CMG Logistics Philippines</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Unit / Channel<span class="lark-required">*</span></label>
            <select id="formUnitChannel" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Corporate HQ">Corporate HQ</option>
              <option value="E-Commerce Fulfillment">E-Commerce Fulfillment</option>
              <option value="Retail Stores Network">Retail Stores Network</option>
              <option value="Regional Logistics Hub">Regional Logistics Hub</option>
              <option value="B2B Wholesale">B2B Wholesale</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Branch<span class="lark-required">*</span></label>
            <div class="flex items-center space-x-2">
              <select id="formBranch" required class="lark-input flex-1">
                <option value="Taguig HQ - 24th Floor" selected>Taguig HQ - 24th Floor</option>
                <option value="Makati Central Hub">Makati Central Hub</option>
                <option value="Cebu Distribution Center">Cebu Distribution Center</option>
                <option value="Davao Regional Hub">Davao Regional Hub</option>
              </select>
              <button type="button" onclick="alert('Add Branch modal')" class="px-3.5 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 text-sm font-semibold transition" title="Add Branch">
                <i class="fa-solid fa-plus"></i>
              </button>
            </div>
          </div>
          <div>
            <label class="lark-label">Employee Status<span class="lark-required">*</span></label>
            <select id="formEmployeeStatus" required class="lark-input">
              <option value="Regular" selected>Regular</option>
              <option value="Probationary">Probationary</option>
              <option value="Project-Based">Project-Based</option>
              <option value="Fixed-Term Contract">Fixed-Term Contract</option>
            </select>
          </div>
          <div>
            <label class="lark-label">EOC/Separation Date<span class="lark-required">*</span></label>
            <input type="date" id="formEocDate" required value="2026-09-21" class="lark-input" />
          </div>
          <div>
            <label class="lark-label">With Clearance Already?<span class="lark-required">*</span></label>
            <select id="formWithClearance" required class="lark-input">
              <option value="Yes">Yes</option>
              <option value="No" selected>No</option>
              <option value="In Progress">In Progress</option>
            </select>
          </div>
          <div>
            <label class="lark-label">Reason for Separation<span class="lark-required">*</span></label>
            <select id="formReasonSeparation" required class="lark-input">
              <option value="Resignation" selected>Resignation</option>
              <option value="End of Contract">End of Contract</option>
              <option value="Retirement">Retirement</option>
              <option value="Redundancy / Restructuring">Redundancy / Restructuring</option>
              <option value="Mutual Separation">Mutual Separation</option>
            </select>
          </div>
          <div class="p-3.5 rounded-lg bg-neutral-100/90 dark:bg-neutral-800/70 border border-neutral-200/80 dark:border-neutral-700 text-xs text-neutral-600 dark:text-neutral-300 flex items-start space-x-2">
            <i class="fa-solid fa-circle-info text-neutral-400 mt-0.5"></i>
            <span>If there are missing documents, please attach a notarized affidavit of loss.</span>
          </div>
          <div class="space-y-1.5">
            <label class="lark-label mb-0">Accountability Form</label>
            <div class="flex items-center space-x-3">
              <button type="button" onclick="document.getElementById('attachAccountability').click()" class="px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-xs font-semibold text-neutral-700 dark:text-neutral-200 shadow-sm transition flex items-center">
                <i class="fa-solid fa-arrow-up-from-bracket mr-2 text-neutral-400"></i> Upload attachment
              </button>
              <input type="file" id="attachAccountability" class="hidden" onchange="handleFormAttachment(this, 'accountabilityFileName')" />
              <span id="accountabilityFileName" class="text-xs text-neutral-500">clearance_sheet_valid.pdf (Pre-loaded sample)</span>
            </div>
          </div>
          <div class="space-y-1.5">
            <label class="lark-label mb-0">Valid Government ID<span class="lark-required">*</span></label>
            <div class="flex items-center space-x-3">
              <button type="button" onclick="document.getElementById('attachId').click()" class="px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-xs font-semibold text-neutral-700 dark:text-neutral-200 shadow-sm transition flex items-center">
                <i class="fa-solid fa-arrow-up-from-bracket mr-2 text-neutral-400"></i> Upload attachment
              </button>
              <input type="file" id="attachId" class="hidden" onchange="handleFormAttachment(this, 'idFileName')" />
              <span id="idFileName" class="text-xs text-neutral-500">bank_gcash_valid.png (Pre-loaded proof)</span>
            </div>
          </div>
          <div class="pt-4 flex items-center space-x-3">
            <button type="submit" id="larkSubmitBtn" class="px-6 py-2.5 bg-lark-blue hover:bg-lark-blueHover text-white text-xs font-semibold rounded-lg shadow-sm transition">
              Submit
            </button>
            <button type="button" onclick="resetLarkForm()" class="px-5 py-2.5 border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 text-xs font-semibold rounded-lg shadow-sm transition">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </section>

    <!-- ================================================================= -->
    <!-- VIEW 2: ULTRA-REFINED APPLE APPROVER WORKSTATION -->
    <!-- ================================================================= -->
    <section id="viewApprover" class="space-y-6">
      
      <!-- Top Apple Segmented Control Toolbar: Approver Personas + SLA Cockpit -->
      <div class="bg-white/80 dark:bg-neutral-900/80 apple-glass p-4 sm:p-5 rounded-3xl border border-black/[0.06] dark:border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col xl:flex-row xl:items-center justify-between gap-4 transition">
        
        <!-- Left: Interactive Approver Persona Switcher (Apple Pills) -->
        <div class="flex flex-col space-y-2">
          <div class="flex items-center space-x-2 text-[11px] uppercase tracking-wider font-bold text-neutral-400 dark:text-neutral-500">
            <i class="fa-solid fa-id-badge text-apple-blue"></i>
            <span>Active Approver Workspace</span>
            <span class="text-[10px] lowercase font-normal text-neutral-400">(select to switch role perspective)</span>
          </div>

          <div class="flex flex-wrap items-center p-1 bg-neutral-200/60 dark:bg-neutral-800/80 rounded-2xl gap-1">
            <button onclick="switchApproverRole('IT_APPROVER')" id="roleBtnIT" class="px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm">
              <div class="w-5 h-5 rounded-lg bg-blue-500/15 text-apple-blue flex items-center justify-center text-[10px]">
                <i class="fa-solid fa-laptop-code"></i>
              </div>
              <div class="text-left">
                <div class="leading-none">Alex Tan</div>
                <div class="text-[9px] text-neutral-400 font-normal">IT Clearance</div>
              </div>
            </button>

            <button onclick="switchApproverRole('FINANCE_APPROVER')" id="roleBtnFinance" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-2">
              <div class="w-5 h-5 rounded-lg bg-emerald-500/15 text-apple-green flex items-center justify-center text-[10px]">
                <i class="fa-solid fa-money-check-dollar"></i>
              </div>
              <div class="text-left">
                <div class="leading-none">Roberto Ong</div>
                <div class="text-[9px] text-neutral-400 font-normal">Finance & Payroll</div>
              </div>
            </button>

            <button onclick="switchApproverRole('HR_APPROVER')" id="roleBtnHR" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-2">
              <div class="w-5 h-5 rounded-lg bg-purple-500/15 text-apple-purple flex items-center justify-center text-[10px]">
                <i class="fa-solid fa-user-tie"></i>
              </div>
              <div class="text-left">
                <div class="leading-none">Grace Diaz</div>
                <div class="text-[9px] text-neutral-400 font-normal">HR Operations</div>
              </div>
            </button>

            <button onclick="switchApproverRole('ADMIN_APPROVER')" id="roleBtnAdmin" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-2">
              <div class="w-5 h-5 rounded-lg bg-amber-500/15 text-apple-amber flex items-center justify-center text-[10px]">
                <i class="fa-solid fa-building-user"></i>
              </div>
              <div class="text-left">
                <div class="leading-none">Elena Cruz</div>
                <div class="text-[9px] text-neutral-400 font-normal">Facilities & Admin</div>
              </div>
            </button>
          </div>
        </div>

        <!-- Middle: SLA Acceleration Tracker (Track B Primary Success Metric) -->
        <div class="flex items-center space-x-3.5 px-4 py-2.5 rounded-2xl bg-neutral-100/80 dark:bg-neutral-800/60 border border-black/[0.04] dark:border-white/[0.06]">
          <div class="w-9 h-9 rounded-xl bg-emerald-500/15 text-apple-green flex items-center justify-center text-sm font-bold shadow-sm">
            <i class="fa-solid fa-bolt"></i>
          </div>
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-[10px] text-neutral-400 uppercase font-bold tracking-wider">Turnaround SLA Tracker</span>
              <span class="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-apple-green font-bold">-68% Velocity</span>
            </div>
            <div class="text-xs font-bold text-neutral-800 dark:text-neutral-200 mt-0.5">
              Current: <span class="text-apple-green font-bold">4.2 Days</span>
              <span class="text-neutral-400 font-normal ml-1">(Legacy Lark Form: 10–20 Days)</span>
            </div>
          </div>
        </div>

        <!-- Right: Real-time Queue Counters -->
        <div class="flex items-center space-x-2">
          <div class="px-3.5 py-2 rounded-2xl bg-neutral-100/90 dark:bg-neutral-800 text-xs font-semibold text-neutral-700 dark:text-neutral-300 flex items-center space-x-1.5 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-apple-blue"></span>
            <span><strong id="statPending" class="text-apple-blue font-bold">3</strong> Pending</span>
          </div>
          <div class="px-3.5 py-2 rounded-2xl bg-red-500/10 text-xs font-semibold text-apple-red flex items-center space-x-1.5 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-apple-red"></span>
            <span><strong id="statFlagged" class="font-bold">2</strong> Flagged</span>
          </div>
          <div class="px-3.5 py-2 rounded-2xl bg-emerald-500/10 text-xs font-semibold text-apple-green flex items-center space-x-1.5 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-apple-green"></span>
            <span><strong id="statCleared" class="font-bold">1</strong> Ready</span>
          </div>
        </div>

      </div>

      <!-- Main Workstation Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <!-- Left Pane (4 cols): Master Queue with Search & Status Filter -->
        <div class="lg:col-span-4 space-y-4">
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-5 rounded-3xl border border-black/[0.06] dark:border-white/[0.08] shadow-[0_4px_20px_rgba(0,0,0,0.03)] space-y-3.5">
            
            <!-- Queue Header & Search -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                  Clearance Queue
                </h3>
                <span class="w-1.5 h-1.5 rounded-full bg-apple-blue"></span>
              </div>
              <div class="flex items-center space-x-1.5">
                <button onclick="batchApproveCleanDossiers()" id="batchSignBtn" class="px-2 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-apple-green text-[10px] font-bold border border-emerald-500/20 transition flex items-center space-x-1 shadow-sm active:scale-95" title="Batch sign-off all clean dossiers with 0 AI flags">
                  <i class="fa-solid fa-wand-magic-sparkles text-[9px]"></i>
                  <span>Fast-Track</span>
                </button>
                <span id="queueCount" class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 text-neutral-500">
                  4 dossiers
                </span>
              </div>
            </div>

            <!-- Search Box with Apple Style -->
            <div class="relative">
              <input type="text" id="queueSearchInput" placeholder="Search employee, ID, branch..." oninput="filterQueue()" class="w-full text-xs bg-neutral-100/80 dark:bg-neutral-800/80 text-neutral-900 dark:text-white placeholder-neutral-400 border border-transparent focus:border-apple-blue focus:bg-white dark:focus:bg-neutral-900 rounded-xl pl-8 pr-12 py-2.5 outline-none transition shadow-inner" />
              <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-neutral-400 text-xs"></i>
              <span class="absolute right-2.5 top-2.5 text-[10px] font-mono text-neutral-400 px-1.5 py-0.5 rounded bg-neutral-200/50 dark:bg-neutral-700/50">⌘K</span>
            </div>

            <!-- Filter Segmented Tabs -->
            <div class="flex items-center p-1 bg-neutral-100 dark:bg-neutral-800/60 rounded-xl text-[11px] font-medium text-neutral-500 space-x-1">
              <button onclick="setQueueFilter('ALL')" id="filterAll" class="flex-1 py-1.5 rounded-lg font-bold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition">All</button>
              <button onclick="setQueueFilter('FLAGGED')" id="filterFlagged" class="flex-1 py-1.5 rounded-lg hover:text-neutral-900 dark:hover:text-white transition">Action Needed</button>
              <button onclick="setQueueFilter('CLEARED')" id="filterCleared" class="flex-1 py-1.5 rounded-lg hover:text-neutral-900 dark:hover:text-white transition">Ready</button>
            </div>

            <!-- Queue List -->
            <div id="dossiersQueue" class="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
              <!-- Rendered via JS -->
            </div>

          </div>
        </div>

        <!-- Right Pane (8 cols): Workstation Details, AI Inspection & Document Viewer -->
        <div class="lg:col-span-8 space-y-6">
          
          <div id="approverActiveCard" class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-7 rounded-3xl border border-black/[0.06] dark:border-white/[0.08] shadow-[0_4px_24px_rgba(0,0,0,0.03)] space-y-6 transition">
            
            <!-- 1. Hero Dossier Identity Card with Apple Squircle Avatar -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-black/[0.06] dark:border-white/[0.08] pb-6">
              <div class="flex items-center space-x-4">
                <!-- Large Squircle Monogram Avatar -->
                <div id="apprAvatar" class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 text-white font-bold text-xl flex items-center justify-center shadow-md tracking-tight shrink-0">
                  JD
                </div>
                <div>
                  <div class="flex items-center space-x-2">
                    <h3 id="apprEmpName" class="text-xl font-bold tracking-tight text-neutral-900 dark:text-white">Juan Dela Cruz</h3>
                    <span id="apprEmpIdBadge" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 border border-neutral-200 dark:border-neutral-700">
                      EMP-94812
                    </span>
                  </div>
                  <p id="apprDeptRole" class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                    Information Technology · Senior Specialist
                  </p>
                  <p id="apprSubText" class="text-[11px] text-neutral-400 mt-0.5">
                    Taguig HQ · Separation Date: 2026-08-31 (Resignation)
                  </p>
                </div>
              </div>

              <!-- Top Right Status Badge & Quick Actions -->
              <div class="flex flex-col items-start sm:items-end space-y-2">
                <div class="flex items-center space-x-2">
                  <span id="apprStatusBadge" class="text-xs font-bold px-3 py-1.5 rounded-full bg-red-500/10 text-apple-red border border-red-500/20 flex items-center space-x-1.5">
                    <span id="apprPulseDot" class="w-2 h-2 rounded-full bg-apple-red apple-pulse-red"></span>
                    <span id="apprStatusText">FLAGGED FOR REVIEW</span>
                  </span>
                </div>
                
                <div class="flex items-center space-x-2">
                  <button onclick="pingLarkEmployee()" class="px-3 py-1 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-lark-blue text-xs font-semibold border border-blue-500/20 transition flex items-center space-x-1.5" title="Direct Lark Bot Ping to Employee">
                    <i class="fa-brands fa-rocketchat text-xs"></i>
                    <span>Ping on Lark</span>
                  </button>
                  <span id="apprSlaText" class="text-[11px] font-medium text-neutral-400">
                    <i class="fa-regular fa-clock mr-1"></i> Submitted 3 days ago
                  </span>
                </div>
              </div>
            </div>

            <!-- 2. Dual-Mode Clearance Routing & Progression (Parallel Matrix vs Sequential) -->
            <div class="p-4 sm:p-5 rounded-2xl bg-neutral-50/80 dark:bg-neutral-800/40 border border-black/[0.04] dark:border-white/[0.06] space-y-3.5">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] font-bold uppercase tracking-wider text-neutral-400">
                <div class="flex items-center space-x-2">
                  <i class="fa-solid fa-route text-apple-blue"></i>
                  <span>Clearance Routing Matrix</span>
                  <span id="parallelBadgePill" class="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-apple-green font-mono lowercase">concurrent</span>
                </div>

                <!-- Mode Switcher Pill -->
                <div class="flex items-center p-0.5 rounded-xl bg-neutral-200/80 dark:bg-neutral-700/60 font-semibold lowercase tracking-normal">
                  <button id="modeParallelBtn" onclick="setRoutingMode('PARALLEL')" class="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition flex items-center space-x-1" title="IT, Admin, and Finance evaluate simultaneously, converging into HR final sign-off">
                    <i class="fa-solid fa-bolt text-apple-green text-[9px]"></i>
                    <span>Parallel Matrix (4.2d)</span>
                  </button>
                  <button id="modeSequentialBtn" onclick="setRoutingMode('SEQUENTIAL')" class="px-2.5 py-1 rounded-lg text-[10px] font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-1" title="Traditional step-by-step queue where each stage blocks the next">
                    <i class="fa-solid fa-arrow-right-long text-neutral-400 text-[9px]"></i>
                    <span>Sequential (14d)</span>
                  </button>
                </div>
              </div>

              <!-- Parallel Convergence Grid (Default) -->
              <div id="parallelMatrixContainer" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 text-xs">
                
                <!-- IT Node -->
                <div id="pNodeBoxIT" class="p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-black/[0.05] dark:border-white/[0.06] shadow-sm space-y-2 transition">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-neutral-900 dark:text-white flex items-center space-x-1.5">
                      <i class="fa-solid fa-laptop-code text-apple-blue"></i>
                      <span>IT Clearance</span>
                    </span>
                    <span id="pNodeBadgeIT" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-red-500/10 text-apple-red">FLAGGED</span>
                  </div>
                  <div class="text-[10px] text-neutral-500 dark:text-neutral-400" id="pNodeSignerIT">Signer: Alex Tan</div>
                  <div class="text-[10px] font-mono text-neutral-400 truncate" id="pNodeSummaryIT">ThinkPad hold</div>
                  <button onclick="signParallelNode('IT')" id="btnSignNodeIT" class="w-full py-1.5 rounded-xl bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 text-neutral-800 dark:text-neutral-200 text-[10px] font-bold transition flex items-center justify-center space-x-1">
                    <i class="fa-solid fa-check text-[9px]"></i>
                    <span>Sign IT Node</span>
                  </button>
                </div>

                <!-- Admin & Facilities Node -->
                <div id="pNodeBoxAdmin" class="p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-black/[0.05] dark:border-white/[0.06] shadow-sm space-y-2 transition">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-neutral-900 dark:text-white flex items-center space-x-1.5">
                      <i class="fa-solid fa-building-user text-apple-amber"></i>
                      <span>Facilities & Locker</span>
                    </span>
                    <span id="pNodeBadgeAdmin" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-apple-green">CLEARED</span>
                  </div>
                  <div class="text-[10px] text-neutral-500 dark:text-neutral-400" id="pNodeSignerAdmin">Signer: Elena Cruz</div>
                  <div class="text-[10px] font-mono text-neutral-400 truncate" id="pNodeSummaryAdmin">Locker & parking OK</div>
                  <button onclick="signParallelNode('ADMIN')" id="btnSignNodeAdmin" class="w-full py-1.5 rounded-xl bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 text-neutral-800 dark:text-neutral-200 text-[10px] font-bold transition flex items-center justify-center space-x-1">
                    <i class="fa-solid fa-check text-[9px]"></i>
                    <span>Sign Admin Node</span>
                  </button>
                </div>

                <!-- Finance & Payroll Node -->
                <div id="pNodeBoxFinance" class="p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-black/[0.05] dark:border-white/[0.06] shadow-sm space-y-2 transition">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-neutral-900 dark:text-white flex items-center space-x-1.5">
                      <i class="fa-solid fa-calculator text-apple-purple"></i>
                      <span>Finance Ledger</span>
                    </span>
                    <span id="pNodeBadgeFinance" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-apple-amber">PENDING</span>
                  </div>
                  <div class="text-[10px] text-neutral-500 dark:text-neutral-400" id="pNodeSignerFinance">Signer: Roberto Ong</div>
                  <div class="text-[10px] font-mono text-neutral-400 truncate" id="pNodeSummaryFinance">Pay audit</div>
                  <button onclick="signParallelNode('FINANCE')" id="btnSignNodeFinance" class="w-full py-1.5 rounded-xl bg-neutral-100 dark:bg-neutral-800 hover:bg-neutral-200 text-neutral-800 dark:text-neutral-200 text-[10px] font-bold transition flex items-center justify-center space-x-1">
                    <i class="fa-solid fa-check text-[9px]"></i>
                    <span>Sign Finance Node</span>
                  </button>
                </div>

                <!-- HR Final Release Node (Convergence Target) -->
                <div id="pNodeBoxHR" class="p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-black/[0.05] dark:border-white/[0.06] shadow-sm space-y-2 transition">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-neutral-900 dark:text-white flex items-center space-x-1.5">
                      <i class="fa-solid fa-stamp text-apple-green"></i>
                      <span>HR Final Release</span>
                    </span>
                    <span id="pNodeBadgeHR" class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-neutral-200/80 dark:bg-neutral-800 text-neutral-500 font-mono">🔒 LOCKED</span>
                  </div>
                  <div class="text-[10px] text-neutral-500 dark:text-neutral-400" id="pNodeSignerHR">Signer: Grace Diaz</div>
                  <div class="text-[10px] font-mono text-neutral-400 truncate" id="pNodeSummaryHR">Requires 3 depts</div>
                  <button onclick="signParallelNode('HR')" id="btnSignNodeHR" disabled class="w-full py-1.5 rounded-xl bg-neutral-100 dark:bg-neutral-800 text-neutral-400 text-[10px] font-bold cursor-not-allowed transition flex items-center justify-center space-x-1">
                    <i class="fa-solid fa-lock text-[9px]"></i>
                    <span>Release Final Pay</span>
                  </button>
                </div>

              </div>

              <!-- Sequential Pipeline Grid (Toggleable Alternative) -->
              <div id="sequentialPipelineContainer" class="hidden grid-cols-4 gap-2.5 text-center text-xs">
                
                <div id="step1Box" class="p-3 rounded-xl border border-lark-blue bg-blue-50/60 dark:bg-blue-950/30 text-lark-blue font-semibold transition">
                  <div class="flex items-center justify-center space-x-1.5 mb-1">
                    <i id="step1Icon" class="fa-solid fa-laptop-file text-sm"></i>
                    <span class="text-[11px] font-bold">1. Clearances</span>
                  </div>
                  <div id="step1Status" class="text-[10px] text-apple-red font-bold">IT Hold</div>
                </div>

                <div id="step2Box" class="p-3 rounded-xl border border-black/[0.05] dark:border-white/[0.08] bg-white dark:bg-neutral-800 text-neutral-400 transition">
                  <div class="flex items-center justify-center space-x-1.5 mb-1">
                    <i class="fa-solid fa-calculator text-sm"></i>
                    <span class="text-[11px] font-bold">2. Last Pay</span>
                  </div>
                  <div id="step2Status" class="text-[10px]">Pending</div>
                </div>

                <div id="step3Box" class="p-3 rounded-xl border border-black/[0.05] dark:border-white/[0.08] bg-white dark:bg-neutral-800 text-neutral-400 transition">
                  <div class="flex items-center justify-center space-x-1.5 mb-1">
                    <i class="fa-solid fa-file-contract text-sm"></i>
                    <span class="text-[11px] font-bold">3. Quit Claim</span>
                  </div>
                  <div id="step3Status" class="text-[10px]">Pending</div>
                </div>

                <div id="step4Box" class="p-3 rounded-xl border border-black/[0.05] dark:border-white/[0.08] bg-white dark:bg-neutral-800 text-neutral-400 transition">
                  <div class="flex items-center justify-center space-x-1.5 mb-1">
                    <i class="fa-solid fa-money-check-dollar text-sm"></i>
                    <span class="text-[11px] font-bold">4. Release</span>
                  </div>
                  <div id="step4Status" class="text-[10px]">Pending</div>
                </div>

              </div>
            </div>

            <!-- 3. Apple Intelligence Pre-Check Card with Cupertino Iridescent Glow -->
            <div class="relative p-5 rounded-2xl apple-intelligence-glow border border-purple-500/20 dark:border-purple-400/20 shadow-sm space-y-3.5 transition">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2.5">
                  <div class="w-7 h-7 rounded-xl bg-gradient-to-tr from-purple-500 via-indigo-500 to-pink-500 text-white flex items-center justify-center text-xs shadow-md">
                    <i class="fa-solid fa-wand-magic-sparkles"></i>
                  </div>
                  <div>
                    <h4 class="text-xs font-bold tracking-tight text-neutral-900 dark:text-white uppercase">
                      Apple Intelligence Pre-Check
                    </h4>
                    <p class="text-[10px] text-neutral-500 dark:text-neutral-400">Automated vision & document integrity audit</p>
                  </div>
                </div>
                <div class="flex items-center space-x-2 text-xs">
                  <span class="text-neutral-500 text-[11px]">Audit Confidence:</span>
                  <span id="apprConfidenceText" class="font-bold text-neutral-900 dark:text-white px-2.5 py-0.5 rounded-full bg-white/80 dark:bg-neutral-800 shadow-sm border border-black/[0.05]">95%</span>
                </div>
              </div>

              <div id="apprFlagsList" class="space-y-2.5">
                <!-- Injected Flags or Clean Verified state -->
              </div>
            </div>

            <!-- 4. Dynamic Department Clearance Work Desk (Tailored per active persona!) -->
            <div id="roleSpecificDesk" class="p-5 rounded-2xl bg-neutral-50/80 dark:bg-neutral-800/40 border border-black/[0.06] dark:border-white/[0.08] space-y-3">
              <!-- Dynamically populated via renderRoleWorkDesk() -->
            </div>

            <!-- 5. Tabbed Multi-Document Inspection Deck with Side-by-Side Extracted Inspector -->
            <div class="border border-black/[0.06] dark:border-white/[0.08] rounded-2xl overflow-hidden bg-neutral-50/50 dark:bg-neutral-900/30">
              
              <!-- Document Tabs Header -->
              <div class="px-4 py-2.5 bg-neutral-100/70 dark:bg-neutral-800/60 border-b border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between">
                <div id="docTabsBar" class="flex items-center space-x-1.5 text-xs">
                  <!-- Injected Doc Tabs -->
                </div>
                <a id="apprDocLink" href="#" target="_blank" class="text-xs text-apple-blue hover:underline font-semibold flex items-center space-x-1">
                  <span>Full Screen</span>
                  <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                </a>
              </div>

              <!-- Split Screen: Preview on Left, Live Extracted Inspector on Right -->
              <div class="grid grid-cols-1 md:grid-cols-12 min-h-[300px]">
                
                <!-- Left (7 cols): Document Preview Frame -->
                <div id="apprDocPreview" class="md:col-span-7 p-3 flex items-center justify-center bg-white dark:bg-neutral-950 border-r border-black/[0.06] dark:border-white/[0.08]">
                  <!-- Injected iframe or image -->
                </div>

                <!-- Right (5 cols): Live Extracted Field Inspector -->
                <div class="md:col-span-5 p-4 bg-neutral-50/80 dark:bg-neutral-900/60 flex flex-col justify-between space-y-3 text-xs">
                  <div>
                    <div class="flex items-center justify-between pb-2 border-b border-black/[0.05] dark:border-white/[0.06]">
                      <span class="font-bold text-[11px] uppercase tracking-wider text-neutral-400">Extracted Inspector</span>
                      <span id="docTypeInspectorBadge" class="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-apple-blue">CLEARANCE_SHEET</span>
                    </div>
                    
                    <div id="extractedFieldsInspector" class="mt-3 space-y-2 max-h-64 overflow-y-auto pr-1">
                      <!-- Injected Key-Value Extracted Fields -->
                    </div>
                  </div>

                  <div class="pt-2 border-t border-black/[0.05] dark:border-white/[0.06] text-[10px] text-neutral-400 flex items-center justify-between font-mono">
                    <span id="docShaShort">SHA: a3f8...91c0</span>
                    <span>Claude Vision 3.5</span>
                  </div>
                </div>

              </div>

            </div>

            <!-- 6. Docked Apple Action Bar -->
            <div class="p-5 rounded-2xl bg-neutral-100/70 dark:bg-neutral-800/80 apple-glass border border-black/[0.06] dark:border-white/[0.08] space-y-4 shadow-sm">
              
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div class="flex items-center space-x-2">
                  <div class="w-2.5 h-2.5 rounded-full bg-apple-green apple-pulse-green"></div>
                  <span class="text-xs font-semibold text-neutral-700 dark:text-neutral-300">
                    Signing Authority: <span id="currentRoleLabel" class="font-bold text-neutral-900 dark:text-white">Alex Tan (IT Clearance Lead)</span>
                  </span>
                </div>
                <div class="flex items-center space-x-2 text-[10px] font-mono text-neutral-400">
                  <i class="fa-solid fa-shield-halved text-apple-green"></i>
                  <span>Constitutional Human Gate · Audit Logged</span>
                </div>
              </div>

              <!-- Override Rationale Box -->
              <div id="apprOverrideBox" class="hidden p-3 rounded-xl bg-red-500/10 border border-red-500/20 space-y-1.5">
                <label class="block text-xs font-bold text-apple-red flex items-center space-x-1.5">
                  <i class="fa-solid fa-triangle-exclamation"></i>
                  <span>Mandatory Approver Override Rationale</span>
                </label>
                <p class="text-[11px] text-neutral-600 dark:text-neutral-300">
                  This clearance dossier contains active AI blocker flags. Explain why approval is permitted (e.g. equipment surrendered manually to security, replacement deduction applied, or notarization verified physically).
                </p>
                <textarea id="apprOverrideNotes" rows="2" placeholder="Enter override justification..." class="w-full text-xs bg-white dark:bg-neutral-900 border border-red-300 dark:border-red-900/50 rounded-xl p-2.5 focus:ring-2 focus:ring-apple-blue focus:outline-none transition"></textarea>
              </div>

              <!-- Anti-Idle & SLA Acceleration Velocity Bar -->
              <div class="p-3.5 rounded-2xl bg-white/80 dark:bg-neutral-900/60 border border-black/[0.04] dark:border-white/[0.06] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                <div class="flex items-center space-x-2.5">
                  <div class="w-7 h-7 rounded-xl bg-amber-500/15 text-apple-amber flex items-center justify-center text-xs shrink-0 shadow-sm">
                    <i class="fa-solid fa-stopwatch"></i>
                  </div>
                  <div>
                    <div class="text-[11px] font-bold text-neutral-800 dark:text-neutral-200 flex items-center space-x-1.5">
                      <span>SLA Urgency Cap:</span>
                      <span id="apprUrgencyTag" class="text-apple-amber font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500/10">18h Remaining</span>
                      <span class="text-[9px] text-neutral-400 font-normal">(48h node max)</span>
                    </div>
                    <div class="text-[10px] text-neutral-400">Proactively nudge signers or open huddles to keep clearance velocity high.</div>
                  </div>
                </div>

                <!-- Anti-Idle Action Buttons -->
                <div class="flex flex-wrap items-center gap-1.5">
                  <button onclick="nudgePendingSigner()" class="px-2.5 py-1.5 rounded-xl bg-neutral-100 hover:bg-neutral-200/80 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 text-[11px] font-semibold transition flex items-center space-x-1.5 shadow-sm active:scale-95" title="Dispatches instant Lark Bot reminder to the current signer holding up this ticket">
                    <i class="fa-solid fa-bell text-apple-amber text-[10px]"></i>
                    <span>Nudge Signer</span>
                  </button>

                  <button onclick="openLarkHuddle()" class="px-2.5 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-lark-blue text-[11px] font-semibold border border-blue-500/20 transition flex items-center space-x-1.5 shadow-sm active:scale-95" title="Instant 3-way Lark group chat with Employee, Dept Head, and HR for 5-minute alignment">
                    <i class="fa-solid fa-users text-[10px]"></i>
                    <span>Lark Huddle</span>
                  </button>

                  <button onclick="escalateTicket()" class="px-2.5 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-apple-red text-[11px] font-semibold border border-red-500/20 transition flex items-center space-x-1.5 shadow-sm active:scale-95" title="Escalates idle ticket to Division VP / HR Director">
                    <i class="fa-solid fa-arrow-up-right-dots text-[10px]"></i>
                    <span>Escalate to VP</span>
                  </button>

                  <button onclick="simulateSlaTimeoutForward()" class="px-2.5 py-1.5 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 text-apple-purple text-[11px] font-semibold border border-purple-500/20 transition flex items-center space-x-1.5 shadow-sm active:scale-95" title="Simulate 48h SLA inactivity: triggers auto-forwarding to secondary OIC Carlo Mendoza">
                    <i class="fa-solid fa-clock-rotate-left text-[10px]"></i>
                    <span>Simulate SLA Timeout</span>
                  </button>

                  <button onclick="delegateTicket()" class="px-2.5 py-1.5 rounded-xl bg-neutral-100 hover:bg-neutral-200/80 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 text-[11px] font-semibold transition flex items-center space-x-1.5 shadow-sm active:scale-95" title="Reassign ticket to designated backup or OIC">
                    <i class="fa-solid fa-user-gear text-[10px]"></i>
                    <span>Delegate</span>
                  </button>
                </div>
              </div>

              <!-- Action CTAs -->
              <div class="flex flex-wrap items-center justify-end gap-2.5 pt-1">
                <button onclick="openSplitEscrowModal()" id="btnSplitEscrowAction" class="hidden px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-bold rounded-xl shadow-sm active:scale-[0.98] transition flex items-center" title="Execute partial release: disburse undisputed pay now and escrow disputed variance">
                  <i class="fa-solid fa-scale-balanced mr-2"></i> Split Escrow Release
                </button>
                <button onclick="pingLarkEmployee()" class="px-4 py-2.5 rounded-xl border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-100 text-xs font-semibold text-neutral-700 dark:text-neutral-200 shadow-sm active:scale-[0.98] transition flex items-center">
                  <i class="fa-brands fa-rocketchat mr-2 text-lark-blue"></i> Lark Message
                </button>
                <button onclick="submitApproverDeskDecision('REQUEST_REVISION')" class="px-4 py-2.5 bg-apple-amber hover:bg-amber-600 text-white text-xs font-bold rounded-xl shadow-sm active:scale-[0.98] transition flex items-center">
                  <i class="fa-solid fa-rotate-left mr-2"></i> Request Revision
                </button>
                <button onclick="submitApproverDeskDecision('REJECT')" class="px-4 py-2.5 bg-apple-red hover:bg-red-600 text-white text-xs font-bold rounded-xl shadow-sm active:scale-[0.98] transition flex items-center">
                  <i class="fa-solid fa-ban mr-2"></i> Reject
                </button>
                <button onclick="submitApproverDeskDecision('APPROVE')" id="apprApproveBtn" class="px-5 py-2.5 bg-apple-green hover:bg-emerald-600 text-white text-xs font-bold rounded-xl shadow-sm active:scale-[0.98] transition flex items-center">
                  <i class="fa-solid fa-check mr-2"></i> Approve Clearance Step
                </button>
              </div>

            </div>

          </div>

        </div>

      </div>

    </section>

    <!-- ================================================================= -->
    <!-- VIEW 3: DEVELOPER HARNESS (TEST RUNNER) -->
    <!-- ================================================================= -->
    <section id="viewHarness" class="hidden space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div class="lg:col-span-4 space-y-6">
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
            <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-3 flex items-center">
              <i class="fa-solid fa-flask mr-2 text-apple-amber"></i> Quick Test Fixtures
            </h3>
            <div id="harnessSamplesList" class="space-y-2"></div>
          </div>
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400">Recent Audit Trail</h3>
              <button onclick="loadAuditLogs()" class="text-xs text-lark-blue hover:underline"><i class="fa-solid fa-rotate-right"></i></button>
            </div>
            <div id="harnessAuditContainer" class="max-h-72 overflow-y-auto space-y-2 text-xs"></div>
          </div>
        </div>
        <div class="lg:col-span-8 space-y-6">
          <div id="harnessResultCard" class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm min-h-[500px]">
            <div id="harnessEmptyState" class="text-center py-20 text-neutral-400">
              <i class="fa-solid fa-terminal text-4xl mb-3 text-neutral-300"></i>
              <h4 class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Developer Diagnostic Output</h4>
              <p class="text-xs text-neutral-400 max-w-sm mx-auto mt-1">Select any fixture to view raw JSON extraction.</p>
            </div>
            <div id="harnessResultContent" class="hidden space-y-5">
              <div class="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
                <div>
                  <span id="harnessDocType" class="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-lark-blue">TYPE</span>
                  <h3 id="harnessFileName" class="text-sm font-bold text-neutral-900 dark:text-white mt-1">file.pdf</h3>
                </div>
                <span id="harnessConfidence" class="text-xl font-bold text-apple-green">95%</span>
              </div>
              <div id="harnessFlagsBox" class="space-y-2"></div>
              <pre id="harnessJsonPre" class="p-4 rounded-xl bg-neutral-900 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-72"></pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Apple Split Escrow Modal Dialog -->
    <div id="splitEscrowModal" class="hidden fixed inset-0 z-50 bg-black/50 backdrop-blur-md flex items-center justify-center p-4">
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark max-w-lg w-full rounded-3xl p-6 border border-black/[0.08] dark:border-white/[0.1] shadow-2xl space-y-5">
        <div class="flex items-center justify-between pb-3 border-b border-black/[0.06] dark:border-white/[0.08]">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-2xl bg-amber-500/15 text-apple-amber flex items-center justify-center text-base shadow-sm">
              <i class="fa-solid fa-scale-balanced"></i>
            </div>
            <div>
              <h3 class="text-sm font-bold text-neutral-900 dark:text-white">Split Clearance & Escrow Disbursement</h3>
              <p class="text-[11px] text-neutral-400">DOLE Labor Advisory #06 Compliance Safeguard</p>
            </div>
          </div>
          <button onclick="closeSplitEscrowModal()" class="w-8 h-8 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-400 hover:text-neutral-700 dark:hover:text-white flex items-center justify-center transition">
            <i class="fa-solid fa-xmark text-sm"></i>
          </button>
        </div>

        <div class="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-neutral-700 dark:text-neutral-300 space-y-1">
          <div class="font-bold text-apple-green flex items-center space-x-1.5">
            <i class="fa-solid fa-shield-check"></i>
            <span>Zero-Dispute Final Pay Protocol</span>
          </div>
          <p class="text-[11px] text-neutral-600 dark:text-neutral-400">
            Releases undisputed livelihood earnings to the employee immediately. Isolates the disputed variance into a 7-day Lark arbitration escrow window.
          </p>
        </div>

        <div class="space-y-2.5 text-xs">
          <div class="flex items-center justify-between p-3 rounded-xl bg-neutral-100/80 dark:bg-neutral-800/80 border border-black/[0.04]">
            <div>
              <div class="font-bold text-neutral-800 dark:text-neutral-200">Undisputed Net Pay (Disburse Now)</div>
              <div class="text-[10px] text-neutral-400">Direct credit to employee verified account</div>
            </div>
            <div class="font-mono text-base font-bold text-apple-green" id="splitModalUndisputed">₱48,500.00</div>
          </div>

          <div class="flex items-center justify-between p-3 rounded-xl bg-neutral-100/80 dark:bg-neutral-800/80 border border-black/[0.04]">
            <div>
              <div class="font-bold text-neutral-800 dark:text-neutral-200">Disputed Hold Amount (Escrowed)</div>
              <div class="text-[10px] text-apple-red">Held in payroll escrow pending Lark Huddle</div>
            </div>
            <div class="font-mono text-base font-bold text-apple-red" id="splitModalEscrow">₱3,500.00</div>
          </div>

          <div class="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-900 border border-black/[0.04] space-y-1">
            <span class="text-[10px] font-bold text-neutral-400 uppercase">Reason for Escrow Hold</span>
            <div class="text-[11px] text-neutral-700 dark:text-neutral-300 font-medium" id="splitModalReason">
              Disputed Quit Claim stated amount (₱52,000.00) vs Computed Final Pay (₱48,500.00)
            </div>
          </div>
        </div>

        <div class="pt-2 flex items-center justify-end space-x-2.5">
          <button onclick="closeSplitEscrowModal()" class="px-4 py-2.5 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition">
            Cancel
          </button>
          <button onclick="confirmSplitEscrowDisbursement()" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white text-xs font-bold shadow-md transition active:scale-95 flex items-center space-x-1.5">
            <i class="fa-solid fa-paper-plane text-xs"></i>
            <span>Execute Split Disbursement</span>
          </button>
        </div>
      </div>
    </div>

  </main>

  <script>
    let activeDossier = null;
    let currentFilter = 'ALL';
    let activeDocIndex = 0;

    // View Switcher
    function switchView(viewName) {
      document.getElementById('viewForm').classList.add('hidden');
      document.getElementById('viewApprover').classList.add('hidden');
      document.getElementById('viewHarness').classList.add('hidden');

      const btnForm = document.getElementById('tabBtnForm');
      const btnAppr = document.getElementById('tabBtnApprover');
      const btnHarn = document.getElementById('tabBtnHarness');

      const inactiveClass = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition";
      const activeClass = "px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition";

      btnForm.className = inactiveClass;
      btnAppr.className = inactiveClass;
      btnHarn.className = inactiveClass;

      if (viewName === 'form') {
        document.getElementById('viewForm').classList.remove('hidden');
        btnForm.className = activeClass;
      } else if (viewName === 'approver') {
        document.getElementById('viewApprover').classList.remove('hidden');
        btnAppr.className = activeClass;
        loadDossiersQueue();
      } else if (viewName === 'harness') {
        document.getElementById('viewHarness').classList.remove('hidden');
        btnHarn.className = activeClass;
      }
    }

    // Auto Fill
    function autoFillEmployee(name) {
      if (name.includes("Juan")) {
        document.getElementById('formDept').value = "Information Technology";
        document.getElementById('formJobLevel').value = "Specialist / Professional";
        document.getElementById('formCompany').value = "CMG Group of Companies";
        document.getElementById('formUnitChannel').value = "Corporate HQ";
        document.getElementById('formBranch').value = "Taguig HQ - 24th Floor";
      } else if (name.includes("Maria")) {
        document.getElementById('formDept').value = "Finance & Accounting";
        document.getElementById('formJobLevel').value = "Team Lead";
        document.getElementById('formCompany').value = "CMG Retail Inc.";
        document.getElementById('formUnitChannel').value = "Retail Stores Network";
        document.getElementById('formBranch').value = "Makati Central Hub";
      } else if (name.includes("Elena")) {
        document.getElementById('formDept').value = "Retail Operations";
        document.getElementById('formJobLevel').value = "Junior Associate";
        document.getElementById('formCompany').value = "CMG Retail Inc.";
        document.getElementById('formUnitChannel').value = "Retail Stores Network";
        document.getElementById('formBranch').value = "Davao Regional Hub";
      }
    }

    function handleFormAttachment(input, labelId) {
      if (input.files.length) {
        document.getElementById(labelId).textContent = input.files[0].name;
      }
    }

    async function handleLarkSubmit(e) {
      e.preventDefault();
      const submitBtn = document.getElementById('larkSubmitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-1.5"></i> Submitting...';

      const payload = {
        department: document.getElementById('formDept').value,
        employee_name: document.getElementById('formEmployeeName').value,
        date_hired: document.getElementById('formDateHired').value,
        job_level: document.getElementById('formJobLevel').value,
        company: document.getElementById('formCompany').value,
        unit_channel: document.getElementById('formUnitChannel').value,
        branch: document.getElementById('formBranch').value,
        employee_status: document.getElementById('formEmployeeStatus').value,
        eoc_date: document.getElementById('formEocDate').value,
        with_clearance_already: document.getElementById('formWithClearance').value,
        reason_for_separation: document.getElementById('formReasonSeparation').value,
        accountability_form_name: document.getElementById('accountabilityFileName').textContent,
        id_form_name: document.getElementById('idFileName').textContent,
      };

      try {
        const res = await fetch('/api/clearance/submit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        alert(`Clearance Application Submitted!\nDossier ID: ${data.dossier.dossier_id}`);
        switchView('approver');
      } catch (err) {
        alert('Submission error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit';
      }
    }

    function resetLarkForm() {
      document.getElementById('larkClearanceForm').reset();
    }

    // Approver Queue Logic
    function setQueueFilter(filter) {
      currentFilter = filter;
      const fAll = document.getElementById('filterAll');
      const fFlag = document.getElementById('filterFlagged');
      const fClear = document.getElementById('filterCleared');

      const activeClass = "flex-1 py-1 rounded-lg font-semibold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition";
      const inactiveClass = "flex-1 py-1 rounded-lg hover:text-neutral-900 dark:hover:text-white transition";

      fAll.className = filter === 'ALL' ? activeClass : inactiveClass;
      fFlag.className = filter === 'FLAGGED' ? activeClass : inactiveClass;
      fClear.className = filter === 'CLEARED' ? activeClass : inactiveClass;

      renderQueue();
    }

    function filterQueue() {
      renderQueue();
    }

    let allDossiersCache = [];

    async function loadDossiersQueue() {
      try {
        const res = await fetch('/api/clearance/dossiers');
        allDossiersCache = await res.json();

        // Update stats
        const pending = allDossiersCache.filter(d => d.overall_status !== 'APPROVED').length;
        const flagged = allDossiersCache.filter(d => d.ai_flags_count > 0).length;
        const cleared = allDossiersCache.filter(d => d.overall_status === 'CLEARED' || d.overall_status === 'APPROVED').length;

        document.getElementById('statPending').textContent = pending;
        document.getElementById('statFlagged').textContent = flagged;
        document.getElementById('statCleared').textContent = cleared;

        renderQueue();

        if (allDossiersCache.length && !activeDossier) {
          selectDossier(allDossiersCache[0].dossier_id);
        }
      } catch (err) {
        console.error(err);
      }
    }

    function renderQueue() {
      const q = document.getElementById('queueSearchInput').value.toLowerCase();
      const container = document.getElementById('dossiersQueue');

      const filtered = allDossiersCache.filter(d => {
        const matchSearch = d.employee_name.toLowerCase().includes(q) || 
                            d.dossier_id.toLowerCase().includes(q) || 
                            d.department.toLowerCase().includes(q);
        if (!matchSearch) return false;

        if (currentFilter === 'FLAGGED') return d.ai_flags_count > 0;
        if (currentFilter === 'CLEARED') return d.ai_flags_count === 0 || d.overall_status === 'APPROVED';
        return true;
      });

      document.getElementById('queueCount').textContent = `${filtered.length} dossiers`;

      container.innerHTML = filtered.map(d => {
        const isActive = activeDossier && activeDossier.dossier_id === d.dossier_id;
        const hasFlags = d.ai_flags_count > 0;
        const initials = d.employee_name.split(' ').map(n => n[0]).slice(0, 2).join('');
        
        let statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-apple-green">CLEARED</span>';
        if (d.overall_status === 'APPROVED') {
          statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-apple-green">APPROVED</span>';
        } else if (hasFlags) {
          statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/10 text-apple-red">FLAGGED</span>';
        } else {
          statusBadge = '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-apple-amber">IN PROGRESS</span>';
        }

        const borderClass = isActive ? 'border-l-4 border-apple-blue bg-blue-50/40 dark:bg-neutral-800 shadow-sm' : 'border border-black/[0.04] dark:border-white/[0.06] bg-neutral-50/70 dark:bg-apple-elevatedDark hover:bg-neutral-100/60 dark:hover:bg-neutral-700/50';

        return `
          <div onclick="selectDossier('${d.dossier_id}')" class="p-3 rounded-xl ${borderClass} cursor-pointer transition flex items-center space-x-3 group">
            <div class="w-10 h-10 rounded-xl bg-neutral-200/80 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-200 font-bold text-xs flex items-center justify-center shrink-0">
              ${initials}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-neutral-800 dark:text-neutral-200 truncate group-hover:text-apple-blue transition">${d.employee_name}</span>
                ${statusBadge}
              </div>
              <div class="text-[11px] text-neutral-400 truncate mt-0.5">${d.department} · ${d.dossier_id}</div>
              <div class="text-[10px] text-neutral-400 mt-1 flex items-center justify-between">
                <span>${hasFlags ? `<span class="text-apple-red font-semibold"><i class="fa-solid fa-triangle-exclamation mr-1"></i>${d.ai_flags_count} flag(s)</span>` : '<span class="text-apple-green"><i class="fa-solid fa-check mr-1"></i>Clean pre-check</span>'}</span>
                <span>EOC: ${d.eoc_date}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    let currentApproverRole = 'IT_APPROVER';

    function showDynamicToast(title, message, type = 'success') {
      const toast = document.getElementById('dynamicIslandToast');
      const icon = document.getElementById('toastIcon');
      const tTitle = document.getElementById('toastTitle');
      const tMsg = document.getElementById('toastMessage');

      tTitle.textContent = title;
      tMsg.textContent = message;

      if (type === 'error') {
        icon.className = 'w-6 h-6 rounded-full bg-apple-red text-white flex items-center justify-center text-xs shrink-0 shadow-sm';
        icon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
      } else if (type === 'info') {
        icon.className = 'w-6 h-6 rounded-full bg-apple-blue text-white flex items-center justify-center text-xs shrink-0 shadow-sm';
        icon.innerHTML = '<i class="fa-brands fa-rocketchat"></i>';
      } else {
        icon.className = 'w-6 h-6 rounded-full bg-apple-green text-white flex items-center justify-center text-xs shrink-0 shadow-sm';
        icon.innerHTML = '<i class="fa-solid fa-check"></i>';
      }

      toast.classList.remove('-translate-y-24', 'opacity-0', 'pointer-events-none');
      toast.classList.add('translate-y-0', 'opacity-100');

      clearTimeout(window._toastTimeout);
      window._toastTimeout = setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('-translate-y-24', 'opacity-0', 'pointer-events-none');
      }, 3200);
    }

    async function pingLarkEmployee() {
      if (!activeDossier) return;
      try {
        const res = await fetch('/api/approvals/notify-lark', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            employee_name: activeDossier.employee_name,
            recipient: `lark://user/${activeDossier.employee_id}`,
            message: `Hello ${activeDossier.employee_name}, your clearance dossier ${activeDossier.dossier_id} is currently in review under ${currentApproverRole}. Please monitor Lark for updates.`,
            sender_role: currentApproverRole,
          })
        });
        await res.json();
        showDynamicToast("Lark Workplace Card Sent", `Direct reminder dispatched to ${activeDossier.employee_name}.`, "info");
      } catch (err) {
        showDynamicToast("Notification Failed", err.message, "error");
      }
    }

    async function nudgePendingSigner() {
      if (!activeDossier) return;
      const target = currentApproverRole === 'IT_APPROVER' ? 'Alex Tan (IT Helpdesk)' :
                     currentApproverRole === 'FINANCE_APPROVER' ? 'Roberto Ong (Finance Lead)' :
                     currentApproverRole === 'HR_APPROVER' ? 'Grace Diaz (HR Operations)' : 'Elena Cruz (Facilities Admin)';
      try {
        const res = await fetch('/api/approvals/nudge', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            target_role: currentApproverRole,
            target_name: target,
            sender_role: "CLEARANCE_WORKSTATION",
            reason: `Urgent sign-off requested for ${activeDossier.employee_name} (${activeDossier.dossier_id}). Approaching 48h SLA limit.`
          })
        });
        await res.json();
        showDynamicToast("Lark Nudge Dispatched", `Sent priority alert to ${target} on Lark mobile/desktop.`, "info");
      } catch (err) {
        showDynamicToast("Nudge Failed", err.message, "error");
      }
    }

    async function openLarkHuddle() {
      if (!activeDossier) return;
      try {
        const res = await fetch('/api/approvals/huddle', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            employee_name: activeDossier.employee_name,
            sender_role: currentApproverRole,
            topic: `Resolve clearance flags: ${activeDossier.flags_summary && activeDossier.flags_summary.length ? activeDossier.flags_summary.join(', ') : 'Standard Final Pay Handover'}`
          })
        });
        const data = await res.json();
        showDynamicToast("Lark Huddle Room Active", `Group chat created with ${activeDossier.employee_name}, Dept Head & HR.`, "info");
      } catch (err) {
        showDynamicToast("Huddle Failed", err.message, "error");
      }
    }

    async function escalateTicket() {
      if (!activeDossier) return;
      const vpTarget = "Maria Consuelo (Division VP) & HR Director";
      try {
        const res = await fetch('/api/approvals/escalate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            employee_name: activeDossier.employee_name,
            escalate_to: vpTarget,
            sender_role: currentApproverRole,
            hours_idle: 36
          })
        });
        await res.json();
        showDynamicToast("Priority Escalation Sent", `Notice sent to ${vpTarget}. SLA breach prevented.`, "error");
      } catch (err) {
        showDynamicToast("Escalation Failed", err.message, "error");
      }
    }

    function delegateTicket() {
      if (!activeDossier) return;
      const backupOIC = "Carlo Mendoza (Designated OIC / Peer Lead)";
      showDynamicToast("Clearance Delegated", `Ticket temporarily routed to ${backupOIC} for sign-off.`, "info");
    }

    async function batchApproveCleanDossiers() {
      try {
        const res = await fetch('/api/approvals/batch-approve-clean', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
        });
        const data = await res.json();
        if (data.approved_count === 0) {
          showDynamicToast("No Action Needed", "All clean dossiers are already signed off.", "info");
        } else {
          showDynamicToast("Fast-Track Complete!", `Signed off ${data.approved_count} verified clean dossier(s) with 0 flags!`, "success");
          await loadDossiersQueue();
        }
      } catch (err) {
        showDynamicToast("Batch Action Failed", err.message, "error");
      }
    }

    let currentRoutingMode = 'PARALLEL';

    async function setRoutingMode(mode) {
      currentRoutingMode = mode;
      const btnParallel = document.getElementById('modeParallelBtn');
      const btnSequential = document.getElementById('modeSequentialBtn');
      const parallelContainer = document.getElementById('parallelMatrixContainer');
      const seqContainer = document.getElementById('sequentialPipelineContainer');
      const pill = document.getElementById('parallelBadgePill');

      const activeBtnClass = "px-2.5 py-1 rounded-lg text-[10px] font-bold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition flex items-center space-x-1";
      const inactiveBtnClass = "px-2.5 py-1 rounded-lg text-[10px] font-medium text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-1";

      if (mode === 'PARALLEL') {
        if (btnParallel) btnParallel.className = activeBtnClass;
        if (btnSequential) btnSequential.className = inactiveBtnClass;
        if (parallelContainer) parallelContainer.classList.remove('hidden');
        if (seqContainer) seqContainer.classList.add('hidden');
        if (pill) {
          pill.textContent = 'concurrent';
          pill.className = 'text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-apple-green font-mono lowercase';
        }
        showDynamicToast("Parallel Routing Active", "IT, Admin, and Finance evaluate simultaneously. Turnaround: 4.2d.", "info");
      } else {
        if (btnParallel) btnParallel.className = inactiveBtnClass;
        if (btnSequential) btnSequential.className = activeBtnClass;
        if (parallelContainer) parallelContainer.classList.add('hidden');
        if (seqContainer) {
          seqContainer.classList.remove('hidden');
          seqContainer.classList.add('grid');
        }
        if (pill) {
          pill.textContent = 'sequential queue';
          pill.className = 'text-[9px] px-2 py-0.5 rounded-full bg-amber-500/10 text-apple-amber font-mono lowercase';
        }
        showDynamicToast("Sequential Routing Active", "Traditional linear queue where each step blocks the next (14d).", "info");
      }

      try {
        await fetch('/api/approvals/toggle-routing-mode', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ mode: mode })
        });
      } catch (err) {}

      if (activeDossier) {
        updateProgressPipeline(activeDossier);
      }
    }

    async function signParallelNode(nodeKey) {
      if (!activeDossier) return;
      const signerName = currentApproverRole === 'IT_APPROVER' ? 'Alex Tan (IT Lead)' :
                         currentApproverRole === 'FINANCE_APPROVER' ? 'Roberto Ong (Finance Lead)' :
                         currentApproverRole === 'HR_APPROVER' ? 'Grace Diaz (HR Operations)' : 'Elena Cruz (Facilities Admin)';
      try {
        const res = await fetch('/api/approvals/node-sign', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            node_key: nodeKey,
            approver_name: signerName,
            role: currentApproverRole,
            action: "CLEARED",
            notes: `Signed off in Parallel Mode via Approver Review Desk`
          })
        });
        const data = await res.json();
        if (data.status === 'SUCCESS') {
          activeDossier.nodes = data.dossier.nodes;
          activeDossier.overall_status = data.dossier.overall_status;
          activeDossier.stage_step = data.dossier.stage_step;
          showDynamicToast(`${nodeKey} Node Cleared!`, `Signed by ${signerName}. ${data.all_dept_cleared ? 'All 3 parallel nodes cleared! HR unlocked.' : ''}`, "success");
          updateProgressPipeline(activeDossier);
          renderQueue();
        }
      } catch (err) {
        showDynamicToast("Node Sign Failed", err.message, "error");
      }
    }

    async function simulateSlaTimeoutForward() {
      if (!activeDossier) return;
      const oicAssignee = "Carlo Mendoza (Designated OIC / Peer Lead)";
      try {
        const res = await fetch('/api/approvals/simulate-timeout-forward', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            current_role: currentApproverRole,
            timeout_hours: 48,
            new_assignee: oicAssignee
          })
        });
        const data = await res.json();
        activeDossier.assigned_signer = data.new_assignee;
        activeDossier.sla_auto_forwarded = true;
        showDynamicToast("SLA Breach Prevented", `48h timeout reached. Auto-forwarded to ${data.new_assignee}.`, "info");
        const urgencyTag = document.getElementById('apprUrgencyTag');
        if (urgencyTag) {
          urgencyTag.textContent = 'Auto-Forwarded to OIC';
          urgencyTag.className = 'text-apple-purple font-mono font-bold px-1.5 py-0.2 rounded bg-purple-500/10';
        }
        renderQueue();
      } catch (err) {
        showDynamicToast("Auto-Forward Failed", err.message, "error");
      }
    }

    function openSplitEscrowModal() {
      if (!activeDossier) return;
      const modal = document.getElementById('splitEscrowModal');
      const undisp = document.getElementById('splitModalUndisputed');
      const escrow = document.getElementById('splitModalEscrow');
      const reason = document.getElementById('splitModalReason');

      if (activeDossier.escrow_details) {
        undisp.textContent = `₱${Number(activeDossier.escrow_details.undisputed_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        escrow.textContent = `₱${Number(activeDossier.escrow_details.escrow_amount).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        reason.textContent = activeDossier.escrow_details.reason;
      } else {
        undisp.textContent = '₱48,500.00';
        escrow.textContent = '₱3,500.00';
        reason.textContent = 'Disputed Quit Claim stated amount (₱52,000.00) vs Computed Final Pay (₱48,500.00)';
      }

      modal.classList.remove('hidden');
    }

    function closeSplitEscrowModal() {
      const modal = document.getElementById('splitEscrowModal');
      if (modal) modal.classList.add('hidden');
    }

    async function confirmSplitEscrowDisbursement() {
      if (!activeDossier) return;
      const signerName = currentApproverRole === 'FINANCE_APPROVER' ? 'Roberto Ong (Finance Lead)' : 'Grace Diaz (HR Operations)';
      try {
        const res = await fetch('/api/approvals/split-escrow', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            dossier_id: activeDossier.dossier_id,
            undisputed_amount: 48500.00,
            escrow_amount: 3500.00,
            escrow_reason: "Quitclaim stated amount (₱52,000.00) vs Computed Final Pay (₱48,500.00)",
            approver_name: signerName,
            role: currentApproverRole
          })
        });
        const data = await res.json();
        closeSplitEscrowModal();
        activeDossier.overall_status = 'PARTIALLY_DISBURSED';
        if (!activeDossier.escrow_details) {
          activeDossier.escrow_details = {
            undisputed_amount: 48500.00,
            escrow_amount: 3500.00,
            reason: "Quitclaim disparity",
            status: 'ESCROW_ACTIVE'
          };
        }
        showDynamicToast("Split Pay Disbursed!", `₱48,500.00 released to employee · ₱3,500.00 held in Escrow.`, "success");
        selectDossier(activeDossier.dossier_id);
        renderQueue();
      } catch (err) {
        showDynamicToast("Split Escrow Failed", err.message, "error");
      }
    }

    function switchApproverRole(role) {
      currentApproverRole = role;
      const btnIT = document.getElementById('roleBtnIT');
      const btnFin = document.getElementById('roleBtnFinance');
      const btnHR = document.getElementById('roleBtnHR');
      const btnAdmin = document.getElementById('roleBtnAdmin');
      const currentRoleLabel = document.getElementById('currentRoleLabel');

      const activeClass = "px-3.5 py-2 rounded-xl text-xs font-bold transition flex items-center space-x-2 bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm";
      const inactiveClass = "px-3.5 py-2 rounded-xl text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition flex items-center space-x-2";

      if (btnIT) btnIT.className = role === 'IT_APPROVER' ? activeClass : inactiveClass;
      if (btnFin) btnFin.className = role === 'FINANCE_APPROVER' ? activeClass : inactiveClass;
      if (btnHR) btnHR.className = role === 'HR_APPROVER' ? activeClass : inactiveClass;
      if (btnAdmin) btnAdmin.className = role === 'ADMIN_APPROVER' ? activeClass : inactiveClass;

      if (role === 'IT_APPROVER') {
        currentRoleLabel.textContent = 'Alex Tan (IT Clearance Lead)';
      } else if (role === 'FINANCE_APPROVER') {
        currentRoleLabel.textContent = 'Roberto Ong (Finance & Payroll Lead)';
      } else if (role === 'HR_APPROVER') {
        currentRoleLabel.textContent = 'Grace Diaz (HR Operations Manager)';
      } else if (role === 'ADMIN_APPROVER') {
        currentRoleLabel.textContent = 'Elena Cruz (Facilities & Admin Lead)';
      }

      if (activeDossier) {
        renderRoleWorkDesk(role, activeDossier);
      }
    }

    function renderRoleWorkDesk(role, d) {
      const container = document.getElementById('roleSpecificDesk');
      if (!container) return;

      const hasITFlag = d.flags_summary && (d.flags_summary.includes("FLAG_ACCOUNTABILITY_NOTED") || d.flags_summary.includes("FLAG_MISSING_FIELD"));
      const hasFinanceFlag = d.flags_summary && (d.flags_summary.includes("FLAG_AMOUNT_MISMATCH") || d.flags_summary.includes("FLAG_FORMAT_MISMATCH"));

      if (role === 'IT_APPROVER') {
        container.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-black/[0.05] dark:border-white/[0.06]">
            <div class="flex items-center space-x-2">
              <i class="fa-solid fa-laptop-code text-apple-blue"></i>
              <span class="font-bold text-xs uppercase tracking-wider text-neutral-800 dark:text-neutral-200">IT Clearance Check & Asset Turnover</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${hasITFlag ? 'bg-red-500/10 text-apple-red' : 'bg-emerald-500/10 text-apple-green'}">
              ${hasITFlag ? 'Action Required (Hold)' : 'Hardware Clean'}
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-2">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 flex items-center justify-between">
                <span>Hardware Assets Surrendered</span>
                <span class="text-[9px] font-mono text-neutral-400">Inventory S/N</span>
              </div>
              <div class="space-y-1.5 text-xs">
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" ${hasITFlag ? '' : 'checked'} class="rounded text-apple-blue focus:ring-0" />
                  <span class="text-neutral-700 dark:text-neutral-300">Lenovo ThinkPad T14s (S/N: 20WM-0045PH)</span>
                </label>
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" checked class="rounded text-apple-blue focus:ring-0" />
                  <span class="text-neutral-700 dark:text-neutral-300">65W USB-C AC Power Adapter</span>
                </label>
                <label class="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" checked class="rounded text-apple-blue focus:ring-0" />
                  <span class="text-neutral-700 dark:text-neutral-300">Jabra Evolve2 Headset (Asset #HW-8812)</span>
                </label>
              </div>
            </div>

            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-2">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 flex items-center justify-between">
                <span>Identity & Access Revocation</span>
                <span class="text-[9px] font-mono text-apple-green">SSO Synced</span>
              </div>
              <div class="space-y-1.5 text-xs">
                <div class="flex items-center justify-between">
                  <span class="text-neutral-600 dark:text-neutral-300">Lark Suite Enterprise Account:</span>
                  <span class="text-[10px] font-bold text-apple-amber">Pending Sign-off</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-neutral-600 dark:text-neutral-300">GitHub & AWS Production IAM:</span>
                  <span class="text-[10px] font-bold text-apple-green">Revoked ✓</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-neutral-600 dark:text-neutral-300">24th Floor RFID Turnstile Badge:</span>
                  <span class="text-[10px] font-bold ${hasITFlag ? 'text-apple-red' : 'text-apple-green'}">${hasITFlag ? 'Not Surrendered' : 'Deactivated ✓'}</span>
                </div>
              </div>
            </div>
          </div>
        `;
      } else if (role === 'FINANCE_APPROVER') {
        container.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-black/[0.05] dark:border-white/[0.06]">
            <div class="flex items-center space-x-2">
              <i class="fa-solid fa-money-check-dollar text-apple-green"></i>
              <span class="font-bold text-xs uppercase tracking-wider text-neutral-800 dark:text-neutral-200">Finance & Last Pay Computation Reconciliation</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold ${hasFinanceFlag ? 'bg-red-500/10 text-apple-red' : 'bg-emerald-500/10 text-apple-green'}">
              ${hasFinanceFlag ? 'Discrepancy Detected' : 'Formula Reconciled'}
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-1.5 text-xs">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06] flex justify-between">
                <span>Final Pay Itemization</span>
                <span class="font-mono">PHP (₱)</span>
              </div>
              <div class="flex justify-between"><span>Pro-rated Basic Salary (Aug 1–31):</span><span class="font-mono font-medium">₱32,000.00</span></div>
              <div class="flex justify-between"><span>13th Month Pay Accrual (8 mos):</span><span class="font-mono font-medium">₱16,500.00</span></div>
              <div class="flex justify-between"><span>Tax Annualization Withholding Refund:</span><span class="font-mono text-apple-green font-medium">+₱1,200.00</span></div>
              <div class="flex justify-between"><span>Equipment Deduction (Lost Adapter):</span><span class="font-mono text-apple-red font-medium">-₱1,200.00</span></div>
              <div class="pt-1.5 border-t border-black/[0.04] dark:border-white/[0.06] flex justify-between font-bold text-neutral-900 dark:text-white">
                <span>Computed Net Last Pay:</span>
                <span class="font-mono text-apple-blue text-sm">₱48,500.00</span>
              </div>
            </div>

            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-2 text-xs">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06] flex justify-between">
                <span>Discrepancy Analysis</span>
                <span class="font-mono text-apple-red">DIFF</span>
              </div>
              <div class="space-y-1">
                <div class="flex justify-between"><span>Quit Claim Signed Figure:</span><span class="font-mono font-bold ${hasFinanceFlag ? 'text-apple-red' : 'text-apple-green'}">₱52,000.00</span></div>
                <div class="flex justify-between"><span>HR/Payroll Ledger:</span><span class="font-mono font-bold text-neutral-800 dark:text-neutral-200">₱48,500.00</span></div>
                <div class="p-2 rounded-lg ${hasFinanceFlag ? 'bg-red-500/10 text-apple-red' : 'bg-emerald-500/10 text-apple-green'} font-semibold text-[11px] flex items-center justify-between">
                  <span>${hasFinanceFlag ? 'Disparity: +₱3,500.00' : 'Perfect Match (₱0.00 diff)'}</span>
                  <i class="fa-solid ${hasFinanceFlag ? 'fa-circle-exclamation' : 'fa-circle-check'}"></i>
                </div>
              </div>
              <div class="text-[10px] text-neutral-400">Bank Target: GCash 0917-XXX-8819 (Verified Holder Name Match)</div>
            </div>
          </div>
        `;
      } else if (role === 'HR_APPROVER') {
        container.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-black/[0.05] dark:border-white/[0.06]">
            <div class="flex items-center space-x-2">
              <i class="fa-solid fa-user-tie text-apple-purple"></i>
              <span class="font-bold text-xs uppercase tracking-wider text-neutral-800 dark:text-neutral-200">HR Separation Compliance & COE Release Desk</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-500/10 text-apple-purple">
              Compliance Review
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 text-xs">
            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-1.5">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06]">Separation Compliance Checklist</div>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-purple" /><span>Resignation Letter Accepted & Signed by Dept VP</span></label>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-purple" /><span>Lark Exit Interview Survey Completed</span></label>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" class="rounded text-apple-purple" /><span>All 4 Department Sign-off Stamps Verified</span></label>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-purple" /><span>Notarized Release & Quit Claim Form Stored</span></label>
            </div>

            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-2">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06]">Post-Clearance Artifacts</div>
              <div class="space-y-1 text-neutral-600 dark:text-neutral-300">
                <div class="flex justify-between"><span>Certificate of Employment (COE):</span><span class="font-bold text-apple-green">Draft Ready</span></div>
                <div class="flex justify-between"><span>BIR Form 2316 (Tax Cert):</span><span class="font-bold text-apple-amber">Auto-generating</span></div>
                <div class="flex justify-between"><span>Alumni Network Invite:</span><span class="font-bold text-neutral-400">Pending Release</span></div>
              </div>
            </div>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-black/[0.05] dark:border-white/[0.06]">
            <div class="flex items-center space-x-2">
              <i class="fa-solid fa-building-user text-apple-amber"></i>
              <span class="font-bold text-xs uppercase tracking-wider text-neutral-800 dark:text-neutral-200">Facilities & Administrative Asset Clearance</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-apple-amber">
              Facilities Audit
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 text-xs">
            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-1.5">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06]">Physical Access & Assets</div>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-amber" /><span>Office Locker #24 Key Surrendered</span></label>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-amber" /><span>Taguig Parking Deck RFID Transponder</span></label>
              <label class="flex items-center space-x-2 cursor-pointer"><input type="checkbox" checked class="rounded text-apple-amber" /><span>Laminated Company ID Badge Cut & Disposed</span></label>
            </div>
            <div class="p-3 rounded-xl bg-white dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.06] space-y-2">
              <div class="text-[11px] font-bold text-neutral-700 dark:text-neutral-300 pb-1 border-b border-black/[0.04] dark:border-white/[0.06]">Admin Sign-Off Status</div>
              <p class="text-neutral-600 dark:text-neutral-300 text-[11px]">All physical locker amenities and security access credentials have been returned in satisfactory condition.</p>
              <div class="text-[10px] font-bold text-apple-green">✓ Facilities Clearance Approved</div>
            </div>
          </div>
        `;
      }
    }

    async function selectDossier(dossierId) {
      const d = allDossiersCache.find(item => item.dossier_id === dossierId);
      if (!d) return;

      activeDossier = d;
      activeDocIndex = 0;
      renderQueue();

      // Populate Hero Card
      const initials = d.employee_name.split(' ').map(n => n[0]).slice(0, 2).join('');
      document.getElementById('apprAvatar').textContent = initials;
      document.getElementById('apprEmpName').textContent = d.employee_name;
      document.getElementById('apprEmpIdBadge').textContent = d.employee_id || d.dossier_id;
      document.getElementById('apprDeptRole').textContent = `${d.department} · ${d.job_level}`;
      document.getElementById('apprSubText').textContent = `${d.company} · ${d.branch} · Separation: ${d.eoc_date} (${d.reason_for_separation})`;

      // Status Badge & Pulse Dot
      const statusBadge = document.getElementById('apprStatusBadge');
      const statusText = document.getElementById('apprStatusText');
      const pulseDot = document.getElementById('apprPulseDot');

      if (d.overall_status === 'APPROVED') {
        statusText.textContent = 'APPROVED';
        statusBadge.className = 'text-xs font-bold px-3 py-1.5 rounded-full bg-emerald-500/15 text-apple-green border border-emerald-500/30 flex items-center space-x-1.5';
        pulseDot.className = 'w-2 h-2 rounded-full bg-apple-green';
      } else if (d.ai_flags_count > 0) {
        statusText.textContent = `${d.ai_flags_count} DISCREPANCY FLAGS`;
        statusBadge.className = 'text-xs font-bold px-3 py-1.5 rounded-full bg-red-500/10 text-apple-red border border-red-500/20 flex items-center space-x-1.5';
        pulseDot.className = 'w-2 h-2 rounded-full bg-apple-red apple-pulse-red';
      } else {
        statusText.textContent = 'READY FOR SIGN-OFF';
        statusBadge.className = 'text-xs font-bold px-3 py-1.5 rounded-full bg-emerald-500/10 text-apple-green border border-emerald-500/20 flex items-center space-x-1.5';
        pulseDot.className = 'w-2 h-2 rounded-full bg-apple-green apple-pulse-green';
      }

      // Check Split Escrow Button Visibility
      const btnSplit = document.getElementById('btnSplitEscrowAction');
      if (btnSplit) {
        if (d.escrow_details || (d.flags_summary && d.flags_summary.includes("FLAG_AMOUNT_MISMATCH"))) {
          btnSplit.classList.remove('hidden');
          if (d.overall_status === 'PARTIALLY_DISBURSED') {
            btnSplit.innerHTML = '<i class="fa-solid fa-coins mr-2"></i> Escrow Active (₱3.5K Held)';
            btnSplit.classList.add('opacity-80');
          } else {
            btnSplit.innerHTML = '<i class="fa-solid fa-scale-balanced mr-2"></i> Split Escrow Release';
            btnSplit.classList.remove('opacity-80');
          }
        } else {
          btnSplit.classList.add('hidden');
        }
      }

      // Check SLA Urgency Tag
      const urgencyTag = document.getElementById('apprUrgencyTag');
      if (urgencyTag) {
        if (d.sla_auto_forwarded) {
          urgencyTag.textContent = 'Auto-Forwarded to OIC';
          urgencyTag.className = 'text-apple-purple font-mono font-bold px-1.5 py-0.2 rounded bg-purple-500/10';
        } else {
          urgencyTag.textContent = '18h Remaining';
          urgencyTag.className = 'text-apple-amber font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500/10';
        }
      }

      // Progression Steps
      updateProgressPipeline(d);

      // Render Role-Specific Work Desk
      renderRoleWorkDesk(currentApproverRole, d);

      // Render Document Tabs
      renderDocTabs(d);

      // Load Pre-check on primary document
      await inspectDossierDocument(d.sample_file, d.sample_type);
    }

    function updateProgressPipeline(d) {
      // 1. Update Parallel Matrix Nodes
      const nodes = d.nodes || {
        "IT": {"name": "IT Clearance", "signer": "Alex Tan", "status": "PENDING", "summary": "Awaiting IT check"},
        "ADMIN": {"name": "Facilities & Lockers", "signer": "Elena Cruz", "status": "CLEARED", "summary": "Locker cleared"},
        "FINANCE": {"name": "Finance & Payroll", "signer": "Roberto Ong", "status": "PENDING", "summary": "Auditing payroll ledger"},
        "HR": {"name": "HR Final Release", "signer": "Grace Diaz", "status": "LOCKED", "summary": "Requires 3 depts"}
      };

      function styleNode(key, boxId, badgeId, signerId, summaryId, btnId) {
        const node = nodes[key] || {status: "PENDING", signer: "", summary: ""};
        const badge = document.getElementById(badgeId);
        const signer = document.getElementById(signerId);
        const summary = document.getElementById(summaryId);
        const btn = document.getElementById(btnId);
        const box = document.getElementById(boxId);

        if (signer) signer.textContent = `Signer: ${node.signer || 'Unassigned'}`;
        if (summary) summary.textContent = node.summary || (node.status === 'CLEARED' ? 'Verified ✓' : 'In review');

        if (node.status === 'CLEARED') {
          if (badge) {
            badge.textContent = 'CLEARED ✓';
            badge.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-apple-green';
          }
          if (box) box.className = 'p-3.5 rounded-2xl bg-emerald-500/[0.04] dark:bg-emerald-950/20 border border-emerald-500/20 shadow-sm space-y-2 transition';
          if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-check mr-1 text-[9px]"></i><span>Cleared ✓</span>';
            btn.className = 'w-full py-1.5 rounded-xl bg-emerald-500/10 text-apple-green text-[10px] font-bold transition flex items-center justify-center space-x-1 cursor-default';
            btn.disabled = true;
          }
        } else if (node.status === 'FLAGGED') {
          if (badge) {
            badge.textContent = 'FLAGGED';
            badge.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-red-500/10 text-apple-red';
          }
          if (box) box.className = 'p-3.5 rounded-2xl bg-red-500/[0.04] dark:bg-red-950/20 border border-red-500/20 shadow-sm space-y-2 transition';
          if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation mr-1 text-[9px]"></i><span>Sign & Override</span>';
            btn.className = 'w-full py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-apple-red text-[10px] font-bold transition flex items-center justify-center space-x-1';
            btn.disabled = false;
          }
        } else {
          if (badge) {
            badge.textContent = 'PENDING';
            badge.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-apple-amber';
          }
          if (box) box.className = 'p-3.5 rounded-2xl bg-white dark:bg-neutral-900 border border-black/[0.05] dark:border-white/[0.06] shadow-sm space-y-2 transition';
          if (btn) {
            btn.innerHTML = '<i class="fa-solid fa-pen-nib mr-1 text-[9px]"></i><span>Sign ' + key + ' Node</span>';
            btn.className = 'w-full py-1.5 rounded-xl bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 text-[10px] font-bold transition flex items-center justify-center space-x-1';
            btn.disabled = false;
          }
        }
      }

      styleNode('IT', 'pNodeBoxIT', 'pNodeBadgeIT', 'pNodeSignerIT', 'pNodeSummaryIT', 'btnSignNodeIT');
      styleNode('ADMIN', 'pNodeBoxAdmin', 'pNodeBadgeAdmin', 'pNodeSignerAdmin', 'pNodeSummaryAdmin', 'btnSignNodeAdmin');
      styleNode('FINANCE', 'pNodeBoxFinance', 'pNodeBadgeFinance', 'pNodeSignerFinance', 'pNodeSummaryFinance', 'btnSignNodeFinance');

      // Check HR Node Convergence
      const itClear = nodes.IT && nodes.IT.status === 'CLEARED';
      const adminClear = nodes.ADMIN && nodes.ADMIN.status === 'CLEARED';
      const finClear = nodes.FINANCE && nodes.FINANCE.status === 'CLEARED';
      const hrNode = nodes.HR || {status: "LOCKED"};

      let clearedCount = (itClear ? 1 : 0) + (adminClear ? 1 : 0) + (finClear ? 1 : 0);
      const allDeptsClear = clearedCount === 3;

      const badgeHR = document.getElementById('pNodeBadgeHR');
      const signerHR = document.getElementById('pNodeSignerHR');
      const summaryHR = document.getElementById('pNodeSummaryHR');
      const btnHR = document.getElementById('btnSignNodeHR');
      const boxHR = document.getElementById('pNodeBoxHR');

      if (signerHR) signerHR.textContent = `Signer: Grace Diaz`;

      if (hrNode.status === 'CLEARED' || d.overall_status === 'APPROVED') {
        if (badgeHR) {
          badgeHR.textContent = 'DISBURSED ✓';
          badgeHR.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-apple-green';
        }
        if (summaryHR) summaryHR.textContent = 'Final pay sent, COE released';
        if (boxHR) boxHR.className = 'p-3.5 rounded-2xl bg-emerald-500/[0.06] dark:bg-emerald-950/20 border border-emerald-500/30 shadow-sm space-y-2 transition';
        if (btnHR) {
          btnHR.innerHTML = '<i class="fa-solid fa-circle-check mr-1 text-[9px]"></i><span>Release Complete</span>';
          btnHR.className = 'w-full py-1.5 rounded-xl bg-emerald-500/15 text-apple-green text-[10px] font-bold cursor-default flex items-center justify-center space-x-1';
          btnHR.disabled = true;
        }
      } else if (allDeptsClear) {
        if (badgeHR) {
          badgeHR.textContent = '🔓 READY';
          badgeHR.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-blue-500/15 text-lark-blue animate-pulse';
        }
        if (summaryHR) summaryHR.textContent = 'All 3 parallel nodes cleared!';
        if (boxHR) boxHR.className = 'p-3.5 rounded-2xl bg-blue-500/[0.04] dark:bg-blue-950/20 border border-blue-500/30 shadow-sm space-y-2 transition';
        if (btnHR) {
          btnHR.innerHTML = '<i class="fa-solid fa-signature mr-1 text-[9px]"></i><span>Disburse Final Pay</span>';
          btnHR.className = 'w-full py-1.5 rounded-xl bg-apple-green hover:bg-emerald-600 text-white text-[10px] font-bold shadow-sm transition flex items-center justify-center space-x-1';
          btnHR.disabled = false;
        }
      } else {
        if (badgeHR) {
          badgeHR.textContent = `🔒 ${clearedCount}/3 CLEARED`;
          badgeHR.className = 'text-[9px] font-bold px-2 py-0.5 rounded-full bg-neutral-200/80 dark:bg-neutral-800 text-neutral-500 font-mono';
        }
        if (summaryHR) summaryHR.textContent = `Waiting on ${!itClear ? 'IT ' : ''}${!adminClear ? 'Admin ' : ''}${!finClear ? 'Finance' : ''}`;
        if (boxHR) boxHR.className = 'p-3.5 rounded-2xl bg-neutral-100/50 dark:bg-neutral-900 border border-black/[0.04] dark:border-white/[0.05] shadow-sm space-y-2 opacity-80';
        if (btnHR) {
          btnHR.innerHTML = '<i class="fa-solid fa-lock mr-1 text-[9px]"></i><span>Release Final Pay</span>';
          btnHR.className = 'w-full py-1.5 rounded-xl bg-neutral-200/60 dark:bg-neutral-800 text-neutral-400 text-[10px] font-bold cursor-not-allowed flex items-center justify-center space-x-1';
          btnHR.disabled = true;
        }
      }

      // 2. Also update Sequential Boxes (for fallback view)
      const step = d.stage_step || 1;
      const s1 = document.getElementById('step1Box');
      const s2 = document.getElementById('step2Box');
      const s3 = document.getElementById('step3Box');
      const s4 = document.getElementById('step4Box');

      const s1Status = document.getElementById('step1Status');
      const s2Status = document.getElementById('step2Status');
      const s3Status = document.getElementById('step3Status');
      const s4Status = document.getElementById('step4Status');

      const baseInactive = "p-3 rounded-xl border border-black/[0.05] dark:border-white/[0.08] bg-white dark:bg-neutral-800 text-neutral-400 transition";
      const baseActive = "p-3 rounded-xl border border-lark-blue bg-blue-50/60 dark:bg-blue-950/30 text-lark-blue font-semibold transition";
      const baseCleared = "p-3 rounded-xl border border-emerald-500/30 bg-emerald-50/50 dark:bg-emerald-950/20 text-apple-green font-semibold transition";

      s1.className = baseInactive;
      s2.className = baseInactive;
      s3.className = baseInactive;
      s4.className = baseInactive;

      if (d.ai_flags_count > 0 && d.flags_summary && d.flags_summary.includes("FLAG_ACCOUNTABILITY_NOTED")) {
        s1.className = "p-3 rounded-xl border border-red-500/30 bg-red-50/50 dark:bg-red-950/20 text-apple-red font-semibold transition";
        s1Status.textContent = "IT Hold";
      } else {
        s1.className = baseCleared;
        s1Status.textContent = "Cleared ✓";
      }

      if (step >= 2) {
        if (d.flags_summary && d.flags_summary.includes("FLAG_AMOUNT_MISMATCH")) {
          s2.className = "p-3 rounded-xl border border-red-500/30 bg-red-50/50 dark:bg-red-950/20 text-apple-red font-semibold transition";
          s2Status.textContent = "Disparity";
        } else {
          s2.className = step > 2 ? baseCleared : baseActive;
          s2Status.textContent = step > 2 ? "Audited ✓" : "In Review";
        }
      }

      if (step >= 3) {
        s3.className = step > 3 ? baseCleared : baseActive;
        s3Status.textContent = step > 3 ? "Signed ✓" : "Reviewing";
      }

      if (step >= 4) {
        s4.className = d.overall_status === 'APPROVED' ? baseCleared : baseActive;
        s4Status.textContent = d.overall_status === 'APPROVED' ? "Released ✓" : "Disbursement";
      }
    }

    function renderDocTabs(d) {
      const tabsBar = document.getElementById('docTabsBar');
      const docs = d.docs || [
        {"title": "Primary Document", "file": d.sample_file, "type": d.sample_type, "has_flags": d.ai_flags_count > 0}
      ];

      tabsBar.innerHTML = docs.map((doc, idx) => {
        const isSelected = idx === activeDocIndex;
        const tabClass = isSelected 
          ? "px-3.5 py-1.5 rounded-xl font-bold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm border border-black/[0.04] dark:border-white/[0.06]"
          : "px-3.5 py-1.5 rounded-xl font-medium text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition";

        const flagDot = doc.has_flags 
          ? '<span class="w-2 h-2 rounded-full bg-apple-red inline-block ml-1.5 apple-pulse-red"></span>' 
          : '<span class="w-2 h-2 rounded-full bg-apple-green inline-block ml-1.5"></span>';

        return `
          <button onclick="switchDocTab(${idx})" class="${tabClass} flex items-center space-x-1">
            <span>${doc.title}</span>
            ${flagDot}
          </button>
        `;
      }).join('');
    }

    async function switchDocTab(index) {
      activeDocIndex = index;
      renderDocTabs(activeDossier);
      const doc = activeDossier.docs[index];
      await inspectDossierDocument(doc.file, doc.type);
    }

    async function inspectDossierDocument(fileName, docType) {
      document.getElementById('apprDocLink').href = `/samples/${fileName}`;
      document.getElementById('docTypeInspectorBadge').textContent = docType;

      // Preview frame
      const preview = document.getElementById('apprDocPreview');
      if (fileName.endsWith('.pdf')) {
        preview.innerHTML = `<iframe src="/samples/${fileName}" class="w-full h-80 rounded-xl border border-black/[0.05] dark:border-white/[0.06] bg-white shadow-inner" frameborder="0"></iframe>`;
      } else {
        preview.innerHTML = `<img src="/samples/${fileName}" class="max-h-72 rounded-xl object-contain border border-black/[0.05] dark:border-white/[0.06] bg-white shadow-sm" />`;
      }

      // Call precheck
      try {
        const fileRes = await fetch(`/samples/${fileName}`);
        const blob = await fileRes.blob();
        const formData = new FormData();
        formData.append('file', blob, fileName);
        formData.append('document_type', docType);

        const checkRes = await fetch('/api/precheck', { method: 'POST', body: formData });
        const checkData = await checkRes.json();

        document.getElementById('apprConfidenceText').textContent = `${Math.round(checkData.overall_confidence * 100)}%`;
        if (checkData.metadata && checkData.metadata.file_hash_sha256) {
          document.getElementById('docShaShort').textContent = `SHA: ${checkData.metadata.file_hash_sha256.slice(0, 8)}...`;
        }

        const flagsList = document.getElementById('apprFlagsList');
        const overrideBox = document.getElementById('apprOverrideBox');

        if (!checkData.flags || checkData.flags.length === 0) {
          flagsList.innerHTML = `
            <div class="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs flex items-center space-x-3 shadow-sm">
              <div class="w-7 h-7 rounded-lg bg-apple-green text-white flex items-center justify-center shrink-0">
                <i class="fa-solid fa-shield-check"></i>
              </div>
              <div>
                <div class="font-bold">Apple Intelligence Pre-Check Verified</div>
                <div class="text-[11px] text-neutral-600 dark:text-neutral-300">All signatures, settlement calculations, and employee identity fields match corporate records.</div>
              </div>
            </div>
          `;
          overrideBox.classList.add('hidden');
        } else {
          overrideBox.classList.remove('hidden');
          flagsList.innerHTML = checkData.flags.map(f => {
            const isBlocker = f.severity === 'BLOCKER';
            const bgClass = isBlocker ? 'bg-red-500/10 border-red-500/20 text-neutral-800 dark:text-neutral-200' : 'bg-amber-500/10 border-amber-500/20 text-neutral-800 dark:text-neutral-200';
            const badgeClass = isBlocker ? 'bg-apple-red text-white' : 'bg-apple-amber text-white';
            const icon = isBlocker ? 'fa-solid fa-circle-xmark text-apple-red' : 'fa-solid fa-triangle-exclamation text-apple-amber';

            return `
              <div class="p-3 rounded-xl border text-xs flex items-start space-x-3 ${bgClass} shadow-sm">
                <i class="${icon} text-base mt-0.5 shrink-0"></i>
                <div class="flex-1">
                  <div class="font-bold flex items-center justify-between">
                    <span class="font-mono tracking-tight">${f.code}</span>
                    <span class="text-[9px] uppercase tracking-wider font-mono font-bold px-2 py-0.5 rounded-full ${badgeClass}">${f.severity}</span>
                  </div>
                  <div class="mt-1 text-neutral-600 dark:text-neutral-300 text-[11px]">${f.message}</div>
                </div>
              </div>
            `;
          }).join('');
        }

        // Populate Extracted Fields Inspector
        renderExtractedFieldsInspector(checkData);

      } catch (err) {
        console.error(err);
      }
    }

    function renderExtractedFieldsInspector(data) {
      const container = document.getElementById('extractedFieldsInspector');
      if (!container || !data.fields) return;

      const f = data.fields;
      let rows = [];

      if (data.document_type === 'QUIT_CLAIM') {
        if (f.employee_name) rows.push({label: 'Employee Name', val: f.employee_name.raw_value, conf: f.employee_name.confidence, flagged: f.employee_name.is_flagged});
        if (f.settlement_amount_figures) rows.push({label: 'Settlement Amount', val: '₱' + Number(f.settlement_amount_figures.normalized_value || 0).toLocaleString(), conf: f.settlement_amount_figures.confidence, flagged: f.settlement_amount_figures.is_flagged});
        if (f.amounts_match) rows.push({label: 'Figures & Words Match', val: f.amounts_match.normalized_value ? 'Match ✓' : 'Mismatch ⚠️', conf: f.amounts_match.confidence, flagged: !f.amounts_match.normalized_value});
        if (f.employee_signature_present) rows.push({label: 'Employee Signature', val: f.employee_signature_present.normalized_value ? 'Detected ✓' : 'Missing ⚠️', conf: f.employee_signature_present.confidence, flagged: !f.employee_signature_present.normalized_value});
        if (f.notary_present) rows.push({label: 'Notary Seal', val: f.notary_present.normalized_value ? 'Verified ✓' : 'Absent', conf: f.notary_present.confidence, flagged: false});
        if (f.waiver_clauses_intact) rows.push({label: 'Waiver Clauses', val: f.waiver_clauses_intact.normalized_value ? 'Intact ✓' : 'Modified ⚠️', conf: f.waiver_clauses_intact.confidence, flagged: !f.waiver_clauses_intact.normalized_value});
      } else if (data.document_type === 'BANK_ENROLLMENT') {
        if (f.account_holder_name) rows.push({label: 'Account Holder', val: f.account_holder_name.raw_value, conf: f.account_holder_name.confidence, flagged: f.account_holder_name.is_flagged});
        if (f.institution) rows.push({label: 'Platform / Bank', val: f.institution.normalized_value, conf: f.institution.confidence, flagged: f.institution.is_flagged});
        if (f.account_number) rows.push({label: 'Account Number', val: f.account_number.raw_value, conf: f.account_number.confidence, flagged: f.account_number.is_flagged});
        if (f.account_number_format_valid) rows.push({label: 'Format Valid', val: f.account_number_format_valid.normalized_value ? 'Valid Format ✓' : 'Invalid Format ⚠️', conf: f.account_number_format_valid.confidence, flagged: !f.account_number_format_valid.normalized_value});
        if (f.proof_type) rows.push({label: 'Proof Category', val: f.proof_type.normalized_value, conf: f.proof_type.confidence, flagged: false});
      } else if (data.document_type === 'CLEARANCE_SHEET') {
        if (f.employee_name) rows.push({label: 'Employee Name', val: f.employee_name.raw_value, conf: f.employee_name.confidence, flagged: f.employee_name.is_flagged});
        if (f.all_departments_cleared) rows.push({label: 'All Depts Cleared', val: f.all_departments_cleared.normalized_value ? 'Complete ✓' : 'Pending ⚠️', conf: f.all_departments_cleared.confidence, flagged: !f.all_departments_cleared.normalized_value});
        if (f.department_statuses) {
          f.department_statuses.forEach(ds => {
            rows.push({
              label: `${ds.department} Clearance`,
              val: ds.is_cleared.normalized_value ? 'Cleared ✓' : 'Hold Active ⚠️',
              conf: ds.is_cleared.confidence,
              flagged: !ds.is_cleared.normalized_value
            });
          });
        }
      }

      container.innerHTML = rows.map(r => `
        <div class="p-2 rounded-xl bg-white dark:bg-neutral-800/80 border border-black/[0.04] dark:border-white/[0.05] flex items-center justify-between">
          <div class="min-w-0 flex-1 pr-2">
            <div class="text-[10px] text-neutral-400 font-medium">${r.label}</div>
            <div class="font-bold text-xs ${r.flagged ? 'text-apple-red' : 'text-neutral-800 dark:text-neutral-200'} truncate">${r.val}</div>
          </div>
          <div class="text-right shrink-0">
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded ${r.flagged ? 'bg-red-500/10 text-apple-red' : 'bg-emerald-500/10 text-apple-green'} font-bold">
              ${Math.round(r.conf * 100)}%
            </span>
          </div>
        </div>
      `).join('');
    }

    async function submitApproverDeskDecision(action) {
      if (!activeDossier) return;
      const role = currentApproverRole;
      const overrideNotes = document.getElementById('apprOverrideNotes').value.trim();

      if (action === 'APPROVE' && activeDossier.ai_flags_count > 0 && !overrideNotes) {
        showDynamicToast("Override Rationale Required", "Please justify approving with active blocker flags.", "error");
        document.getElementById('apprOverrideNotes').focus();
        return;
      }

      try {
        const res = await fetch('/api/approvals/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            document_id: activeDossier.dossier_id,
            approver_id: "USR-ACTIVE-APPROVER",
            role: role,
            action: action,
            flags_reviewed: activeDossier.flags_summary || [],
            override_justification: overrideNotes,
          })
        });
        await res.json();
        showDynamicToast(`Decision Logged: ${action}`, `${activeDossier.employee_name} (${activeDossier.dossier_id}) updated.`, "success");
        document.getElementById('apprOverrideNotes').value = '';
        await loadDossiersQueue();
      } catch (err) {
        showDynamicToast("Action Failed", err.message, "error");
      }
    }

    // Developer Harness Functions
    async function loadHarnessSamples() {
      try {
        const res = await fetch('/api/samples');
        const samples = await res.json();
        const container = document.getElementById('harnessSamplesList');
        container.innerHTML = samples.map(s => `
          <button onclick="runHarnessTest('${s.file_name}', '${s.document_type}')" class="w-full text-left p-2.5 rounded-xl bg-neutral-50 dark:bg-apple-elevatedDark hover:bg-neutral-100 dark:hover:bg-neutral-700/60 border border-black/[0.04] dark:border-white/[0.06] text-xs flex justify-between items-center transition">
            <div>
              <span class="font-semibold text-neutral-800 dark:text-neutral-200 block">${s.file_name}</span>
              <span class="text-[10px] text-neutral-500 uppercase">${s.document_type}</span>
            </div>
            <i class="fa-solid fa-play text-apple-blue text-xs"></i>
          </button>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    async function runHarnessTest(fileName, docType) {
      document.getElementById('harnessEmptyState').classList.add('hidden');
      document.getElementById('harnessResultContent').classList.remove('hidden');

      const fileRes = await fetch(`/samples/${fileName}`);
      const blob = await fileRes.blob();
      const formData = new FormData();
      formData.append('file', blob, fileName);
      formData.append('document_type', docType);

      const res = await fetch('/api/precheck', { method: 'POST', body: formData });
      const data = await res.json();

      document.getElementById('harnessDocType').textContent = data.document_type;
      document.getElementById('harnessFileName').textContent = data.metadata.file_name;
      document.getElementById('harnessConfidence').textContent = Math.round(data.overall_confidence * 100) + '%';
      document.getElementById('harnessJsonPre').textContent = JSON.stringify(data, null, 2);

      const flagsBox = document.getElementById('harnessFlagsBox');
      if (!data.flags.length) {
        flagsBox.innerHTML = '<p class="text-xs text-apple-green font-semibold">0 Flags detected. Clean validation.</p>';
      } else {
        flagsBox.innerHTML = data.flags.map(f => `
          <div class="p-2 rounded bg-red-500/10 text-apple-red text-xs font-semibold">
            ${f.code} [${f.severity}]: ${f.message}
          </div>
        `).join('');
      }
      loadAuditLogs();
    }

    async function loadAuditLogs() {
      try {
        const res = await fetch('/api/audit-logs');
        const logs = await res.json();
        const container = document.getElementById('harnessAuditContainer');
        if (!container) return;
        container.innerHTML = logs.map(l => `
          <div class="p-2 rounded-lg bg-neutral-50 dark:bg-apple-elevatedDark border border-black/[0.04] dark:border-white/[0.06] text-[11px]">
            <div class="flex justify-between font-semibold">
              <span>${l.file_name || l.dossier_id}</span>
              <span class="text-[10px] text-neutral-400">${l.action || l.document_type}</span>
            </div>
            <div class="text-[9px] text-neutral-400 font-mono mt-0.5">${l.timestamp.slice(11, 19)} · ${l.log_type}</div>
          </div>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    // Theme Switcher (Default: Light Mode)
    function initTheme() {
      const savedTheme = localStorage.getItem('theme');
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        document.getElementById('themeIconSun').classList.remove('hidden');
        document.getElementById('themeIconMoon').classList.add('hidden');
      } else {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
        document.getElementById('themeIconSun').classList.add('hidden');
        document.getElementById('themeIconMoon').classList.remove('hidden');
      }
    }

    function toggleTheme() {
      const isDark = document.documentElement.classList.contains('dark');
      if (isDark) {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
        localStorage.setItem('theme', 'light');
        document.getElementById('themeIconSun').classList.add('hidden');
        document.getElementById('themeIconMoon').classList.remove('hidden');
      } else {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        localStorage.setItem('theme', 'dark');
        document.getElementById('themeIconSun').classList.remove('hidden');
        document.getElementById('themeIconMoon').classList.add('hidden');
      }
    }

    // Startup
    initTheme();
    loadDossiersQueue();
    loadHarnessSamples();
    loadAuditLogs();
  </script>
</body>
</html>
"""


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
