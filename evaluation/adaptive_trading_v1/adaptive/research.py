"""Proposal-only agent interface and evidence-gated, timestamped promotion registry."""

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Protocol

from .common import DAY, config
from .profiles import library


class State(str, Enum):
    RESEARCH = "RESEARCH"
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    SHADOW = "SHADOW"
    CANARY_ELIGIBLE = "CANARY_ELIGIBLE"
    LIVE_ELIGIBLE = "LIVE_ELIGIBLE"
    DISABLED = "DISABLED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Proposal:
    hypothesis: str
    candidate: str
    priority: int
    diagnosis: str


class ResearchAgent(Protocol):
    def propose(self, diagnostics: dict) -> list[Proposal]: ...


class RuleResearchAgent:
    """Offline reproducible agent; no model credentials and no activation capability."""

    def propose(self, diagnostics):
        state = diagnostics.get("state", "INSUFFICIENT_DATA")
        result = [
            Proposal(
                "Pullbacks in low-volatility trends",
                "TP24",
                2,
                "Test directional re-entry",
            ),
            Proposal(
                "Mean reversion only in quiet range",
                "MR48",
                2,
                "Test liquidity provision economics",
            ),
            Proposal(
                "Expansion after compression", "VB48", 2, "Test volatility persistence"
            ),
            Proposal(
                "Funding-sensitive participation",
                "TB48_FUNDING",
                5,
                "Test carry-aware signal filtering",
            ),
            Proposal(
                "Breakout only in confirmed trends",
                "TB48",
                1,
                "Whipsaw risk outside persistent directional movement",
            ),
            Proposal(
                "Wider stop reduces volatility stop-outs",
                "TB48_STOP",
                3,
                "Test stop neighborhood against MAE/MFE",
            ),
            Proposal(
                "Short asymmetry requires separate validation",
                "TB48_SHORT",
                4,
                "Do not infer side permission from latest PnL",
            ),
        ]
        if state == "EXECUTION_DEGRADATION":
            result.insert(
                0,
                Proposal(
                    "Funding-sensitive participation",
                    "TB48_FUNDING",
                    0,
                    "Separate execution drag from signal failure",
                ),
            )
        return sorted(result, key=lambda p: p.priority)


def validate_proposals(proposals):
    known = library()
    for p in proposals:
        if (
            not isinstance(p, Proposal)
            or p.candidate not in known
            or p.candidate == "NO_TRADE"
        ):
            raise ValueError("AI proposal must name a declared immutable candidate")
    return proposals


class Registry:
    def __init__(self):
        self.states = {p: State.RESEARCH for p in library() if p != "NO_TRADE"}
        self.available = {"NO_TRADE": 0}
        self.evidence = {}
        self.quarantined_until = {}
        self.events = []

    def transition(self, profile, target, timestamp, evidence):
        old = self.states[profile]
        allowed = {
            State.RESEARCH: {State.CANDIDATE, State.REJECTED},
            State.CANDIDATE: {State.VALIDATED, State.REJECTED},
            State.VALIDATED: {State.SHADOW, State.DISABLED},
            State.SHADOW: {State.CANARY_ELIGIBLE, State.DISABLED, State.REJECTED},
            State.CANARY_ELIGIBLE: {State.DISABLED},
            State.DISABLED: {State.RESEARCH},
            State.REJECTED: {State.RESEARCH},
        }
        if target == State.LIVE_ELIGIBLE or target not in allowed.get(old, set()):
            raise ValueError(f"Forbidden promotion {old} -> {target}")
        if evidence.get("end_ns", timestamp + 1) > timestamp:
            raise ValueError("Promotion cannot use future evidence")
        if target == State.VALIDATED:
            gates = evidence.get("gates", {})
            required = {
                "sample",
                "validation_positive",
                "walk_forward",
                "sealed_oos",
                "cost_stress",
                "neighbors",
                "symbols",
                "drawdown",
                "concentration",
                "profit_factor",
                "regimes",
                "sides",
            }
            if set(gates) != required or not all(gates.values()):
                raise ValueError("Missing or failed validation gate")
        if target == State.CANARY_ELIGIBLE and not (
            evidence.get("shadow_days", 0) >= 30
            and evidence.get("shadow_trades", 0) >= 30
            and evidence.get("shadow_positive")
            and evidence.get("cost_stress")
        ):
            raise ValueError("Insufficient forward shadow evidence")
        self.states[profile] = target
        if target == State.SHADOW:
            self.available[profile] = timestamp + 1
        if target in (State.DISABLED, State.REJECTED, State.RESEARCH):
            self.available.pop(profile, None)
        self.evidence[profile] = evidence
        self.events.append(
            {
                "timestamp": timestamp,
                "profile": profile,
                "old_state": old.value,
                "new_state": target.value,
                "evidence": evidence,
            }
        )

    def eligible(self, timestamp):
        return [p for p, t in self.available.items() if t <= timestamp]

    def consider(self, profile, timestamp, evidence):
        if timestamp < self.quarantined_until.get(profile, 0):
            return
        if self.states[profile] in (State.REJECTED, State.DISABLED):
            self.transition(profile, State.RESEARCH, timestamp, {"end_ns": timestamp})
        if self.states[profile] != State.RESEARCH:
            return
        self.transition(profile, State.CANDIDATE, timestamp, evidence)
        if all(evidence["gates"].values()):
            self.transition(profile, State.VALIDATED, timestamp, evidence)
            self.transition(profile, State.SHADOW, timestamp, evidence)
        else:
            self.transition(profile, State.REJECTED, timestamp, evidence)


class ResearchLoop:
    def __init__(self, registry, evidence_provider, agent=None):
        self.registry, self.provider = registry, evidence_provider
        self.agent = agent or RuleResearchAgent()
        self.last_request = None
        self.events = []

    def request(self, timestamp, diagnostics):
        if (
            self.last_request is not None
            and timestamp - self.last_request
            < config()["policy"]["research_cooldown_days"] * DAY
        ):
            return
        self.last_request = timestamp
        proposals = validate_proposals(self.agent.propose(diagnostics))
        for proposal in proposals:
            evidence = self.provider(proposal.candidate, timestamp)
            event = {
                "timestamp": timestamp,
                "diagnostics": diagnostics,
                "proposal": asdict(proposal),
                "pipeline": [
                    "diagnosis",
                    "hypothesis",
                    "historical",
                    "walk_forward",
                    "sealed_oos",
                    "cost_stress",
                    "neighbors",
                    "shadow",
                ],
                "evidence": evidence,
                "status": "REJECT",
            }
            if evidence is None:
                event["reason"] = "INSUFFICIENT_MATURED_EVIDENCE"
            else:
                self.registry.consider(proposal.candidate, timestamp, evidence)
                event["status"] = self.registry.states[proposal.candidate].value
                event["reason"] = "PREDECLARED_EVIDENCE_GATES"
            encoded = json.dumps(event, sort_keys=True).encode()
            event["event_sha256"] = hashlib.sha256(encoded).hexdigest()
            self.events.append(event)
