"""Safe updater script for pipeline/local_harness.py."""
import re
from pathlib import Path

path = Path("pipeline/local_harness.py")
content = path.read_text(encoding="utf-8")

# 1. Update app.state.dossiers block
marker_dossier_start = "# In-memory dossier store for demonstration"
marker_dossier_end = "def run_cli_extraction("

idx1 = content.find(marker_dossier_start)
idx2 = content.find(marker_dossier_end)
assert idx1 != -1 and idx2 != -1, f"Markers not found: {idx1}, {idx2}"

dossier_replacement = """from pipeline.dossiers import get_initial_dossiers

# In-memory dossier store containing 15 seeded tester accounts
# (5 Pending, 5 For Review, 5 Ready for Release)
app.state.dossiers = get_initial_dossiers()


"""

content = content[:idx1] + dossier_replacement + content[idx2:]

# 2. Update get_approval_metrics
old_metrics = '''@app.get("/api/approvals/metrics")
def get_approval_metrics():
    """Returns live KPI metric numbers for the Executive Clearance Dashboard."""
    total = len(app.state.dossiers)
    pending = sum(1 for d in app.state.dossiers if d.get("overall_status") not in ("APPROVED", "CLEARED"))
    flagged = sum(1 for d in app.state.dossiers if d.get("ai_flags_count", 0) > 0)
    ready = sum(1 for d in app.state.dossiers if d.get("overall_status") in ("APPROVED", "CLEARED") or d.get("ai_flags_count", 0) == 0)
    return {
        "total_requests": total,
        "pending": pending,
        "action_needed": flagged,
        "ready_for_release": ready,
        "avg_sla_days": 4.2,
    }'''

new_metrics = '''@app.get("/api/approvals/metrics")
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
    }'''

assert old_metrics in content, "old_metrics not found in content"
content = content.replace(old_metrics, new_metrics)

# 3. Update sign_department_node to advance linear turn sequence
old_sign = '''    if req.node_key == "HR" and req.action == "CLEARED":
        target["overall_status"] = "APPROVED"
        target["stage_step"] = 4'''

new_sign = '''    # Advance linear turn sequence if matching active node
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
        })'''

assert old_sign in content, "old_sign not found in content"
content = content.replace(old_sign, new_sign)

# 4. Replace embedded HTML_DASHBOARD block with reading templates/dashboard.html
marker_html_start = '@app.get("/", response_class=HTMLResponse)'
marker_html_end = "def main():"

idx_h1 = content.find(marker_html_start)
idx_h2 = content.find(marker_html_end)
assert idx_h1 != -1 and idx_h2 != -1, f"HTML markers not found: {idx_h1}, {idx_h2}"

new_html_block = '''template_path = Path(__file__).resolve().parent / "templates" / "dashboard.html"
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


'''

content = content[:idx_h1] + new_html_block + content[idx_h2:]

path.write_text(content, encoding="utf-8")
print("pipeline/local_harness.py successfully updated!")
