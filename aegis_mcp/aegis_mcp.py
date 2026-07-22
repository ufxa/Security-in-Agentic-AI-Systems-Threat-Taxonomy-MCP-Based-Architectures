"""
AEGIS-MCP: Main Orchestrator
Coordinates all five layers for end-to-end MCP message security evaluation.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .layer1_protocol import ProtocolInterceptor
from .layer2_policy import PolicyEnforcer, CapabilityPolicy, CapabilityLevel
from .layer3_trust import (TrustAttestationEngine, CryptographicEvidence,
                           ReputationEvidence, BehavioralEvidence, AttestationEvidence)
from .layer4_audit import ForensicAuditLog
from .layer5_alert import AlertResponseEngine, Severity


@dataclass
class EvaluationResult:
    allowed: bool
    agent_id: str
    risk_score: float
    ats: float
    capability_tier: str
    actions_taken: list[str]
    alert_id: Optional[str] = None


class AEGISMCP:
    """
    AEGIS-MCP five-layer security orchestrator.

    Usage:
        aegis = AEGISMCP()
        result = aegis.evaluate(
            raw_message='{"jsonrpc":"2.0","method":"tools/call","params":{"name":"read_file",...},"id":1}',
            agent_id="agent-001",
            crypto=CryptographicEvidence(cert_valid=True, signature_verified=True, tls_version="TLSv1.3"),
            reputation=ReputationEvidence(registry_age_days=365, community_score=0.9),
            behavioral=BehavioralEvidence(),
            attestation=AttestationEvidence(proof_of_non_malicious=True),
        )
    """

    def __init__(
        self,
        hmac_secret: Optional[bytes] = None,
        log_path: Optional[Path] = None,
        ats_weights: tuple = (0.4, 0.3, 0.2, 0.1),
        alert_threshold: float = 0.70,
    ):
        self.layer1 = ProtocolInterceptor(hmac_secret=hmac_secret)
        self.layer2 = PolicyEnforcer()
        self.layer3 = TrustAttestationEngine(*ats_weights)
        self.layer4 = ForensicAuditLog(log_path=log_path)
        self.layer5 = AlertResponseEngine(risk_threshold=alert_threshold)

    def evaluate(
        self,
        raw_message: str,
        agent_id: str,
        crypto: Optional[CryptographicEvidence] = None,
        reputation: Optional[ReputationEvidence] = None,
        behavioral: Optional[BehavioralEvidence] = None,
        attestation: Optional[AttestationEvidence] = None,
    ) -> EvaluationResult:
        actions = []

        # Layer 1: Protocol validation
        l1 = self.layer1.validate(raw_message)
        self.layer4.log("L1_VALIDATION", agent_id, l1.action, l1.risk_score,
                        details={"anomalies": l1.anomalies})

        if not l1.valid:
            self.layer5.process(agent_id, "protocol_violation", l1.risk_score,
                                str(l1.anomalies))
            return EvaluationResult(False, agent_id, l1.risk_score, 0.0,
                                    "quarantine", ["L1_BLOCK"])

        # Layer 3: ATS computation (before policy enforcement)
        ats_result = self.layer3.compute(
            agent_id,
            crypto or CryptographicEvidence(),
            reputation or ReputationEvidence(),
            behavioral or BehavioralEvidence(),
            attestation or AttestationEvidence(),
        )
        self.layer4.log("L3_ATS", agent_id, "computed", 0.0,
                        details={"ats": ats_result.ats, "tier": ats_result.tier})

        # Layer 2: Policy enforcement based on ATS tier
        if agent_id not in self.layer2._policies:
            policy = self.layer2.get_default_policy(agent_id, ats_result.ats)
            self.layer2.register_policy(policy)

        try:
            msg = json.loads(raw_message)
            tool_name = msg.get("params", {}).get("name", "") if msg.get("method") == "tools/call" else ""
            payload_size = len(raw_message)
        except Exception:
            tool_name = ""
            payload_size = len(raw_message)

        l2 = self.layer2.evaluate(agent_id, tool_name, payload_size)
        self.layer4.log("L2_POLICY", agent_id, "allowed" if l2.allowed else "denied",
                        0.0 if l2.allowed else 0.5, tool_name=tool_name,
                        details={"reason": l2.reason, "tier": l2.capability_level.value})

        if not l2.allowed:
            actions.append("L2_DENY")
            combined_risk = max(l1.risk_score, 0.5)
            alert = self.layer5.process(agent_id, "policy_violation", combined_risk, l2.reason)
            return EvaluationResult(False, agent_id, combined_risk, ats_result.ats,
                                    ats_result.tier, actions,
                                    alert_id=alert.alert_id if alert else None)

        # Layer 5: Alert on elevated risk
        combined_risk = max(l1.risk_score, 1.0 - ats_result.ats)
        alert = self.layer5.process(agent_id, "evaluation_complete", combined_risk)

        if alert and alert.severity in (Severity.HIGH, Severity.CRITICAL):
            actions.append(f"L5_ALERT_{alert.severity.value.upper()}")

        actions.append("ALLOWED" if l2.allowed else "DENIED")
        return EvaluationResult(
            allowed=l2.allowed,
            agent_id=agent_id,
            risk_score=combined_risk,
            ats=ats_result.ats,
            capability_tier=ats_result.tier,
            actions_taken=actions,
            alert_id=alert.alert_id if alert else None,
        )
