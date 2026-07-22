"""
AEGIS-MCP Layer 1: Protocol Interception
Validates all MCP JSON-RPC 2.0 messages at the client-server boundary.
Performs schema validation, syntax anomaly detection, and HMAC integrity checks.
"""

import json
import hmac
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional


MALICIOUS_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"you\s+are\s+now\s+(a|an)\s+\w+",
    r"system\s*:\s*\[",
    r"<\|im_start\|>",
    r"\[INST\]",
    r"###\s*(human|assistant|system)\s*:",
    r"bypass\s+(safety|filter|restriction)",
    r"DAN\s+mode",
]

SUSPICIOUS_TOOL_PATTERNS = [
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
    r"subprocess",
    r"os\.system",
    r"base64\.b64decode",
    r"\\x[0-9a-fA-F]{2}",
]


@dataclass
class ValidationResult:
    valid: bool
    message_id: Optional[str] = None
    anomalies: list = field(default_factory=list)
    risk_score: float = 0.0
    action: str = "allow"


class ProtocolInterceptor:
    """
    Layer 1: Protocol-level validation of MCP JSON-RPC messages.

    Intercepts all messages between MCP client and server, performing:
    - JSON-RPC 2.0 schema compliance validation
    - Payload size and structure anomaly detection
    - Injection pattern detection in string fields
    - HMAC-based message integrity verification
    """

    def __init__(self, hmac_secret: Optional[bytes] = None, max_payload_bytes: int = 1_048_576):
        self.hmac_secret = hmac_secret or b"aegis-mcp-default-secret"
        self.max_payload_bytes = max_payload_bytes
        self._compiled_malicious = [re.compile(p, re.IGNORECASE) for p in MALICIOUS_PATTERNS]
        self._compiled_suspicious = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_TOOL_PATTERNS]

    def validate(self, raw_message: str, direction: str = "client->server") -> ValidationResult:
        anomalies = []
        risk_score = 0.0

        if len(raw_message.encode()) > self.max_payload_bytes:
            return ValidationResult(False, anomalies=["payload_too_large"], risk_score=1.0, action="block")

        try:
            msg = json.loads(raw_message)
        except json.JSONDecodeError as e:
            return ValidationResult(False, anomalies=[f"invalid_json: {e}"], risk_score=0.9, action="block")

        if msg.get("jsonrpc") != "2.0":
            anomalies.append("missing_or_invalid_jsonrpc_version")
            risk_score += 0.3

        msg_id = str(msg.get("id", "notification"))

        if "method" in msg:
            method = msg["method"]
            if not isinstance(method, str):
                anomalies.append("non_string_method")
                risk_score += 0.4

            allowed_methods = {
                "initialize", "tools/list", "tools/call",
                "resources/read", "resources/list",
                "prompts/get", "prompts/list",
                "ping", "notifications/initialized",
                "notifications/cancelled",
            }
            if method not in allowed_methods:
                anomalies.append(f"unknown_method: {method}")
                risk_score += 0.2

            if method == "tools/call":
                params = msg.get("params", {})
                score, flags = self._scan_tool_call(params)
                risk_score += score
                anomalies.extend(flags)

        content_str = json.dumps(msg)
        for pattern in self._compiled_malicious:
            if pattern.search(content_str):
                anomalies.append(f"injection_pattern: {pattern.pattern[:40]}")
                risk_score += 0.5

        risk_score = min(risk_score, 1.0)
        action = "block" if risk_score >= 0.7 else ("flag" if risk_score >= 0.3 else "allow")
        return ValidationResult(valid=(action != "block"), message_id=msg_id,
                                anomalies=anomalies, risk_score=risk_score, action=action)

    def _scan_tool_call(self, params: dict) -> tuple[float, list]:
        score = 0.0
        flags = []
        tool_name = params.get("name", "")
        arguments = json.dumps(params.get("arguments", {}))

        if len(tool_name) > 128:
            flags.append("tool_name_too_long")
            score += 0.2

        for pattern in self._compiled_suspicious:
            if pattern.search(arguments):
                flags.append(f"suspicious_arg_pattern: {pattern.pattern[:30]}")
                score += 0.4
                break

        if len(arguments) > 65536:
            flags.append("oversized_arguments")
            score += 0.3

        return score, flags

    def sign_message(self, raw_message: str) -> str:
        mac = hmac.new(self.hmac_secret, raw_message.encode(), hashlib.sha256)
        return mac.hexdigest()

    def verify_signature(self, raw_message: str, signature: str) -> bool:
        expected = self.sign_message(raw_message)
        return hmac.compare_digest(expected, signature)
