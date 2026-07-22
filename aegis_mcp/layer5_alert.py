"""
AEGIS-MCP Layer 5: Alert & Response Engine
Real-time alerting and automated response on high-confidence threats.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResponseAction(Enum):
    LOG_ONLY = "log_only"
    FLAG = "flag"
    RATE_LIMIT = "rate_limit"
    QUARANTINE_REQUEST = "quarantine_request"
    REVOKE_CAPABILITY = "revoke_capability"
    TERMINATE_SESSION = "terminate_session"
    NOTIFY_OPERATOR = "notify_operator"


@dataclass
class Alert:
    alert_id: str
    timestamp: str
    severity: Severity
    agent_id: str
    event_type: str
    risk_score: float
    description: str
    response_actions: list[ResponseAction]
    auto_resolved: bool = False
    resolved_at: Optional[str] = None


def _default_risk_to_severity(risk: float) -> Severity:
    if risk >= 0.85:
        return Severity.CRITICAL
    elif risk >= 0.70:
        return Severity.HIGH
    elif risk >= 0.40:
        return Severity.MEDIUM
    return Severity.LOW


def _default_response_policy(severity: Severity) -> list[ResponseAction]:
    if severity == Severity.CRITICAL:
        return [ResponseAction.TERMINATE_SESSION,
                ResponseAction.REVOKE_CAPABILITY,
                ResponseAction.NOTIFY_OPERATOR]
    elif severity == Severity.HIGH:
        return [ResponseAction.QUARANTINE_REQUEST,
                ResponseAction.REVOKE_CAPABILITY,
                ResponseAction.NOTIFY_OPERATOR]
    elif severity == Severity.MEDIUM:
        return [ResponseAction.FLAG,
                ResponseAction.RATE_LIMIT]
    return [ResponseAction.LOG_ONLY]


class AlertResponseEngine:
    """
    Layer 5: Real-time alert generation and automated response.

    Converts risk scores from Layers 1-3 into structured alerts
    and executes response actions (quarantine, revocation, notification).
    """

    def __init__(
        self,
        risk_threshold: float = 0.70,
        severity_fn: Optional[Callable] = None,
        response_fn: Optional[Callable] = None,
        notification_hook: Optional[Callable[[Alert], None]] = None,
    ):
        self.risk_threshold = risk_threshold
        self._severity_fn = severity_fn or _default_risk_to_severity
        self._response_fn = response_fn or _default_response_policy
        self._notification_hook = notification_hook
        self._alerts: list[Alert] = []
        self._quarantined_agents: set[str] = set()
        self._revoked_agents: set[str] = set()
        self._seq = 0

    def process(self, agent_id: str, event_type: str,
                risk_score: float, description: str = "") -> Optional[Alert]:
        if risk_score < self.risk_threshold and risk_score < 0.30:
            return None

        severity = self._severity_fn(risk_score)
        actions = self._response_fn(severity)

        alert = Alert(
            alert_id=f"AEGIS-{self._seq:06d}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            agent_id=agent_id,
            event_type=event_type,
            risk_score=risk_score,
            description=description or event_type,
            response_actions=actions,
        )
        self._seq += 1
        self._alerts.append(alert)

        self._execute_responses(alert)

        if self._notification_hook and severity in (Severity.HIGH, Severity.CRITICAL):
            self._notification_hook(alert)

        return alert

    def _execute_responses(self, alert: Alert) -> None:
        for action in alert.response_actions:
            if action == ResponseAction.QUARANTINE_REQUEST:
                self._quarantined_agents.add(alert.agent_id)
            elif action == ResponseAction.REVOKE_CAPABILITY:
                self._revoked_agents.add(alert.agent_id)
            elif action == ResponseAction.TERMINATE_SESSION:
                self._quarantined_agents.add(alert.agent_id)
                self._revoked_agents.add(alert.agent_id)

    def is_quarantined(self, agent_id: str) -> bool:
        return agent_id in self._quarantined_agents

    def is_revoked(self, agent_id: str) -> bool:
        return agent_id in self._revoked_agents

    def get_alerts(self, min_severity: Severity = Severity.LOW) -> list[Alert]:
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        threshold_idx = order.index(min_severity)
        return [a for a in self._alerts if order.index(a.severity) >= threshold_idx]
