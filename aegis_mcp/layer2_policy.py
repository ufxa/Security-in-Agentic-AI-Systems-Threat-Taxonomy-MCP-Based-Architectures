"""
AEGIS-MCP Layer 2: Policy Enforcement Engine
Capability-based access control for MCP tool invocations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CapabilityLevel(Enum):
    QUARANTINE = "quarantine"
    RESTRICTED = "restricted"
    TRUSTED = "trusted"


@dataclass
class CapabilityPolicy:
    agent_id: str
    level: CapabilityLevel
    allowed_tools: list = field(default_factory=list)
    denied_tools: list = field(default_factory=list)
    max_calls_per_minute: int = 60
    max_payload_bytes: int = 65536
    allow_filesystem: bool = False
    allow_network: bool = False
    allow_code_execution: bool = False


@dataclass
class PolicyDecision:
    allowed: bool
    agent_id: str
    tool_name: str
    reason: str
    capability_level: CapabilityLevel


class PolicyEnforcer:
    """
    Layer 2: Capability-based access control.

    Each agent receives a CapabilityPolicy that restricts:
    - Which tools may be invoked
    - Rate limits on tool calls
    - Resource access categories (filesystem, network, code execution)
    - Parameter size limits
    """

    FILESYSTEM_TOOLS = {"read_file", "write_file", "list_directory", "delete_file", "move_file"}
    NETWORK_TOOLS = {"http_request", "fetch_url", "dns_lookup", "port_scan", "socket_connect"}
    CODE_EXEC_TOOLS = {"run_python", "execute_bash", "run_javascript", "eval_code", "spawn_process"}

    QUARANTINE_DENIED = FILESYSTEM_TOOLS | NETWORK_TOOLS | CODE_EXEC_TOOLS
    RESTRICTED_DENIED = CODE_EXEC_TOOLS

    def __init__(self):
        self._policies: dict[str, CapabilityPolicy] = {}
        self._call_counts: dict[str, list] = {}

    def register_policy(self, policy: CapabilityPolicy) -> None:
        self._policies[policy.agent_id] = policy

    def get_default_policy(self, agent_id: str, ats: float) -> CapabilityPolicy:
        if ats >= 0.75:
            level = CapabilityLevel.TRUSTED
        elif ats >= 0.50:
            level = CapabilityLevel.RESTRICTED
        else:
            level = CapabilityLevel.QUARANTINE

        return CapabilityPolicy(
            agent_id=agent_id,
            level=level,
            allow_filesystem=(level == CapabilityLevel.TRUSTED),
            allow_network=(level == CapabilityLevel.TRUSTED),
            allow_code_execution=False,
            max_calls_per_minute=60 if level == CapabilityLevel.TRUSTED else 20,
        )

    def evaluate(self, agent_id: str, tool_name: str, payload_size: int = 0) -> PolicyDecision:
        policy = self._policies.get(agent_id)
        if policy is None:
            return PolicyDecision(
                allowed=False, agent_id=agent_id, tool_name=tool_name,
                reason="no_policy_registered", capability_level=CapabilityLevel.QUARANTINE
            )

        if tool_name in policy.denied_tools:
            return PolicyDecision(False, agent_id, tool_name, "explicitly_denied", policy.level)

        if policy.level == CapabilityLevel.QUARANTINE:
            if tool_name in self.QUARANTINE_DENIED:
                return PolicyDecision(False, agent_id, tool_name,
                                      f"quarantine_denies_{tool_name}", policy.level)

        if policy.level in (CapabilityLevel.QUARANTINE, CapabilityLevel.RESTRICTED):
            if tool_name in self.RESTRICTED_DENIED:
                return PolicyDecision(False, agent_id, tool_name,
                                      "code_execution_denied_below_trusted", policy.level)

        if not policy.allow_filesystem and tool_name in self.FILESYSTEM_TOOLS:
            return PolicyDecision(False, agent_id, tool_name, "filesystem_access_denied", policy.level)

        if not policy.allow_network and tool_name in self.NETWORK_TOOLS:
            return PolicyDecision(False, agent_id, tool_name, "network_access_denied", policy.level)

        if payload_size > policy.max_payload_bytes:
            return PolicyDecision(False, agent_id, tool_name, "payload_exceeds_limit", policy.level)

        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return PolicyDecision(False, agent_id, tool_name, "not_in_allowlist", policy.level)

        return PolicyDecision(True, agent_id, tool_name, "policy_satisfied", policy.level)
