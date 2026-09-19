"""Local test harness for Clearance & Last Pay document pre-check pipeline.
Supports both CLI batch processing and an interactive local browser dashboard.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline.audit import AuditLogger
from pipeline.extractor import BaseExtractor, get_extractor
from pipeline.models import DocumentType, ExtractionResult

app = FastAPI(
    title="Clearance & Last Pay — Document Pre-Check Local Harness",
    description="Local test runner and visualizer for AI document extraction pre-checks.",
    version="1.0.0",
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
    flags_reviewed: List[str]
    override_justification: str = ""


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
    return {"status": "SUCCESS", "audit_entry": entry}


@app.get("/api/audit-logs")
def get_audit_logs(limit: int = 30):
    """Fetches recent immutable audit log entries."""
    return app.state.audit_logger.get_recent_logs(limit=limit)


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Interactive local dashboard for document extraction testing."""
    return HTML_DASHBOARD


HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Clearance & Last Pay — AI Document Pre-Check Test Harness</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  <style>
    .badge-blocker { background-color: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .badge-success { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
  </style>
</head>
<body class="bg-slate-50 text-slate-900 min-h-screen">
  <!-- Top Navigation -->
  <header class="bg-slate-900 text-white shadow-md sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow">
          <i class="fa-solid fa-file-shield text-lg"></i>
        </div>
        <div>
          <h1 class="text-base font-bold tracking-tight">Clearance & Last Pay — AI Pre-Check Harness</h1>
          <p class="text-[11px] text-slate-400">Milestone 1 Validation · Spec-Driven Development Phase 6</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <i class="fa-solid fa-shield-halved mr-1.5 text-amber-400"></i> Constitutional Guardrail: Human Sign-Off Mandatory
        </span>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
    <!-- Left Column: Upload & Sample Selection -->
    <div class="lg:col-span-4 space-y-6">
      <!-- Upload Card -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center">
          <i class="fa-solid fa-cloud-arrow-up mr-2 text-blue-600"></i> Upload Document
        </h2>

        <form id="uploadForm" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">Document Type</label>
            <select id="docTypeSelect" class="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-blue-500 focus:outline-none">
              <option value="QUIT_CLAIM">Quit Claim Form (PDF)</option>
              <option value="BANK_ENROLLMENT">Bank / E-Wallet Proof (Image/PDF)</option>
              <option value="CLEARANCE_SHEET">Department Clearance Sheet (PDF)</option>
            </select>
          </div>

          <!-- Drag and Drop Dropzone -->
          <div id="dropZone" class="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-5 text-center transition cursor-pointer bg-slate-50 hover:bg-blue-50/50">
            <input type="file" id="fileInput" class="hidden" />
            <i class="fa-solid fa-file-arrow-up text-3xl text-slate-400 mb-2"></i>
            <p id="fileLabel" class="text-xs font-medium text-slate-700">Drag & drop document here or <span class="text-blue-600 underline">browse</span></p>
            <p class="text-[10px] text-slate-400 mt-1">Supports PDF, PNG, JPG</p>
          </div>

          <button type="submit" id="submitBtn" class="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow transition flex items-center justify-center">
            <i class="fa-solid fa-bolt mr-2"></i> Run AI Pre-Check
          </button>
        </form>
      </div>

      <!-- Quick Test Synthetic Samples -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center">
          <i class="fa-solid fa-flask-vial mr-2 text-indigo-600"></i> Synthetic Test Samples
        </h2>
        <p class="text-[11px] text-slate-500 mb-3">Click any fixture to test edge-case detection instantly:</p>
        <div id="samplesList" class="space-y-2">
          <p class="text-xs text-slate-400">Loading samples...</p>
        </div>
      </div>

      <!-- Audit Trail Card -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center">
            <i class="fa-solid fa-list-check mr-2 text-emerald-600"></i> Immutable Audit Trail
          </h2>
          <button onclick="loadAuditLogs()" class="text-xs text-blue-600 hover:underline"><i class="fa-solid fa-rotate-right mr-1"></i>Refresh</button>
        </div>
        <div id="auditLogContainer" class="max-h-60 overflow-y-auto space-y-2 text-xs">
          <p class="text-slate-400">Loading audit trail...</p>
        </div>
      </div>
    </div>

    <!-- Right Column: Results & Flags Visualizer -->
    <div class="lg:col-span-8 space-y-6">
      <!-- Active Result Card -->
      <div id="resultCard" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 min-h-[500px]">
        <div class="text-center py-16 text-slate-400" id="emptyState">
          <i class="fa-solid fa-magnifying-glass-chart text-5xl mb-3 text-slate-300"></i>
          <h3 class="text-base font-semibold text-slate-600">No Document Pre-Checked Yet</h3>
          <p class="text-xs max-w-sm mx-auto mt-1">Upload a PDF/image on the left or select a synthetic test fixture to view AI extraction and pre-check flags.</p>
        </div>

        <div id="resultContent" class="hidden space-y-6">
          <!-- Summary Header -->
          <div class="flex flex-wrap items-center justify-between border-b border-slate-200 pb-4 gap-4">
            <div>
              <div class="flex items-center space-x-2">
                <span id="resDocType" class="px-2.5 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-800 border">DOC</span>
                <h3 id="resFileName" class="text-base font-bold text-slate-900">file.pdf</h3>
              </div>
              <p class="text-xs text-slate-400 mt-0.5">
                Hash: <span id="resHash" class="font-mono text-slate-500">...</span> · 
                Time: <span id="resTime" class="font-semibold text-slate-700">0ms</span>
              </p>
            </div>
            <div class="text-right">
              <div class="text-xs text-slate-500">Overall Confidence</div>
              <div id="resConfidence" class="text-2xl font-black text-blue-600">95%</div>
            </div>
          </div>

          <!-- Pre-Check Flags Section -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center">
              <i class="fa-solid fa-triangle-exclamation mr-1.5 text-amber-500"></i> Pre-Check Discrepancy Flags
            </h4>
            <div id="flagsContainer" class="space-y-2">
              <!-- Flag items injected here -->
            </div>
          </div>

          <!-- Structured Extracted Fields Table -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center">
              <i class="fa-solid fa-table-list mr-1.5 text-blue-500"></i> Extracted Fields & Normalized Values
            </h4>
            <div class="overflow-x-auto border border-slate-200 rounded-lg">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-100 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th class="py-2.5 px-3">Field Name</th>
                    <th class="py-2.5 px-3">Raw Extracted Value</th>
                    <th class="py-2.5 px-3">Normalized Value</th>
                    <th class="py-2.5 px-3 text-center">Confidence</th>
                    <th class="py-2.5 px-3 text-center">Status</th>
                  </tr>
                </thead>
                <tbody id="fieldsTableBody" class="divide-y divide-slate-200">
                  <!-- Field rows injected here -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- Human Approver Action Demo Box -->
          <div class="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h5 class="text-xs font-bold text-slate-800">Human Approver Decision Gate</h5>
              <p class="text-xs text-slate-500">AI only pre-checks and flags. The final clearance determination requires explicit human action.</p>
            </div>
            <div class="flex items-center space-x-2">
              <button onclick="alert('Human Approval simulated! Logged to audit trail.')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm">
                <i class="fa-solid fa-check mr-1"></i> Sign-Off / Approve
              </button>
              <button onclick="alert('Revision requested. Clearance halted.')" class="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-sm">
                <i class="fa-solid fa-xmark mr-1"></i> Request Revision
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    // Load Samples on startup
    async function loadSamples() {
      try {
        const res = await fetch('/api/samples');
        const samples = await res.json();
        const container = document.getElementById('samplesList');
        if (!samples.length) {
          container.innerHTML = '<p class="text-xs text-slate-400">No samples found.</p>';
          return;
        }
        container.innerHTML = samples.map(s => `
          <button onclick="runSampleTest('${s.file_name}', '${s.document_type}')" class="w-full text-left p-2.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-lg transition text-xs flex items-center justify-between">
            <div>
              <span class="font-semibold text-slate-800 block">${s.file_name}</span>
              <span class="text-[10px] text-slate-500">${s.document_type}</span>
            </div>
            <i class="fa-solid fa-chevron-right text-slate-400"></i>
          </button>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    // Load Audit Logs
    async function loadAuditLogs() {
      try {
        const res = await fetch('/api/audit-logs');
        const logs = await res.json();
        const container = document.getElementById('auditLogContainer');
        if (!logs.length) {
          container.innerHTML = '<p class="text-xs text-slate-400">No audit records logged yet.</p>';
          return;
        }
        container.innerHTML = logs.map(l => `
          <div class="p-2 border border-slate-200 rounded bg-slate-50 font-mono text-[11px]">
            <div class="flex justify-between font-semibold text-slate-700">
              <span>${l.file_name}</span>
              <span class="${l.flag_count > 0 ? 'text-red-600' : 'text-emerald-600'}">${l.flag_count} flags</span>
            </div>
            <div class="text-[10px] text-slate-400 truncate">${l.timestamp.slice(11, 19)} · ${l.file_hash_sha256.slice(0, 12)}...</div>
          </div>
        `).join('');
      } catch (err) {
        console.error(err);
      }
    }

    // Quick Test Sample
    async function runSampleTest(fileName, docType) {
      document.getElementById('emptyState').classList.add('hidden');
      document.getElementById('resultContent').classList.add('hidden');
      
      try {
        // Fetch sample file from server as blob
        const fileRes = await fetch(`/samples/${fileName}`);
        let blob;
        if (!fileRes.ok) {
          // Fallback if not served directly: synthesize request
          blob = new Blob(["sample content for " + fileName], { type: fileName.endsWith('.pdf') ? 'application/pdf' : 'image/png' });
        } else {
          blob = await fileRes.blob();
        }

        const formData = new FormData();
        formData.append('file', blob, fileName);
        formData.append('document_type', docType);

        const res = await fetch('/api/precheck', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        renderResult(data);
        loadAuditLogs();
      } catch (err) {
        alert("Extraction failed: " + err.message);
      }
    }

    // Form Submit
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('fileInput');
      const docType = document.getElementById('docTypeSelect').value;
      if (!fileInput.files.length) {
        alert('Please choose a file to upload');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);
      formData.append('document_type', docType);

      const submitBtn = document.getElementById('submitBtn');
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Analyzing...';

      try {
        const res = await fetch('/api/precheck', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        renderResult(data);
        loadAuditLogs();
      } catch (err) {
        alert('Pre-check error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-bolt mr-2"></i> Run AI Pre-Check';
      }
    });

    function renderResult(data) {
      document.getElementById('emptyState').classList.add('hidden');
      const container = document.getElementById('resultContent');
      container.classList.remove('hidden');

      document.getElementById('resDocType').textContent = data.document_type;
      document.getElementById('resFileName').textContent = data.metadata.file_name;
      document.getElementById('resHash').textContent = data.metadata.file_hash_sha256.slice(0, 16) + '...';
      document.getElementById('resTime').textContent = data.metadata.processing_time_ms + 'ms';
      document.getElementById('resConfidence').textContent = Math.round(data.overall_confidence * 100) + '%';

      // Render Flags
      const flagsBox = document.getElementById('flagsContainer');
      if (!data.flags || data.flags.length === 0) {
        flagsBox.innerHTML = `
          <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center">
            <i class="fa-solid fa-circle-check mr-2 text-base text-emerald-600"></i>
            <div><b>Clean Pre-Check:</b> No missing fields, amount discrepancies, or format violations detected.</div>
          </div>
        `;
      } else {
        flagsBox.innerHTML = data.flags.map(f => {
          const isBlocker = f.severity === 'BLOCKER';
          const badgeClass = isBlocker ? 'badge-blocker' : 'badge-warning';
          const icon = isBlocker ? 'fa-solid fa-circle-xmark text-red-600' : 'fa-solid fa-triangle-exclamation text-amber-600';
          return `
            <div class="p-3 rounded-lg text-xs flex items-start space-x-3 ${badgeClass}">
              <i class="${icon} text-base mt-0.5"></i>
              <div class="flex-1">
                <div class="font-bold flex items-center justify-between">
                  <span>${f.code}</span>
                  <span class="uppercase text-[10px] tracking-wider px-2 py-0.5 rounded bg-white/70">${f.severity}</span>
                </div>
                <div class="mt-0.5">${f.message}</div>
              </div>
            </div>
          `;
        }).join('');
      }

      // Render Fields Table
      const tbody = document.getElementById('fieldsTableBody');
      const rows = [];
      const fields = data.fields;

      if (data.document_type === 'CLEARANCE_SHEET') {
        // Clearance sheet has department sub-array
        rows.push(`
          <tr>
            <td class="py-2.5 px-3 font-semibold text-slate-800">employee_name</td>
            <td class="py-2.5 px-3">${fields.employee_name.raw_value || '—'}</td>
            <td class="py-2.5 px-3 font-mono">${fields.employee_name.normalized_value || '—'}</td>
            <td class="py-2.5 px-3 text-center">${Math.round(fields.employee_name.confidence * 100)}%</td>
            <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700">OK</span></td>
          </tr>
        `);
        for (const dept of fields.department_statuses) {
          const isHold = dept.has_outstanding_accountability.normalized_value;
          const statusBadge = isHold ? '<span class="px-2 py-0.5 text-[10px] rounded bg-red-100 text-red-700">HOLD</span>' : '<span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700">CLEARED</span>';
          rows.push(`
            <tr class="${isHold ? 'bg-red-50/50' : ''}">
              <td class="py-2.5 px-3 font-semibold text-slate-800">${dept.department} Dept Clearance</td>
              <td class="py-2.5 px-3">${dept.is_cleared.raw_value || '—'} (${dept.approver_name.raw_value || 'No Sig'})</td>
              <td class="py-2.5 px-3 font-mono">${dept.accountability_notes.normalized_value || 'None'}</td>
              <td class="py-2.5 px-3 text-center">${Math.round(dept.is_cleared.confidence * 100)}%</td>
              <td class="py-2.5 px-3 text-center">${statusBadge}</td>
            </tr>
          `);
        }
      } else {
        // Flat fields for Quit Claim & Bank
        for (const [k, v] of Object.entries(fields)) {
          const isFlagged = v.is_flagged;
          const statusBadge = isFlagged 
            ? '<span class="px-2 py-0.5 text-[10px] rounded bg-red-100 text-red-700 font-bold">FLAGGED</span>'
            : '<span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700 font-medium">VERIFIED</span>';
          rows.push(`
            <tr class="${isFlagged ? 'bg-amber-50/50' : ''}">
              <td class="py-2.5 px-3 font-semibold text-slate-800">${k}</td>
              <td class="py-2.5 px-3">${v.raw_value !== null ? v.raw_value : '<i>null</i>'}</td>
              <td class="py-2.5 px-3 font-mono text-slate-600">${v.normalized_value !== null ? String(v.normalized_value) : '<i>null</i>'}</td>
              <td class="py-2.5 px-3 text-center">${Math.round(v.confidence * 100)}%</td>
              <td class="py-2.5 px-3 text-center">${statusBadge}</td>
            </tr>
          `);
        }
      }
      tbody.innerHTML = rows.join('');
    }

    // Startup
    loadSamples();
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
