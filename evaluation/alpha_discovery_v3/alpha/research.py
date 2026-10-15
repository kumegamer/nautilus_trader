"""Inert finite research journal: proposals have no gate or runtime authority."""

from .common import config


def diagnose(metrics):
    if metrics["trades"] < 20:
        return "Sparse activity: hypothesis not falsified reliably; no sample waiver."
    if metrics["net_pnl"] <= 0:
        if metrics["purged_trade_net"] + metrics["fees"] + metrics["slippage"] > 0:
            return "Gross mechanism insufficient to cover trading friction."
        return "Directional or entry mechanism has nonpositive chronological economics."
    if metrics["top1_share"] is not None and metrics["top1_share"] > 0.25:
        return "Positive result depends excessively on an individual outcome."
    return "Positive historical economics require independent cost, chronology, stability and concentration gates."


def local_observation(result):
    net = sum(t["net_pnl"] for t in result["trades"])
    return {
        "profile": result["candidate"],
        "symbol": result["symbol"],
        "scenario": result["scenario"],
        "net": net,
        "trades": len(result["trades"]),
        "diagnosis": "Nonpositive path; cannot promote."
        if net <= 0
        else "Positive path; await portfolio gates.",
        "proposal_authority": False,
        "automatic_activation": False,
    }


def journal(profiles):
    records = []
    for pid, e in profiles.items():
        diagnosis = diagnose(e["metrics"])
        records.append(
            {
                "hypothesis_id": pid,
                "step": "experiment_result_diagnosis",
                "diagnosis": diagnosis,
                "classification": e["classification"],
                "deterministic_gate_failures": e["failures"],
                "falsifiable_next_hypothesis": "Economic participation should transfer across chronological blocks if it is persistent.",
                "predeclared_followups": [pid + "_LOW", pid + "_HIGH"]
                if not pid.startswith("ML")
                else [],
                "next_version_proposal": "Collect forward unchanged-profile observations; reconsider mechanism only in a newly frozen version.",
                "proposal_status": "INERT_BUDGET_EXHAUSTED",
                "automatic_activation": False,
            }
        )
    return {
        "budget": config()["research_budget"],
        "iterations": records,
        "result_driven_revisions_executed": 0,
        "budget_exhausted": True,
        "explanation": "Research judgment predeclares mechanisms; deterministic observations and followups cannot optimize until success.",
    }
