"""Local test harness for Clearance & Last Pay document pre-check pipeline.
Supports both CLI batch processing and an interactive local browser dashboard
designed with an Apple minimalist aesthetic and full Light/Dark mode support.
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
    description="Apple-minimalist local test runner and visualizer for AI document extraction pre-checks.",
    version="1.1.0",
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
    """Interactive Apple-minimalist dashboard for document extraction testing."""
    return HTML_DASHBOARD


HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en" class="light">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Clearance & Last Pay — AI Document Pre-Check</title>
  
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
            mono: [
              '"SF Mono"',
              'Menlo',
              'Monaco',
              'Consolas',
              'monospace'
            ],
          },
          colors: {
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
  
  <!-- SF Pro / FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  
  <style>
    /* Apple smooth scroll and subpixel antialiasing */
    html {
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    
    /* Subtle custom scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(140, 140, 145, 0.3);
      border-radius: 9999px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(140, 140, 145, 0.5);
    }
  </style>
</head>
<body class="bg-apple-canvasLight dark:bg-apple-canvasDark text-neutral-900 dark:text-neutral-100 min-h-screen transition-colors duration-300">
  
  <!-- Apple Frosted Glass Header -->
  <header class="sticky top-0 z-50 bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border-b border-black/[0.06] dark:border-white/[0.08] transition-colors duration-300">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
      
      <!-- Brand & Product Title -->
      <div class="flex items-center space-x-3.5">
        <div class="w-8 h-8 rounded-xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-950 flex items-center justify-center shadow-sm">
          <i class="fa-solid fa-file-shield text-sm"></i>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-sm font-semibold tracking-tight">Clearance & Last Pay</h1>
            <span class="text-[11px] px-2 py-0.5 rounded-full font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 border border-black/[0.04] dark:border-white/[0.06]">
              Milestone 1
            </span>
          </div>
          <p class="text-[11px] text-neutral-500 dark:text-neutral-400">AI Document Pre-Check & Human Verification Gate</p>
        </div>
      </div>

      <!-- Right Controls: Guardrail & Theme Switcher -->
      <div class="flex items-center space-x-4">
        <!-- Guardrail Badge -->
        <div class="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
          <i class="fa-solid fa-user-check text-[11px]"></i>
          <span>Human Sign-Off Mandatory</span>
        </div>

        <!-- Light / Dark Mode Segmented Toggle -->
        <button id="themeToggle" onclick="toggleTheme()" class="relative p-2 w-9 h-9 rounded-full bg-neutral-200/70 dark:bg-neutral-800 hover:bg-neutral-300/70 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 transition flex items-center justify-center focus:outline-none" title="Toggle Light / Dark Mode">
          <i id="themeIconSun" class="fa-solid fa-sun text-sm hidden"></i>
          <i id="themeIconMoon" class="fa-solid fa-moon text-sm"></i>
        </button>
      </div>

    </div>
  </header>

  <!-- Main Content Layout -->
  <main class="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
    
    <!-- Left Column (4 cols): Ingestion & Synthetic Samples -->
    <div class="lg:col-span-4 space-y-6">
      
      <!-- Upload Document Card -->
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.2)] border border-black/[0.05] dark:border-white/[0.08] transition">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
            Document Ingestion
          </h2>
          <span class="text-[11px] text-apple-blue font-medium cursor-pointer hover:underline" onclick="document.getElementById('fileInput').click()">Browse</span>
        </div>

        <form id="uploadForm" class="space-y-4">
          <!-- Document Type Selector (Cupertino Segmented Feel) -->
          <div>
            <label class="block text-xs font-medium text-neutral-600 dark:text-neutral-400 mb-1.5">Document Target Type</label>
            <div class="relative">
              <select id="docTypeSelect" class="w-full text-xs font-medium appearance-none bg-neutral-100 dark:bg-apple-elevatedDark border border-transparent dark:border-white/[0.05] rounded-xl px-3.5 py-2.5 text-neutral-800 dark:text-neutral-200 focus:ring-2 focus:ring-apple-blue focus:outline-none transition cursor-pointer">
                <option value="QUIT_CLAIM">Quit Claim Form (PDF)</option>
                <option value="BANK_ENROLLMENT">Bank / E-Wallet Proof (Image/PDF)</option>
                <option value="CLEARANCE_SHEET">Department Clearance Sheet (PDF)</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-neutral-400">
                <i class="fa-solid fa-chevron-down text-[10px]"></i>
              </div>
            </div>
          </div>

          <!-- Minimalist Drag and Drop Area -->
          <div id="dropZone" class="border border-dashed border-neutral-300 dark:border-neutral-700 hover:border-apple-blue dark:hover:border-apple-blue rounded-xl p-6 text-center transition cursor-pointer bg-neutral-50/50 dark:bg-neutral-800/30 hover:bg-blue-50/20 dark:hover:bg-blue-950/10">
            <input type="file" id="fileInput" class="hidden" />
            <div class="w-10 h-10 mx-auto mb-2.5 rounded-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center text-neutral-400 dark:text-neutral-500">
              <i class="fa-solid fa-arrow-up-from-bracket text-sm"></i>
            </div>
            <p id="fileLabel" class="text-xs font-semibold text-neutral-800 dark:text-neutral-200">
              Drop file here, or <span class="text-apple-blue font-medium">browse</span>
            </p>
            <p class="text-[11px] text-neutral-400 dark:text-neutral-500 mt-1">PDF, PNG, JPG up to 25MB</p>
          </div>

          <!-- Execute Button (Apple Solid Pill) -->
          <button type="submit" id="submitBtn" class="w-full py-2.5 px-4 bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 hover:bg-neutral-800 dark:hover:bg-neutral-100 text-xs font-semibold rounded-xl shadow-sm active:scale-[0.99] transition flex items-center justify-center">
            <i class="fa-solid fa-bolt mr-2 text-xs"></i> Run AI Pre-Check
          </button>
        </form>
      </div>

      <!-- Quick Test Synthetic Samples Card -->
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.2)] border border-black/[0.05] dark:border-white/[0.08] transition">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
            Synthetic Test Fixtures
          </h2>
          <span class="text-[10px] px-2 py-0.5 rounded-md font-mono bg-neutral-100 dark:bg-neutral-800 text-neutral-500">6 samples</span>
        </div>
        <p class="text-[11px] text-neutral-500 dark:text-neutral-400 mb-3.5">
          Select any verified or edge-case document to test discrepancy detection:
        </p>
        <div id="samplesList" class="space-y-2">
          <p class="text-xs text-neutral-400">Loading samples...</p>
        </div>
      </div>

      <!-- Immutable Audit Trail Card -->
      <div class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.2)] border border-black/[0.05] dark:border-white/[0.08] transition">
        <div class="flex items-center justify-between mb-3.5">
          <h2 class="text-xs font-bold uppercase tracking-wider text-neutral-400 dark:text-neutral-500">
            Immutable Audit Trail
          </h2>
          <button onclick="loadAuditLogs()" class="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 transition" title="Refresh logs">
            <i class="fa-solid fa-arrow-rotate-right"></i>
          </button>
        </div>
        <div id="auditLogContainer" class="max-h-64 overflow-y-auto space-y-2 text-xs pr-1">
          <p class="text-neutral-400">Loading audit trail...</p>
        </div>
      </div>

    </div>

    <!-- Right Column (8 cols): Document Preview & Pre-Check Results -->
    <div class="lg:col-span-8 space-y-6">
      
      <!-- Main Display Card -->
      <div id="resultCard" class="bg-apple-surfaceLight dark:bg-apple-surfaceDark rounded-2xl p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.2)] border border-black/[0.05] dark:border-white/[0.08] min-h-[560px] flex flex-col justify-between transition">
        
        <!-- Empty State -->
        <div id="emptyState" class="my-auto py-20 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-neutral-100 dark:bg-neutral-800/80 flex items-center justify-center text-neutral-400 dark:text-neutral-500">
            <i class="fa-regular fa-folder-open text-2xl"></i>
          </div>
          <h3 class="text-sm font-semibold text-neutral-800 dark:text-neutral-200">No Document Analyzed Yet</h3>
          <p class="text-xs text-neutral-400 dark:text-neutral-500 max-w-sm mx-auto mt-1.5 leading-relaxed">
            Select a synthetic test sample on the left, or upload a document to trigger the AI extraction and rule verification engine.
          </p>
        </div>

        <!-- Result Content (Visible upon inspection) -->
        <div id="resultContent" class="hidden space-y-6">
          
          <!-- Summary Header -->
          <div class="flex flex-wrap items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-5 gap-4">
            <div>
              <div class="flex items-center space-x-2.5">
                <span id="resDocType" class="text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 border border-black/[0.04] dark:border-white/[0.06]">
                  QUIT_CLAIM
                </span>
                <h3 id="resFileName" class="text-base font-semibold text-neutral-900 dark:text-white">quit_claim_valid.pdf</h3>
              </div>
              <p class="text-[11px] text-neutral-400 dark:text-neutral-500 mt-1 font-mono">
                SHA-256: <span id="resHash" class="text-neutral-600 dark:text-neutral-300">...</span> · 
                <span id="resTime" class="text-neutral-600 dark:text-neutral-300">0ms</span> · 
                Model: <span id="resModel" class="text-neutral-600 dark:text-neutral-300">mock</span>
              </p>
            </div>
            
            <!-- Overall Confidence Metric -->
            <div class="text-right">
              <div class="text-xs text-slate-500 font-medium">Overall AI Confidence</div>
              <div id="resConfidence" class="text-2xl font-black text-blue-600">95%</div>
            </div>
          </div>

          <!-- Document Preview Accordion / Section -->
          <div class="border border-slate-200 rounded-xl overflow-hidden bg-slate-50">
            <div onclick="togglePreview()" class="px-4 py-2.5 bg-slate-100/70 border-b border-slate-200 flex items-center justify-between cursor-pointer hover:bg-slate-100">
              <span class="text-xs font-bold text-slate-700 flex items-center">
                <i class="fa-solid fa-eye mr-2 text-blue-600"></i> Document Preview
              </span>
              <span id="previewToggleIcon" class="text-xs text-slate-400"><i class="fa-solid fa-chevron-down"></i></span>
            </div>
            <div id="previewContainer" class="p-3 bg-slate-900/5 flex justify-center items-center min-h-[220px]">
              <!-- Injected iframe or image -->
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
              <i class="fa-solid fa-table-list mr-1.5 text-blue-500"></i> Extracted Fields & Verification Status
            </h4>
            <div class="overflow-x-auto border border-slate-200 rounded-lg">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-100 text-slate-600 uppercase font-semibold">
                  <tr>
                    <th class="py-2.5 px-3">Field Name</th>
                    <th class="py-2.5 px-3">Raw Extracted Value</th>
                    <th class="py-2.5 px-3">Normalized Value</th>
                    <th class="py-2.5 px-3 text-center">Confidence</th>
                    <th class="py-2.5 px-3 text-center">Verification Status</th>
                  </tr>
                </thead>
                <tbody id="fieldsTableBody" class="divide-y divide-slate-200">
                  <!-- Field rows injected here -->
                </tbody>
              </table>
            </div>
          </div>

          <!-- Human Approver Action Gate Box -->
          <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 space-y-4">
            <div class="flex items-start justify-between">
              <div>
                <h5 class="text-sm font-bold text-slate-800 flex items-center">
                  <i class="fa-solid fa-user-check mr-2 text-blue-600"></i> Human Approver Decision Gate
                </h5>
                <p class="text-xs text-slate-600 mt-0.5">
                  The AI pre-check does not make final decisions. Approver review is required to advance or reject clearance.
                </p>
              </div>
              <span class="px-2.5 py-1 rounded bg-blue-100 text-blue-800 text-[10px] font-bold uppercase tracking-wider">
                Audited Action
              </span>
            </div>

            <!-- Optional Override Justification Input -->
            <div id="overrideBox" class="hidden">
              <label class="block text-xs font-semibold text-slate-700 mb-1">
                Approver Override Justification <span class="text-red-500">*</span>
              </label>
              <textarea id="overrideNotes" rows="2" placeholder="Explain rationale for approving despite flagged discrepancies (e.g., manual ID card match, rounding adjustment)..." class="w-full text-xs border border-slate-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"></textarea>
            </div>

            <div class="flex items-center justify-between pt-2 border-t border-blue-200/60">
              <div class="text-[11px] text-slate-500">
                Approver: <span class="font-semibold text-slate-700">Maria Santos (HR Admin)</span>
              </div>
              <div class="flex items-center space-x-2">
                <button onclick="submitDecision('APPROVE')" id="approveBtn" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-check mr-1.5"></i> Approve Clearance
                </button>
                <button onclick="submitDecision('REQUEST_REVISION')" class="px-3.5 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-rotate-left mr-1.5"></i> Request Revision
                </button>
                <button onclick="submitDecision('REJECT')" class="px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg shadow-sm transition flex items-center">
                  <i class="fa-solid fa-ban mr-1.5"></i> Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    let currentResult = null;
    let currentFileUrl = null;

    // Drag and Drop Handling
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('border-blue-500', 'bg-blue-50');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-blue-500', 'bg-blue-50');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('border-blue-500', 'bg-blue-50');
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(fileInput.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        handleFileSelect(fileInput.files[0]);
      }
    });

    function handleFileSelect(file) {
      document.getElementById('fileLabel').innerHTML = `Selected: <b>${file.name}</b> (${Math.round(file.size / 1024)} KB)`;
      if (file.name.toLowerCase().includes('quit') || file.name.toLowerCase().includes('qc')) {
        document.getElementById('docTypeSelect').value = 'QUIT_CLAIM';
      } else if (file.name.toLowerCase().includes('bank') || file.name.toLowerCase().includes('gcash')) {
        document.getElementById('docTypeSelect').value = 'BANK_ENROLLMENT';
      } else if (file.name.toLowerCase().includes('clearance')) {
        document.getElementById('docTypeSelect').value = 'CLEARANCE_SHEET';
      }
    }

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
          <button onclick="runSampleTest('${s.file_name}', '${s.document_type}', '${s.url}')" class="w-full text-left p-2.5 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-lg transition text-xs flex items-center justify-between">
            <div>
              <span class="font-semibold text-slate-800 block">${s.file_name}</span>
              <span class="text-[10px] text-slate-500 uppercase">${s.document_type.replace('_', ' ')} · ${Math.round(s.size_bytes / 1024)} KB</span>
            </div>
            <i class="fa-solid fa-play text-blue-500 text-xs"></i>
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
        container.innerHTML = logs.map(l => {
          if (l.log_type === 'HUMAN_DECISION') {
            const isApproved = l.action === 'APPROVE';
            return `
              <div class="p-2 border border-blue-200 rounded-lg bg-blue-50/60 font-mono text-[11px]">
                <div class="flex justify-between font-bold text-slate-800">
                  <span class="text-blue-700"><i class="fa-solid fa-user-check mr-1"></i>${l.action}</span>
                  <span class="text-[10px] text-slate-500">${l.role}</span>
                </div>
                <div class="text-[10px] text-slate-600 mt-0.5 truncate">${l.override_justification || 'Standard approval without override'}</div>
                <div class="text-[9px] text-slate-400 mt-0.5">${l.timestamp.slice(11, 19)} · Dossier: ${l.dossier_id}</div>
              </div>
            `;
          }

          const hasFlags = l.flag_count > 0;
          return `
            <div class="p-2 border border-slate-200 rounded-lg bg-slate-50 font-mono text-[11px]">
              <div class="flex justify-between font-semibold text-slate-700">
                <span class="truncate max-w-[140px]">${l.file_name}</span>
                <span class="${hasFlags ? 'text-red-600 font-bold' : 'text-emerald-600'}">${l.flag_count} flags</span>
              </div>
              <div class="text-[10px] text-slate-400 truncate mt-0.5">${l.timestamp.slice(11, 19)} · ${l.file_hash_sha256.slice(0, 12)}...</div>
            </div>
          `;
        }).join('');
      } catch (err) {
        console.error(err);
      }
    }

    // Quick Test Sample
    async function runSampleTest(fileName, docType, fileUrl) {
      document.getElementById('emptyState').classList.add('hidden');
      document.getElementById('resultContent').classList.add('hidden');
      currentFileUrl = fileUrl;

      try {
        const fileRes = await fetch(fileUrl);
        let blob;
        if (!fileRes.ok) {
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
        renderResult(data, fileUrl);
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

      const file = fileInput.files[0];
      currentFileUrl = URL.createObjectURL(file);

      const formData = new FormData();
      formData.append('file', file);
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
        renderResult(data, currentFileUrl);
        loadAuditLogs();
      } catch (err) {
        alert('Pre-check error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-bolt mr-2"></i> Run AI Pre-Check';
      }
    });

    function togglePreview() {
      const container = document.getElementById('previewContainer');
      const icon = document.getElementById('previewToggleIcon');
      if (container.classList.contains('hidden')) {
        container.classList.remove('hidden');
        icon.innerHTML = '<i class="fa-solid fa-chevron-up"></i>';
      } else {
        container.classList.add('hidden');
        icon.innerHTML = '<i class="fa-solid fa-chevron-down"></i>';
      }
    }

    function renderResult(data, fileUrl) {
      currentResult = data;
      document.getElementById('emptyState').classList.add('hidden');
      const container = document.getElementById('resultContent');
      container.classList.remove('hidden');

      document.getElementById('resDocType').textContent = data.document_type;
      document.getElementById('resFileName').textContent = data.metadata.file_name;
      document.getElementById('resHash').textContent = data.metadata.file_hash_sha256.slice(0, 16) + '...';
      document.getElementById('resTime').textContent = data.metadata.processing_time_ms + 'ms';
      document.getElementById('resModel').textContent = data.metadata.model_id;
      document.getElementById('resConfidence').textContent = Math.round(data.overall_confidence * 100) + '%';

      // Update Document Preview
      const previewBox = document.getElementById('previewContainer');
      previewBox.classList.remove('hidden');
      document.getElementById('previewToggleIcon').innerHTML = '<i class="fa-solid fa-chevron-up"></i>';

      if (fileUrl) {
        if (data.metadata.file_name.toLowerCase().endsWith('.pdf') || data.metadata.mime_type === 'application/pdf') {
          previewBox.innerHTML = `<iframe src="${fileUrl}" class="w-full h-80 rounded border border-slate-300 shadow-inner" frameborder="0"></iframe>`;
        } else {
          previewBox.innerHTML = `<img src="${fileUrl}" alt="Document Preview" class="max-h-80 rounded border border-slate-300 shadow-sm object-contain" />`;
        }
      } else {
        previewBox.innerHTML = '<p class="text-xs text-slate-400">Document preview unavailable</p>';
      }

      // Render Flags
      const flagsBox = document.getElementById('flagsContainer');
      const overrideBox = document.getElementById('overrideBox');

      if (!data.flags || data.flags.length === 0) {
        flagsBox.innerHTML = `
          <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center">
            <i class="fa-solid fa-circle-check mr-2 text-base text-emerald-600"></i>
            <div><b>Clean Pre-Check:</b> No missing fields, amount discrepancies, or format violations detected.</div>
          </div>
        `;
        overrideBox.classList.add('hidden');
      } else {
        overrideBox.classList.remove('hidden');
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
                  <span class="uppercase text-[10px] tracking-wider px-2 py-0.5 rounded bg-white/80 border">${f.severity}</span>
                </div>
                <div class="mt-0.5 text-slate-800">${f.message}</div>
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
        rows.push(`
          <tr>
            <td class="py-2.5 px-3 font-semibold text-slate-800">employee_name</td>
            <td class="py-2.5 px-3">${fields.employee_name.raw_value || '—'}</td>
            <td class="py-2.5 px-3 font-mono">${fields.employee_name.normalized_value || '—'}</td>
            <td class="py-2.5 px-3 text-center">${Math.round(fields.employee_name.confidence * 100)}%</td>
            <td class="py-2.5 px-3 text-center"><span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700 font-bold">VERIFIED</span></td>
          </tr>
        `);
        for (const dept of fields.department_statuses) {
          const isHold = dept.has_outstanding_accountability.normalized_value;
          const isMissingSig = !dept.signature_present.normalized_value;
          let statusBadge = '<span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700 font-bold">CLEARED</span>';
          if (isHold) {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] rounded bg-red-100 text-red-700 font-bold">HOLD</span>';
          } else if (isMissingSig) {
            statusBadge = '<span class="px-2 py-0.5 text-[10px] rounded bg-amber-100 text-amber-700 font-bold">MISSING SIG</span>';
          }

          rows.push(`
            <tr class="${isHold ? 'bg-red-50/40' : ''}">
              <td class="py-2.5 px-3 font-semibold text-slate-800">${dept.department} Dept Clearance</td>
              <td class="py-2.5 px-3">${dept.is_cleared.raw_value || '—'} (${dept.approver_name.raw_value || 'No Sig'})</td>
              <td class="py-2.5 px-3 font-mono text-slate-600">${dept.accountability_notes.normalized_value || 'None'}</td>
              <td class="py-2.5 px-3 text-center">${Math.round(dept.is_cleared.confidence * 100)}%</td>
              <td class="py-2.5 px-3 text-center">${statusBadge}</td>
            </tr>
          `);
        }
      } else {
        for (const [k, v] of Object.entries(fields)) {
          const isFlagged = v.is_flagged;
          const statusBadge = isFlagged 
            ? '<span class="px-2 py-0.5 text-[10px] rounded bg-red-100 text-red-700 font-bold">FLAGGED</span>'
            : '<span class="px-2 py-0.5 text-[10px] rounded bg-emerald-100 text-emerald-700 font-medium">VERIFIED</span>';
          rows.push(`
            <tr class="${isFlagged ? 'bg-amber-50/40' : ''}">
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

    // Submit Human Decision
    async function submitDecision(action) {
      if (!currentResult) return;

      const overrideNotes = document.getElementById('overrideNotes').value.trim();
      const hasBlocker = currentResult.flags && currentResult.flags.some(f => f.severity === 'BLOCKER');

      if (action === 'APPROVE' && hasBlocker && !overrideNotes) {
        alert('Constitutional Requirement: You are approving a document with active BLOCKER flags. Please enter an approver override justification before submitting.');
        document.getElementById('overrideNotes').focus();
        return;
      }

      try {
        const payload = {
          document_id: currentResult.metadata.document_id,
          approver_id: "USR-MARIA-SANTOS",
          role: "HR_APPROVER",
          action: action,
          flags_reviewed: currentResult.flags ? currentResult.flags.map(f => f.code) : [],
          override_justification: overrideNotes,
        };

        const res = await fetch('/api/approvals/action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        alert(`Action recorded: ${action}! Successfully logged to immutable audit trail.`);
        document.getElementById('overrideNotes').value = '';
        loadAuditLogs();
      } catch (err) {
        alert('Failed to log approver action: ' + err.message);
      }
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
