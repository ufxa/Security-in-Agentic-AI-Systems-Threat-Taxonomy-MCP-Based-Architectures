"""
AEGIS-MCP: Adaptive Engine for Guardian-Integrated Security in MCP

Five-layer runtime defense framework for Model Context Protocol deployments.
Reference implementation for:
  Costa, A. D. "Security in Agentic AI Systems: Threat Taxonomy and Defense
  Frameworks for MCP-Based Architectures." IEEE Trans. Inf. Forensics Security, 2026.
"""

from .layer1_protocol import ProtocolInterceptor
from .layer2_policy import PolicyEnforcer
from .layer3_trust import TrustAttestationEngine
from .layer4_audit import ForensicAuditLog
from .layer5_alert import AlertResponseEngine
from .aegis_mcp import AEGISMCP

__version__ = "1.0.0"
__all__ = [
    "AEGISMCP",
    "ProtocolInterceptor",
    "PolicyEnforcer",
    "TrustAttestationEngine",
    "ForensicAuditLog",
    "AlertResponseEngine",
]
