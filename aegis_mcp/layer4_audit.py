"""
AEGIS-MCP Layer 4: Forensic Audit Log
Immutable, tamper-evident audit trail of all tool invocations and policy decisions.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class AuditEntry:
    seq: int
    timestamp: str
    event_type: str
    agent_id: str
    tool_name: Optional[str]
    action: str
    risk_score: float
    details: dict
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        data = json.dumps(asdict(self), sort_keys=True, default=str).encode()
        return hashlib.sha256(data).hexdigest()


class ForensicAuditLog:
    """
    Layer 4: Immutable forensic audit log with hash chaining.

    Each entry is cryptographically linked to the previous one,
    making tampering detectable. Optionally persists to disk as JSONL.
    """

    def __init__(self, log_path: Optional[Path] = None):
        self._entries: list[AuditEntry] = []
        self._log_path = log_path
        self._seq = 0

    def _genesis_hash(self) -> str:
        return hashlib.sha256(b"AEGIS-MCP-GENESIS-2026").hexdigest()

    def log(self, event_type: str, agent_id: str, action: str,
            risk_score: float = 0.0, tool_name: Optional[str] = None,
            details: Optional[dict] = None) -> AuditEntry:
        prev_hash = self._entries[-1].entry_hash if self._entries else self._genesis_hash()
        entry = AuditEntry(
            seq=self._seq,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            agent_id=agent_id,
            tool_name=tool_name,
            action=action,
            risk_score=risk_score,
            details=details or {},
            prev_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self._entries.append(entry)
        self._seq += 1

        if self._log_path:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(asdict(entry), default=str) + "\n")

        return entry

    def verify_chain(self) -> tuple[bool, Optional[int]]:
        if not self._entries:
            return True, None
        prev = self._genesis_hash()
        for i, entry in enumerate(self._entries):
            stored_hash = entry.entry_hash
            entry.entry_hash = ""
            expected = entry.compute_hash()
            entry.entry_hash = stored_hash
            if stored_hash != expected:
                return False, i
            if entry.prev_hash != prev:
                return False, i
            prev = stored_hash
        return True, None

    def query(self, agent_id: Optional[str] = None,
              event_type: Optional[str] = None,
              min_risk: float = 0.0) -> list[AuditEntry]:
        results = self._entries
        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if min_risk > 0:
            results = [e for e in results if e.risk_score >= min_risk]
        return results

    def export_json(self) -> str:
        return json.dumps([asdict(e) for e in self._entries], indent=2, default=str)
