"""Append-only structured audit logger for Clearance & Last Pay document pipeline."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pipeline.models import ExtractionResult


def compute_file_sha256(file_path: str) -> str:
    """Computes the SHA-256 hash of a local file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes the SHA-256 hash of in-memory bytes."""
    return hashlib.sha256(data).hexdigest()


class AuditLogger:
    """Append-only audit logger writing structured JSONL entries."""

    def __init__(self, log_path: str = "logs/audit_log.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_extraction(
        self,
        result: ExtractionResult,
        caller_id: str = "system",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Logs an automated extraction and pre-check event to the audit log."""
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "log_type": "DOCUMENT_EXTRACTION",
            "timestamp": timestamp,
            "caller_id": caller_id,
            "document_id": result.metadata.document_id,
            "file_name": result.metadata.file_name,
            "file_hash_sha256": result.metadata.file_hash_sha256,
            "document_type": result.document_type.value,
            "model_id": result.metadata.model_id,
            "processing_time_ms": result.metadata.processing_time_ms,
            "overall_confidence": result.overall_confidence,
            "flags": [flag.model_dump() for flag in result.flags],
            "flag_count": len(result.flags),
            "notes": notes,
        }

        self._append_line(entry)
        return entry

    def log_human_action(
        self,
        dossier_id: str,
        approver_id: str,
        role: str,
        action: str,  # APPROVE, REJECT, REQUEST_REVISION
        flags_reviewed: List[str],
        override_justification: str = "",
    ) -> Dict[str, Any]:
        """Logs an explicit human approver action, satisfying the constitutional audit requirement."""
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "log_type": "HUMAN_DECISION",
            "timestamp": timestamp,
            "dossier_id": dossier_id,
            "approver_id": approver_id,
            "role": role,
            "action": action,
            "flags_reviewed": flags_reviewed,
            "override_justification": override_justification,
        }

        self._append_line(entry)
        return entry

    def _append_line(self, entry: Dict[str, Any]) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent log entries, newest first."""
        if not self.log_path.exists():
            return []

        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
