"""Untrusted research proposals are durable data, with no runtime activation channel."""

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Protocol

from .common import write_json

STAGES = (
    "RESEARCH",
    "BACKTEST",
    "WALK_FORWARD",
    "COST_STRESS",
    "STABILITY",
    "SHADOW_ELIGIBLE",
)


@dataclass(frozen=True)
class Proposal:
    hypothesis: str
    explanation: str
    experiment: str
    evidence_references: tuple[str, ...]
    proposed_change: str


class ResearchAgent(Protocol):
    def propose(self, evidence: dict) -> list[Proposal]: ...


def save_proposals(agent: ResearchAgent, evidence, destination):
    proposals = agent.propose(json.loads(json.dumps(evidence)))
    records = []
    for p in proposals:
        if not isinstance(p, Proposal) or not p.hypothesis or not p.evidence_references:
            raise ValueError(
                "Research proposal requires a hypothesis and evidence references"
            )
        payload = asdict(p)
        records.append(
            {
                "proposal_sha256": hashlib.sha256(
                    json.dumps(payload, sort_keys=True).encode()
                ).hexdigest(),
                "proposal": payload,
                "stage": "RESEARCH",
                "evidence_sha256": hashlib.sha256(
                    json.dumps(evidence, sort_keys=True).encode()
                ).hexdigest(),
                "structured_evidence": evidence,
                "required_pipeline": STAGES,
                "activation": "PROHIBITED",
                "requires_new_version": True,
            }
        )
    write_json(destination, records)
    return records


class DiagnosticAgent:
    """Deterministic example implementation; replace with an external model off-path."""

    def propose(self, evidence):
        return [
            Proposal(
                "The value of regime invalidation may depend on the profile",
                "Review complete policy simulations, including null or adverse effects, before proposing a new version",
                "Review four predeclared exits without adding thresholds",
                tuple(evidence.get("references", ["results/exit_policy_results.csv"])),
                "No executable change; review as a new-version hypothesis",
            )
        ]
