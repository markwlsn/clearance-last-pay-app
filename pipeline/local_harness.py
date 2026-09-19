"""Local test harness for Clearance & Last Pay document pre-check pipeline.
Supports:
1. Employee Submission View (Faithfully recreating the Lark Approval Form in Apple Minimalist style)
2. Role-Based Approver Dashboard (IT, Finance/Payroll, HR, Admin) with AI flag review & preview
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
    version="2.0.0",
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
        "department": "Information Technology",
        "company": "CMG Group of Companies",
        "unit_channel": "HQ Operations",
        "job_level": "Senior Specialist",
        "branch": "Taguig HQ",
        "date_hired": "2022-03-15",
        "eoc_date": "2026-08-31",
        "employee_status": "Regular",
        "reason_for_separation": "Resignation",
        "with_clearance_already": "In Progress",
        "current_stage": "IT_CLEARANCE",
        "overall_status": "PENDING_REVIEW",
        "submitted_at": "2026-09-18T08:30:00Z",
        "sample_file": "clearance_missing_it.pdf",
        "sample_type": "CLEARANCE_SHEET",
        "ai_flags_count": 2,
        "flags_summary": ["FLAG_MISSING_FIELD", "FLAG_ACCOUNTABILITY_NOTED"],
    },
    {
        "dossier_id": "DOS-2026-002",
        "employee_name": "Maria Clara Santos",
        "department": "Finance & Accounting",
        "company": "CMG Retail Inc.",
        "unit_channel": "Retail Stores",
        "job_level": "Team Lead",
        "branch": "Makati Central",
        "date_hired": "2020-06-01",
        "eoc_date": "2026-09-15",
        "employee_status": "Regular",
        "reason_for_separation": "End of Contract",
        "with_clearance_already": "Yes",
        "current_stage": "LAST_PAY_CALC",
        "overall_status": "FLAGGED",
        "submitted_at": "2026-09-17T11:20:00Z",
        "sample_file": "quit_claim_mismatch.pdf",
        "sample_type": "QUIT_CLAIM",
        "ai_flags_count": 2,
        "flags_summary": ["FLAG_AMOUNT_MISMATCH", "FLAG_SIGNATURE_ABSENT"],
    },
    {
        "dossier_id": "DOS-2026-003",
        "employee_name": "Pedro Penduko",
        "department": "Logistics & Supply Chain",
        "company": "CMG Distribution Corp.",
        "unit_channel": "Logistics Hub",
        "job_level": "Rank & File",
        "branch": "Cebu Hub",
        "date_hired": "2023-01-10",
        "eoc_date": "2026-09-30",
        "employee_status": "Regular",
        "reason_for_separation": "Resignation",
        "with_clearance_already": "No",
        "current_stage": "FINANCE_DISBURSEMENT",
        "overall_status": "FLAGGED",
        "submitted_at": "2026-09-19T14:45:00Z",
        "sample_file": "bank_bad_format.png",
        "sample_type": "BANK_ENROLLMENT",
        "ai_flags_count": 1,
        "flags_summary": ["FLAG_FORMAT_MISMATCH"],
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
        "overall_status": "PENDING_REVIEW",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "sample_file": data.accountability_form_name or "uploaded_form.pdf",
        "sample_type": "CLEARANCE_SHEET",
        "ai_flags_count": 0,
        "flags_summary": [],
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
            elif req.action == "REJECT":
                d["overall_status"] = "REJECTED"
            else:
                d["overall_status"] = "REVISION_REQUESTED"
            break

    return {"status": "SUCCESS", "audit_entry": entry}


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
  
  <!-- Tailwind CSS CDN with dark mode config -->
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
    ::-webkit-scrollbar-thumb { background: rgba(140, 140, 145, 0.3); border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(140, 140, 145, 0.5); }
    
    /* Lark custom select and input styles with Apple touch */
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
    .dark .lark-label {
      color: #E5E5EA;
    }
    .lark-required {
      color: #F54A45;
      margin-left: 2px;
    }
  </style>
</head>
<body class="bg-apple-canvasLight dark:bg-apple-canvasDark text-neutral-900 dark:text-neutral-100 min-h-screen transition-colors duration-300">
  
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
        <button id="tabBtnForm" onclick="switchView('form')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition">
          <i class="fa-regular fa-pen-to-square mr-1.5 text-lark-blue"></i> Requester Form
        </button>
        <button id="tabBtnApprover" onclick="switchView('approver')" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition">
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
    <button onclick="switchView('form')" class="text-xs font-semibold text-lark-blue py-1">Requester Form</button>
    <button onclick="switchView('approver')" class="text-xs font-medium text-neutral-500 py-1">Approver Desk</button>
    <button onclick="switchView('harness')" class="text-xs font-medium text-neutral-500 py-1">Dev Harness</button>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8">

    <!-- ================================================================= -->
    <!-- VIEW 1: REQUESTER FORM (LARK APPROVAL RECREATION) -->
    <!-- ================================================================= -->
    <section id="viewForm" class="max-w-3xl mx-auto space-y-6">
      
      <!-- Main Lark Form Container Card -->
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-8 sm:p-10 shadow-[0_4px_20px_rgba(0,0,0,0.04)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.25)] border border-black/[0.06] dark:border-white/[0.08] transition">
        
        <!-- Header -->
        <div class="mb-6">
          <h2 class="text-xl font-bold tracking-tight text-neutral-900 dark:text-white">Application Details</h2>
        </div>

        <!-- CMG Group SOA Records Banner (Exact from user screenshot) -->
        <div class="mb-6 p-3 rounded-lg bg-neutral-100/80 dark:bg-neutral-800/60 border border-neutral-200/70 dark:border-neutral-700/60 flex items-center space-x-2 text-xs text-neutral-700 dark:text-neutral-300">
          <i class="fa-solid fa-table-list text-lark-blue text-sm"></i>
          <span class="font-medium text-lark-blue hover:underline cursor-pointer">CMG Group SOA Records</span>
        </div>

        <!-- Form Elements -->
        <form id="larkClearanceForm" class="space-y-5" onsubmit="handleLarkSubmit(event)">
          
          <!-- Row 1: Department -->
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

          <!-- Row 2: Employee Name -->
          <div>
            <label class="lark-label">Employee Name<span class="lark-required">*</span></label>
            <select id="formEmployeeName" required class="lark-input" onchange="autoFillEmployee(this.value)">
              <option value="" disabled selected>Select</option>
              <option value="Juan Dela Cruz">Juan Dela Cruz (EMP-94812)</option>
              <option value="Maria Santos">Maria Santos (EMP-10294)</option>
              <option value="Pedro Penduko">Pedro Penduko (EMP-88419)</option>
              <option value="Custom">Other / Enter Manual...</option>
            </select>
          </div>

          <!-- Row 3: Date Hired -->
          <div>
            <label class="lark-label">Date Hired<span class="lark-required">*</span></label>
            <input type="date" id="formDateHired" required value="2026-09-21" class="lark-input" />
          </div>

          <!-- Row 4: Job Level -->
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

          <!-- Row 5: Company -->
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

          <!-- Row 6: Unit / Channel -->
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

          <!-- Row 7: Branch -->
          <div>
            <label class="lark-label">Branch<span class="lark-required">*</span></label>
            <div class="flex items-center space-x-2">
              <select id="formBranch" required class="lark-input flex-1">
                <option value="Taguig HQ - 24th Floor" selected>Taguig HQ - 24th Floor</option>
                <option value="Makati Central Hub">Makati Central Hub</option>
                <option value="Cebu Distribution Center">Cebu Distribution Center</option>
                <option value="Davao Regional Hub">Davao Regional Hub</option>
              </select>
              <button type="button" onclick="alert('Add Branch modal simulated')" class="px-3.5 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-sm font-semibold transition" title="Add Branch">
                <i class="fa-solid fa-plus"></i>
              </button>
            </div>
          </div>

          <!-- Row 8: Employee Status -->
          <div>
            <label class="lark-label">Employee Status<span class="lark-required">*</span></label>
            <select id="formEmployeeStatus" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Regular" selected>Regular</option>
              <option value="Probationary">Probationary</option>
              <option value="Project-Based">Project-Based</option>
              <option value="Fixed-Term Contract">Fixed-Term Contract</option>
            </select>
          </div>

          <!-- Row 9: EOC/Separation Date -->
          <div>
            <label class="lark-label">EOC/Separation Date<span class="lark-required">*</span></label>
            <input type="date" id="formEocDate" required value="2026-09-21" class="lark-input" />
          </div>

          <!-- Row 10: With Clearance Already? -->
          <div>
            <label class="lark-label">With Clearance Already?<span class="lark-required">*</span></label>
            <select id="formWithClearance" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Yes">Yes</option>
              <option value="No" selected>No</option>
              <option value="In Progress">In Progress</option>
            </select>
          </div>

          <!-- Row 11: Reason for Separation -->
          <div>
            <label class="lark-label">Reason for Separation<span class="lark-required">*</span></label>
            <select id="formReasonSeparation" required class="lark-input">
              <option value="" disabled selected>Select</option>
              <option value="Resignation" selected>Resignation</option>
              <option value="End of Contract">End of Contract</option>
              <option value="Retirement">Retirement</option>
              <option value="Redundancy / Restructuring">Redundancy / Restructuring</option>
              <option value="Mutual Separation">Mutual Separation</option>
            </select>
          </div>

          <!-- Instruction Banner (Exact from user screenshot) -->
          <div class="p-3.5 rounded-lg bg-neutral-100/90 dark:bg-neutral-800/70 border border-neutral-200/80 dark:border-neutral-700 text-xs text-neutral-600 dark:text-neutral-300 flex items-start space-x-2">
            <i class="fa-solid fa-circle-info text-neutral-400 mt-0.5"></i>
            <span>If there are missing documents, please attach a notarized affidavit of loss.</span>
          </div>

          <!-- Attachment 1: Accountability Form -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="lark-label mb-0">Accountability Form</label>
              <span id="aiTag1" class="hidden text-[10px] font-medium px-2 py-0.5 rounded-full bg-blue-500/10 text-lark-blue">
                <i class="fa-solid fa-wand-magic-sparkles mr-1"></i>Pre-Checked
              </span>
            </div>
            <div class="flex items-center space-x-3">
              <button type="button" onclick="document.getElementById('attachAccountability').click()" class="px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-xs font-semibold text-neutral-700 dark:text-neutral-200 shadow-sm transition flex items-center">
                <i class="fa-solid fa-arrow-up-from-bracket mr-2 text-neutral-400"></i> Upload attachment
              </button>
              <input type="file" id="attachAccountability" class="hidden" onchange="handleFormAttachment(this, 'accountabilityFileName', 'CLEARANCE_SHEET', 'aiTag1')" />
              <span id="accountabilityFileName" class="text-xs text-neutral-500">clearance_sheet_valid.pdf (Pre-loaded sample)</span>
            </div>
            <p class="text-[11px] text-neutral-400">Up to 9 attachments (50 MB each max)</p>
          </div>

          <!-- Attachment 2: Valid Government ID -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="lark-label mb-0">Valid Government ID<span class="lark-required">*</span></label>
              <span id="aiTag2" class="hidden text-[10px] font-medium px-2 py-0.5 rounded-full bg-blue-500/10 text-lark-blue">
                <i class="fa-solid fa-wand-magic-sparkles mr-1"></i>Pre-Checked
              </span>
            </div>
            <div class="flex items-center space-x-3">
              <button type="button" onclick="document.getElementById('attachId').click()" class="px-4 py-2 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-xs font-semibold text-neutral-700 dark:text-neutral-200 shadow-sm transition flex items-center">
                <i class="fa-solid fa-arrow-up-from-bracket mr-2 text-neutral-400"></i> Upload attachment
              </button>
              <input type="file" id="attachId" class="hidden" onchange="handleFormAttachment(this, 'idFileName', 'BANK_ENROLLMENT', 'aiTag2')" />
              <span id="idFileName" class="text-xs text-neutral-500">bank_gcash_valid.png (Pre-loaded proof)</span>
            </div>
            <p class="text-[11px] text-neutral-400">Up to 9 attachments (50 MB each max)</p>
          </div>

          <!-- Collapsible Approval Process Tree -->
          <div class="border border-neutral-200 dark:border-neutral-700 rounded-xl overflow-hidden bg-neutral-50/50 dark:bg-neutral-800/30">
            <div onclick="toggleApprovalTree()" class="p-3.5 bg-neutral-100/60 dark:bg-neutral-800/50 flex items-center justify-between cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 transition">
              <span class="text-xs font-bold text-neutral-800 dark:text-neutral-200 flex items-center">
                Approval Process
              </span>
              <span id="treeIcon" class="text-xs text-neutral-400"><i class="fa-solid fa-chevron-up"></i></span>
            </div>
            <div id="approvalTreeContent" class="p-4 space-y-3 text-xs">
              <!-- Visual Node Stages -->
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold">1</div>
                <div>
                  <div class="font-semibold text-neutral-800 dark:text-neutral-200">Department Clearances (Parallel Nodes)</div>
                  <div class="text-[11px] text-neutral-500">IT Asset Surrender · Admin Facilities · Immediate Supervisor</div>
                </div>
              </div>
              <div class="w-0.5 h-3 bg-neutral-300 dark:bg-neutral-700 ml-3"></div>
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-[10px] font-bold">2</div>
                <div>
                  <div class="font-semibold text-neutral-800 dark:text-neutral-200">Last Pay Computation (Finance & Payroll)</div>
                  <div class="text-[11px] text-neutral-500">Tax computation, leave monetization, quit claim figure audit</div>
                </div>
              </div>
              <div class="w-0.5 h-3 bg-neutral-300 dark:bg-neutral-700 ml-3"></div>
              <div class="flex items-center space-x-3">
                <div class="w-6 h-6 rounded-full bg-neutral-300 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 flex items-center justify-center text-[10px] font-bold">3</div>
                <div>
                  <div class="font-semibold text-neutral-800 dark:text-neutral-200">Final Release & Disbursement</div>
                  <div class="text-[11px] text-neutral-500">Bank / E-Wallet transfer release confirmation</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Actions (Exact button arrangement from screenshot) -->
          <div class="pt-4 flex items-center space-x-3">
            <button type="submit" id="larkSubmitBtn" class="px-6 py-2.5 bg-lark-blue hover:bg-lark-blueHover text-white text-xs font-semibold rounded-lg shadow-sm active:scale-[0.98] transition">
              Submit
            </button>
            <button type="button" onclick="resetLarkForm()" class="px-5 py-2.5 border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 text-xs font-semibold rounded-lg shadow-sm transition">
              Cancel
            </button>
          </div>

        </form>

      </div>

    </section>

    <!-- ================================================================= -->
    <!-- VIEW 2: ROLE-BASED APPROVER DESK (LARK ADMIN / APPROVER VIEW) -->
    <!-- ================================================================= -->
    <section id="viewApprover" class="hidden space-y-6">
      
      <!-- Role Switcher & Sub-Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-apple-surfaceLight dark:bg-apple-surfaceDark p-5 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
        <div>
          <h2 class="text-base font-bold text-neutral-900 dark:text-white flex items-center">
            <i class="fa-solid fa-list-check mr-2 text-lark-blue"></i> Clearance Approver Review Desk
          </h2>
          <p class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">Review submitted clearance dossiers and verify AI pre-check flags</p>
        </div>

        <!-- Approver Role Selector -->
        <div class="flex items-center space-x-2">
          <span class="text-xs text-neutral-400 font-medium">Logged Role:</span>
          <select id="approverRoleSelect" onchange="switchApproverRole(this.value)" class="text-xs font-semibold appearance-none bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg px-3 py-1.5 text-neutral-800 dark:text-neutral-200 focus:ring-2 focus:ring-lark-blue focus:outline-none cursor-pointer">
            <option value="IT_APPROVER">IT Department Approver</option>
            <option value="FINANCE_APPROVER">Finance & Payroll Approver</option>
            <option value="HR_APPROVER">HR Exit Approver</option>
            <option value="ADMIN_APPROVER">Facilities & Admin</option>
          </select>
        </div>
      </div>

      <!-- Approver Two-Column Review Deck -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Deck: Pending Submissions Queue -->
        <div class="lg:col-span-5 space-y-4">
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-5 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
                Pending Clearance Queue
              </h3>
              <span id="queueBadge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400">
                3 submissions
              </span>
            </div>
            
            <div id="dossiersQueue" class="space-y-2.5">
              <!-- Queue items populated by JS -->
            </div>
          </div>
        </div>

        <!-- Right Deck: Active Clearance Review Details & AI Flags -->
        <div class="lg:col-span-7 space-y-4">
          
          <div id="approverEmptyCard" class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-12 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] text-center text-neutral-400 min-h-[460px] flex flex-col justify-center">
            <i class="fa-regular fa-folder-open text-4xl mb-3 text-neutral-300 dark:text-neutral-600"></i>
            <h4 class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Select a Dossier to Inspect</h4>
            <p class="text-xs text-neutral-400 max-w-xs mx-auto mt-1">Click any pending employee in the queue to load the Lark application details, document preview, and AI pre-check flags.</p>
          </div>

          <div id="approverActiveCard" class="hidden bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm space-y-5">
            
            <!-- Employee Header -->
            <div class="flex items-start justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
              <div>
                <div class="flex items-center space-x-2">
                  <span id="apprDossierId" class="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-500/10 text-lark-blue">DOS-2026-001</span>
                  <h3 id="apprEmpName" class="text-base font-bold text-neutral-900 dark:text-white">Juan Dela Cruz</h3>
                </div>
                <p id="apprDeptRole" class="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">Information Technology · Senior Specialist</p>
              </div>
              <div class="text-right">
                <span id="apprStatusBadge" class="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-amber-500/10 text-apple-amber border border-amber-500/20">
                  Pending Sign-Off
                </span>
              </div>
            </div>

            <!-- Application Metadata Grid -->
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3.5 rounded-xl bg-neutral-50 dark:bg-neutral-800/40 text-xs border border-black/[0.04] dark:border-white/[0.06]">
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">Company</span>
                <span id="apprCompany" class="font-medium text-neutral-800 dark:text-neutral-200">CMG Group</span>
              </div>
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">Unit / Channel</span>
                <span id="apprUnit" class="font-medium text-neutral-800 dark:text-neutral-200">HQ Operations</span>
              </div>
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">Branch</span>
                <span id="apprBranch" class="font-medium text-neutral-800 dark:text-neutral-200">Taguig HQ</span>
              </div>
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">Hired Date</span>
                <span id="apprDateHired" class="font-medium text-neutral-800 dark:text-neutral-200">2022-03-15</span>
              </div>
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">EOC / Separation</span>
                <span id="apprEocDate" class="font-medium text-neutral-800 dark:text-neutral-200">2026-08-31</span>
              </div>
              <div>
                <span class="text-[10px] text-neutral-400 uppercase font-semibold block">Separation Reason</span>
                <span id="apprReason" class="font-medium text-neutral-800 dark:text-neutral-200">Resignation</span>
              </div>
            </div>

            <!-- AI Pre-Check Flags for this dossier -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500 flex items-center">
                  <i class="fa-solid fa-shield-halved mr-1.5 text-apple-blue"></i> AI Document Pre-Check Analysis
                </h4>
                <span id="apprFlagsCount" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-500/10 text-apple-red font-semibold">2 Flags</span>
              </div>
              <div id="apprFlagsList" class="space-y-2">
                <!-- Injected flags -->
              </div>
            </div>

            <!-- Attached Document Preview -->
            <div class="border border-black/[0.06] dark:border-white/[0.08] rounded-xl overflow-hidden bg-neutral-50 dark:bg-neutral-900/50">
              <div class="px-4 py-2 bg-neutral-100 dark:bg-neutral-800/60 flex items-center justify-between text-xs">
                <span class="font-semibold text-neutral-700 dark:text-neutral-300">
                  <i class="fa-regular fa-file-pdf mr-1.5 text-lark-blue"></i> Attached Document Preview: <span id="apprDocName" class="font-mono text-[11px]">doc.pdf</span>
                </span>
                <a id="apprDocLink" href="#" target="_blank" class="text-lark-blue hover:underline text-[11px]">Open Full <i class="fa-solid fa-arrow-up-right-from-square ml-1 text-[9px]"></i></a>
              </div>
              <div id="apprDocPreview" class="p-3 min-h-[220px] flex items-center justify-center">
                <!-- Injected iframe or image -->
              </div>
            </div>

            <!-- Human Approver Action Box -->
            <div class="p-4 rounded-xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 border border-lark-blue/20 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-neutral-800 dark:text-neutral-200 flex items-center">
                  <i class="fa-solid fa-user-pen mr-1.5 text-lark-blue"></i> Approver Decision
                </span>
                <span class="text-[10px] text-neutral-400 font-mono">Role: <span id="currentRoleLabel" class="font-semibold text-neutral-700 dark:text-neutral-300">IT_APPROVER</span></span>
              </div>

              <!-- Required override box if flags exist -->
              <div id="apprOverrideBox" class="hidden">
                <label class="block text-[11px] font-medium text-apple-red mb-1">
                  Override Justification <span class="text-apple-red">*</span>
                </label>
                <textarea id="apprOverrideNotes" rows="2" placeholder="Explain why approving despite active blocker flags (e.g., equipment returned physically without system update, waiver acknowledged)..." class="w-full text-xs bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-lg p-2 focus:ring-2 focus:ring-lark-blue focus:outline-none"></textarea>
              </div>

              <div class="flex items-center justify-end space-x-2 pt-1">
                <button onclick="submitApproverDeskDecision('APPROVE')" class="px-4 py-2 bg-apple-green hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-check mr-1.5"></i> Approve Clearance
                </button>
                <button onclick="submitApproverDeskDecision('REQUEST_REVISION')" class="px-3.5 py-2 bg-apple-amber hover:bg-amber-600 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-rotate-left mr-1.5"></i> Request Revision
                </button>
                <button onclick="submitApproverDeskDecision('REJECT')" class="px-3.5 py-2 bg-apple-red hover:bg-red-600 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-ban mr-1.5"></i> Reject
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>

    </section>

    <!-- ================================================================= -->
    <!-- VIEW 3: DEVELOPER HARNESS (ORIGINAL LOCAL TEST RUNNER) -->
    <!-- ================================================================= -->
    <section id="viewHarness" class="hidden space-y-6">
      
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Left Column: Synthetic Fixtures & Direct Pre-check -->
        <div class="lg:col-span-4 space-y-6">
          
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
            <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-3 flex items-center">
              <i class="fa-solid fa-flask mr-2 text-apple-amber"></i> Quick Test Fixtures
            </h3>
            <p class="text-xs text-neutral-500 mb-3">1-click automated extraction & flagging test:</p>
            <div id="harnessSamplesList" class="space-y-2">
              <!-- Populated by JS -->
            </div>
          </div>

          <!-- Audit Trail Quick Card -->
          <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-xs font-bold uppercase tracking-wider text-neutral-400">
                Recent Audit Trail
              </h3>
              <button onclick="loadAuditLogs()" class="text-xs text-lark-blue hover:underline"><i class="fa-solid fa-rotate-right"></i></button>
            </div>
            <div id="harnessAuditContainer" class="max-h-72 overflow-y-auto space-y-2 text-xs">
              <!-- Populated by JS -->
            </div>
          </div>

        </div>

        <!-- Right Column: Raw JSON & Extracted Inspection -->
        <div class="lg:col-span-8 space-y-6">
          <div id="harnessResultCard" class="bg-apple-surfaceLight dark:bg-apple-surfaceDark p-6 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm min-h-[500px]">
            <div id="harnessEmptyState" class="text-center py-20 text-neutral-400">
              <i class="fa-solid fa-terminal text-4xl mb-3 text-neutral-300 dark:text-neutral-600"></i>
              <h4 class="text-sm font-semibold text-neutral-700 dark:text-neutral-300">Developer Diagnostic Output</h4>
              <p class="text-xs text-neutral-400 max-w-sm mx-auto mt-1">Select any fixture on the left to run raw Pydantic schema validation and view rule execution logs.</p>
            </div>

            <div id="harnessResultContent" class="hidden space-y-5">
              <div class="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
                <div>
                  <span id="harnessDocType" class="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-500/10 text-lark-blue">TYPE</span>
                  <h3 id="harnessFileName" class="text-sm font-bold text-neutral-900 dark:text-white mt-1">file.pdf</h3>
                </div>
                <div class="text-right">
                  <span class="text-[10px] text-neutral-400 block">Overall Confidence</span>
                  <span id="harnessConfidence" class="text-xl font-bold text-apple-green">95%</span>
                </div>
              </div>

              <!-- Flags list -->
              <div>
                <h5 class="text-xs font-bold uppercase text-neutral-400 mb-2">Detected Flags</h5>
                <div id="harnessFlagsBox" class="space-y-2"></div>
              </div>

              <!-- Raw JSON Viewer -->
              <div>
                <h5 class="text-xs font-bold uppercase text-neutral-400 mb-2">Pydantic Extracted JSON</h5>
                <pre id="harnessJsonPre" class="p-4 rounded-xl bg-neutral-900 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-72"></pre>
              </div>
            </div>
          </div>
        </div>

      </div>

    </section>

  </main>

  <script>
    let activeDossier = null;

    // View Switcher
    function switchView(viewName) {
      document.getElementById('viewForm').classList.add('hidden');
      document.getElementById('viewApprover').classList.add('hidden');
      document.getElementById('viewHarness').classList.add('hidden');

      const btnForm = document.getElementById('tabBtnForm');
      const btnAppr = document.getElementById('tabBtnApprover');
      const btnHarn = document.getElementById('tabBtnHarness');

      btnForm.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition";
      btnAppr.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition";
      btnHarn.className = "px-3.5 py-1.5 rounded-lg text-xs font-semibold text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition";

      const activeClass = "px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-apple-elevatedDark text-neutral-900 dark:text-white shadow-sm transition";

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

    // Auto fill for demo
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
      }
    }

    function toggleApprovalTree() {
      const content = document.getElementById('approvalTreeContent');
      const icon = document.getElementById('treeIcon');
      if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        icon.innerHTML = '<i class="fa-solid fa-chevron-up"></i>';
      } else {
        content.classList.add('hidden');
        icon.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
      }
    }

    // Attachment Handler on Form
    async function handleFormAttachment(input, labelId, docType, tagId) {
      if (!input.files.length) return;
      const file = input.files[0];
      document.getElementById(labelId).textContent = `${file.name} (${Math.round(file.size/1024)} KB)`;

      // Run background pre-check
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', docType);

      try {
        const res = await fetch('/api/precheck', { method: 'POST', body: formData });
        const data = await res.json();
        const tag = document.getElementById(tagId);
        tag.classList.remove('hidden');
        if (data.flags && data.flags.length > 0) {
          tag.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-apple-red border border-red-500/20";
          tag.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-1"></i>${data.flags.length} Flag(s)`;
        } else {
          tag.className = "text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20";
          tag.innerHTML = `<i class="fa-solid fa-check mr-1"></i>Pre-Check Passed`;
        }
      } catch (err) {
        console.error(err);
      }
    }

    // Handle Lark Submit
    async function handleLarkSubmit(e) {
      e.preventDefault();
      const submitBtn = document.getElementById('larkSubmitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-1.5"></i> Submitting to Lark...';

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
        alert(`Application Submitted Successfully!\nInstance ID: ${data.dossier.dossier_id}\nRouting to Approvers in Lark Approval Flow.`);
        switchView('approver');
      } catch (err) {
        alert('Submission failed: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit';
      }
    }

    function resetLarkForm() {
      document.getElementById('larkClearanceForm').reset();
    }

    // Load Approver Queue
    async function loadDossiersQueue() {
      try {
        const res = await fetch('/api/clearance/dossiers');
        const dossiers = await res.json();
        const container = document.getElementById('dossiersQueue');
        document.getElementById('queueBadge').textContent = `${dossiers.length} submissions`;

        container.innerHTML = dossiers.map(d => {
          const hasFlags = d.ai_flags_count > 0;
          const statusClass = d.overall_status === 'APPROVED' ? 'bg-emerald-500/10 text-apple-green' : (hasFlags ? 'bg-red-500/10 text-apple-red' : 'bg-amber-500/10 text-apple-amber');
          return `
            <div onclick="selectDossier('${d.dossier_id}')" class="p-3.5 rounded-xl bg-neutral-50 dark:bg-apple-elevatedDark hover:bg-blue-50/40 dark:hover:bg-neutral-700/50 border border-black/[0.04] dark:border-white/[0.06] cursor-pointer transition flex items-center justify-between group">
              <div>
                <div class="flex items-center space-x-2">
                  <span class="text-[10px] font-mono font-bold text-neutral-400">${d.dossier_id}</span>
                  <span class="text-xs font-bold text-neutral-800 dark:text-neutral-200 group-hover:text-lark-blue transition">${d.employee_name}</span>
                </div>
                <div class="text-[11px] text-neutral-500 dark:text-neutral-400 mt-0.5">${d.department} · ${d.reason_for_separation}</div>
              </div>
              <div class="text-right">
                <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusClass}">
                  ${d.overall_status}
                </span>
                <span class="text-[10px] text-neutral-400 block mt-0.5">${d.ai_flags_count} AI flags</span>
              </div>
            </div>
          `;
        }).join('');

        if (dossiers.length && !activeDossier) {
          selectDossier(dossiers[0].dossier_id);
        }
      } catch (err) {
        console.error(err);
      }
    }

    async function selectDossier(dossierId) {
      try {
        const res = await fetch('/api/clearance/dossiers');
        const dossiers = await res.json();
        const d = dossiers.find(item => item.dossier_id === dossierId);
        if (!d) return;

        activeDossier = d;
        document.getElementById('approverEmptyCard').classList.add('hidden');
        document.getElementById('approverActiveCard').classList.remove('hidden');

        document.getElementById('apprDossierId').textContent = d.dossier_id;
        document.getElementById('apprEmpName').textContent = d.employee_name;
        document.getElementById('apprDeptRole').textContent = `${d.department} · ${d.job_level}`;
        document.getElementById('apprCompany').textContent = d.company;
        document.getElementById('apprUnit').textContent = d.unit_channel;
        document.getElementById('apprBranch').textContent = d.branch;
        document.getElementById('apprDateHired').textContent = d.date_hired;
        document.getElementById('apprEocDate').textContent = d.eoc_date;
        document.getElementById('apprReason').textContent = d.reason_for_separation;

        const statusBadge = document.getElementById('apprStatusBadge');
        statusBadge.textContent = d.overall_status.replace('_', ' ');

        document.getElementById('apprDocName').textContent = d.sample_file;
        document.getElementById('apprDocLink').href = `/samples/${d.sample_file}`;

        // Preview rendering
        const preview = document.getElementById('apprDocPreview');
        if (d.sample_file.endsWith('.pdf')) {
          preview.innerHTML = `<iframe src="/samples/${d.sample_file}" class="w-full h-80 rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white" frameborder="0"></iframe>`;
        } else {
          preview.innerHTML = `<img src="/samples/${d.sample_file}" class="max-h-72 rounded-lg object-contain border border-neutral-200 dark:border-neutral-700 bg-white" />`;
        }

        // Run pre-check on that sample to load exact flags
        const fileRes = await fetch(`/samples/${d.sample_file}`);
        const blob = await fileRes.blob();
        const formData = new FormData();
        formData.append('file', blob, d.sample_file);
        formData.append('document_type', d.sample_type);

        const checkRes = await fetch('/api/precheck', { method: 'POST', body: formData });
        const checkData = await checkRes.json();

        const flagsList = document.getElementById('apprFlagsList');
        const flagsCount = document.getElementById('apprFlagsCount');
        const overrideBox = document.getElementById('apprOverrideBox');

        if (!checkData.flags || checkData.flags.length === 0) {
          flagsCount.textContent = "0 Flags (Clean)";
          flagsCount.className = "text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-apple-green font-semibold";
          flagsList.innerHTML = `
            <div class="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs flex items-center space-x-2">
              <i class="fa-solid fa-check-circle text-apple-green"></i>
              <span>All automated pre-checks passed cleanly. Zero accountabilities or format discrepancies detected.</span>
            </div>
          `;
          overrideBox.classList.add('hidden');
        } else {
          flagsCount.textContent = `${checkData.flags.length} Flags Detected`;
          flagsCount.className = "text-[10px] font-mono px-2 py-0.5 rounded-full bg-red-500/10 text-apple-red font-semibold";
          overrideBox.classList.remove('hidden');

          flagsList.innerHTML = checkData.flags.map(f => `
            <div class="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-neutral-800 dark:text-neutral-200 flex items-start space-x-2.5">
              <i class="fa-solid fa-triangle-exclamation text-apple-red mt-0.5"></i>
              <div class="flex-1">
                <div class="font-bold flex items-center justify-between">
                  <span>${f.code}</span>
                  <span class="text-[9px] uppercase px-1.5 py-0.5 rounded bg-apple-red text-white font-mono">${f.severity}</span>
                </div>
                <div class="mt-0.5 text-neutral-600 dark:text-neutral-300">${f.message}</div>
              </div>
            </div>
          `).join('');
        }
      } catch (err) {
        console.error(err);
      }
    }

    function switchApproverRole(role) {
      document.getElementById('currentRoleLabel').textContent = role;
    }

    async function submitApproverDeskDecision(action) {
      if (!activeDossier) return;
      const role = document.getElementById('approverRoleSelect').value;
      const overrideNotes = document.getElementById('apprOverrideNotes').value.trim();

      if (action === 'APPROVE' && activeDossier.ai_flags_count > 0 && !overrideNotes) {
        alert('Approver Override Required: This clearance dossier has active blocker flags. Please provide an override explanation before finalizing approval.');
        document.getElementById('apprOverrideNotes').focus();
        return;
      }

      try {
        const res = await fetch('/api/approvals/action', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            document_id: activeDossier.dossier_id,
            approver_id: "USR-CURRENT-APPROVER",
            role: role,
            action: action,
            flags_reviewed: activeDossier.flags_summary || [],
            override_justification: overrideNotes,
          })
        });
        await res.json();
        alert(`Dossier ${activeDossier.dossier_id} updated: ${action}!\nLogged permanently to audit trail.`);
        document.getElementById('apprOverrideNotes').value = '';
        loadDossiersQueue();
      } catch (err) {
        alert('Action failed: ' + err.message);
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
          <div class="p-2 rounded bg-red-500/10 text-apple-red text-xs">
            <b>${f.code}</b> [${f.severity}]: ${f.message}
          </div>
        `).join('');
      }
      loadAuditLogs();
    }

    // Audit logs
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

    // Theme Switcher
    function initTheme() {
      const savedTheme = localStorage.getItem('theme');
      // DEFAULT TO LIGHT MODE per user request!
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
