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
