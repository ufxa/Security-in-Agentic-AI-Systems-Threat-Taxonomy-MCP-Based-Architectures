"""
AEGIS-MCP Layer 3: Trust Attestation Engine
Computes the Agent Trust Score (ATS) as defined in the paper:

    ATS(a, t) = w_c * C(a,t) + w_r * R(a) + w_b * B(a) + w_a * A(a)

where:
  C(a,t) = cryptographic trust component
  R(a)   = reputation component
  B(a)   = behavioral component
  A(a)   = attestation component
  Weights (default): w_c=0.4, w_r=0.3, w_b=0.2, w_a=0.1
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


ATS_TRUSTED = 0.75
ATS_RESTRICTED = 0.50


@dataclass
class CryptographicEvidence:
    cert_valid: bool = False
    cert_not_expired: bool = False
    signature_verified: bool = False
    tls_version: str = "unknown"
    cert_age_days: int = 0

    def score(self) -> float:
        s = 0.0
        if self.cert_valid:
            s += 0.4
        if self.cert_not_expired:
            s += 0.2
        if self.signature_verified:
            s += 0.3
        if self.tls_version in ("TLSv1.3", "TLSv1.2"):
            s += 0.1
        return min(s, 1.0)


@dataclass
class ReputationEvidence:
    known_cve_count: int = 0
    registry_age_days: int = 0
    community_score: float = 0.5
    verified_publisher: bool = False
    downloads_last_30d: int = 0

    def score(self) -> float:
        cve_penalty = min(self.known_cve_count * 0.15, 0.6)
        age_bonus = min(self.registry_age_days / 365, 1.0) * 0.3
        community = self.community_score * 0.4
        publisher_bonus = 0.2 if self.verified_publisher else 0.0
        download_bonus = min(self.downloads_last_30d / 10000, 1.0) * 0.1
        return max(0.0, min(community + age_bonus + publisher_bonus + download_bonus - cve_penalty, 1.0))


@dataclass
class BehavioralEvidence:
    request_rate_anomaly: bool = False
    unusual_tool_sequence: bool = False
    parameter_distribution_anomaly: bool = False
    resource_usage_spike: bool = False
    prior_violations: int = 0
    session_duration_minutes: float = 0.0

    def score(self) -> float:
        penalty = 0.0
        if self.request_rate_anomaly:
            penalty += 0.25
        if self.unusual_tool_sequence:
            penalty += 0.30
        if self.parameter_distribution_anomaly:
            penalty += 0.20
        if self.resource_usage_spike:
            penalty += 0.15
        penalty += min(self.prior_violations * 0.10, 0.40)
        return max(0.0, 1.0 - penalty)


@dataclass
class AttestationEvidence:
    proof_of_non_malicious: bool = False
    zk_proof_valid: bool = False
    attestation_timestamp: Optional[datetime] = None
    attestation_age_hours: float = float("inf")

    def score(self) -> float:
        if not self.proof_of_non_malicious:
            return 0.0
        s = 0.5
        if self.zk_proof_valid:
            s += 0.3
        freshness = max(0.0, 1.0 - self.attestation_age_hours / 24.0)
        s += freshness * 0.2
        return min(s, 1.0)


@dataclass
class ATSResult:
    agent_id: str
    ats: float
    c_score: float
    r_score: float
    b_score: float
    a_score: float
    tier: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def capability_tier(self) -> str:
        if self.ats >= ATS_TRUSTED:
            return "trusted"
        elif self.ats >= ATS_RESTRICTED:
            return "restricted"
        return "quarantine"


class TrustAttestationEngine:
    """
    Layer 3: Agent Trust Score computation.

    Implements Equation (1) from the paper with configurable weights.
    Default weights: w_c=0.4, w_r=0.3, w_b=0.2, w_a=0.1
    """

    def __init__(self, w_c: float = 0.4, w_r: float = 0.3,
                 w_b: float = 0.2, w_a: float = 0.1):
        assert abs(w_c + w_r + w_b + w_a - 1.0) < 1e-6, "Weights must sum to 1.0"
        self.w_c = w_c
        self.w_r = w_r
        self.w_b = w_b
        self.w_a = w_a
        self._history: dict[str, list[ATSResult]] = {}

    def compute(
        self,
        agent_id: str,
        crypto: CryptographicEvidence,
        reputation: ReputationEvidence,
        behavioral: BehavioralEvidence,
        attestation: AttestationEvidence,
    ) -> ATSResult:
        c = crypto.score()
        r = reputation.score()
        b = behavioral.score()
        a = attestation.score()

        ats = self.w_c * c + self.w_r * r + self.w_b * b + self.w_a * a
        ats = round(min(max(ats, 0.0), 1.0), 4)

        result = ATSResult(
            agent_id=agent_id,
            ats=ats, c_score=c, r_score=r, b_score=b, a_score=a,
            tier=("trusted" if ats >= ATS_TRUSTED else
                  "restricted" if ats >= ATS_RESTRICTED else "quarantine"),
        )
        self._history.setdefault(agent_id, []).append(result)
        return result

    def get_history(self, agent_id: str) -> list[ATSResult]:
        return self._history.get(agent_id, [])

    def latest_ats(self, agent_id: str) -> Optional[float]:
        history = self._history.get(agent_id)
        return history[-1].ats if history else None
