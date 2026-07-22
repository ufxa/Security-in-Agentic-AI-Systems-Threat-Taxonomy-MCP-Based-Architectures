"""
MCP-TaxSec: Six-Vector Threat Taxonomy Classifier
Classifies MCP-related security events into the six primary attack vectors.

Attack Vectors:
  TI - Tool Injection
  MP - Memory Poisoning
  PM - Prompt Manipulation
  TC - Transport Compromise
  SC - Supply Chain Attack
  AA - Agent-to-Agent Exploitation
"""

import re
from dataclasses import dataclass
from typing import Optional


VECTOR_SIGNATURES = {
    "TI": {
        "description": "Tool Injection",
        "subtypes": {
            "TI-1": "Malicious Tool Description",
            "TI-2": "Shadow Tool Injection",
            "TI-3": "Tool Chaining / Privilege Escalation",
            "TI-4": "Side-Channel Exfiltration via Tool Output",
        },
        "patterns": [
            r"tools/list.*description.*ignore",
            r"tool.*schema.*inject",
            r"malicious.*tool.*def",
            r"shadow.*tool",
            r"tool.*chain.*escalat",
            r"side.?channel.*exfil",
            r"tool.*description.*system.?prompt",
        ],
        "keywords": ["tool injection", "schema injection", "tool definition",
                     "shadow tool", "tool chaining", "capability escalation"],
    },
    "MP": {
        "description": "Memory Poisoning",
        "subtypes": {
            "MP-1": "Context Injection",
            "MP-2": "Persistent Backdoor via Knowledge Base",
            "MP-3": "Cross-Session Memory Leak",
        },
        "patterns": [
            r"context.*inject|inject.*context",
            r"memory.*poison|poison.*memory",
            r"knowledge.?base.*manipulat",
            r"embedding.*poison",
            r"cross.?session.*leak",
            r"persistent.*backdoor.*memory",
            r"rag.*poison|poison.*rag",
        ],
        "keywords": ["memory poisoning", "context injection", "knowledge base",
                     "embedding", "cross-session", "persistent backdoor"],
    },
    "PM": {
        "description": "Prompt Manipulation",
        "subtypes": {
            "PM-1": "Goal Hijacking",
            "PM-2": "Role Confusion",
            "PM-3": "Delimiter Injection",
        },
        "patterns": [
            r"prompt.*inject|inject.*prompt",
            r"goal.*hijack|hijack.*goal",
            r"role.*confusion|system.*prompt.*override",
            r"delimiter.*inject",
            r"jailbreak",
            r"ignore.*previous.*instructions",
            r"you are now",
        ],
        "keywords": ["prompt injection", "goal hijacking", "role confusion",
                     "delimiter injection", "jailbreak", "system prompt"],
    },
    "TC": {
        "description": "Transport Compromise",
        "subtypes": {
            "TC-1": "JSON-RPC Message Hijacking",
            "TC-2": "SSE Stream Injection",
        },
        "patterns": [
            r"json.?rpc.*hijack|hijack.*json.?rpc",
            r"mitm|man.in.the.middle",
            r"sse.*inject|stream.*inject",
            r"tls.*downgrade|ssl.*strip",
            r"transport.*compromise",
            r"stdio.*intercept",
            r"websocket.*inject",
        ],
        "keywords": ["transport compromise", "json-rpc hijacking", "MITM",
                     "SSE injection", "TLS downgrade", "stdio"],
    },
    "SC": {
        "description": "Supply Chain Attack",
        "subtypes": {
            "SC-1": "Typosquatting / Registry Namespace Attack",
            "SC-2": "Trojanized Server / Malicious Update",
            "SC-3": "Dependency Confusion",
            "SC-4": "Registry Account Takeover",
        },
        "patterns": [
            r"typosquat",
            r"trojan.*server|malicious.*package",
            r"dependency.*confusion",
            r"registry.*takeover|account.*takeover",
            r"supply.?chain",
            r"malicious.*update|backdoor.*package",
            r"npm.*poison|pip.*poison",
        ],
        "keywords": ["supply chain", "typosquatting", "trojanized", "dependency confusion",
                     "registry", "account takeover", "malicious package"],
    },
    "AA": {
        "description": "Agent-to-Agent Exploitation",
        "subtypes": {
            "AA-1": "Trust Escalation via Identity Forgery",
            "AA-2": "Orchestrator Compromise",
            "AA-3": "Lateral Movement",
        },
        "patterns": [
            r"agent.to.agent|inter.?agent",
            r"trust.*escalat|escalat.*trust",
            r"orchestrat.*comprom",
            r"lateral.*movement.*agent",
            r"agent.*boundary.*bypass",
            r"multi.?agent.*attack",
            r"capability.*cascad",
        ],
        "keywords": ["agent-to-agent", "trust escalation", "orchestrator",
                     "lateral movement", "multi-agent", "capability cascading"],
    },
}


@dataclass
class ClassificationResult:
    primary_vector: str
    subtype: Optional[str]
    confidence: float
    matched_patterns: list[str]
    all_scores: dict[str, float]
    description: str


class MCPTaxSecClassifier:
    """
    Rule-based classifier mapping security events to MCP-TaxSec attack vectors.

    Uses pattern matching on event descriptions and contextual signals.
    For production use, replace with the trained ML classifier from experiments/.
    """

    def __init__(self):
        self._compiled: dict[str, list] = {}
        for vector, data in VECTOR_SIGNATURES.items():
            self._compiled[vector] = [re.compile(p, re.IGNORECASE) for p in data["patterns"]]

    def classify(self, event_text: str, context: Optional[dict] = None) -> ClassificationResult:
        scores: dict[str, float] = {}
        matched: dict[str, list] = {}

        for vector, patterns in self._compiled.items():
            score = 0.0
            hits = []
            for pat in patterns:
                if pat.search(event_text):
                    score += 1.0 / len(patterns)
                    hits.append(pat.pattern[:40])

            keywords = VECTOR_SIGNATURES[vector]["keywords"]
            for kw in keywords:
                if kw.lower() in event_text.lower():
                    score += 0.05

            scores[vector] = min(score, 1.0)
            matched[vector] = hits

        if not any(scores.values()):
            return ClassificationResult("UNKNOWN", None, 0.0, [], scores,
                                        "No matching attack vector found")

        primary = max(scores, key=scores.get)
        confidence = scores[primary]

        subtype = self._infer_subtype(primary, event_text)

        return ClassificationResult(
            primary_vector=primary,
            subtype=subtype,
            confidence=round(confidence, 3),
            matched_patterns=matched[primary],
            all_scores={k: round(v, 3) for k, v in scores.items()},
            description=VECTOR_SIGNATURES[primary]["description"],
        )

    def _infer_subtype(self, vector: str, text: str) -> Optional[str]:
        subtypes = VECTOR_SIGNATURES[vector]["subtypes"]
        subtype_patterns = {
            "TI": {"TI-1": r"description|schema|tool.def",
                   "TI-2": r"shadow|override|replac",
                   "TI-3": r"chain|escalat|sequen",
                   "TI-4": r"exfil|side.channel|timing"},
            "MP": {"MP-1": r"context|inject|history",
                   "MP-2": r"knowledge|embed|rag|persist",
                   "MP-3": r"cross.session|leak|share"},
            "PM": {"PM-1": r"goal|hijack|objective",
                   "PM-2": r"role|persona|identity|confus",
                   "PM-3": r"delimiter|boundary|inject"},
            "TC": {"TC-1": r"json.?rpc|hijack|intercept",
                   "TC-2": r"sse|stream|event"},
            "SC": {"SC-1": r"typosquat|namespace|similar",
                   "SC-2": r"trojan|backdoor|update|malicious",
                   "SC-3": r"dependency|confusion|public.private",
                   "SC-4": r"takeover|credential|account"},
            "AA": {"AA-1": r"trust|escalat|identity|forg",
                   "AA-2": r"orchestrat|queue|task",
                   "AA-3": r"lateral|propagat|spread"},
        }.get(vector, {})

        for sub_id, pat in subtype_patterns.items():
            if re.search(pat, text, re.IGNORECASE):
                return sub_id
        return list(subtypes.keys())[0] if subtypes else None
