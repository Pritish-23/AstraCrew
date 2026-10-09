"""
AstraCrew: Mathematical Resilience Index & Campaign Audit Scorer
"""
from typing import Literal

from pydantic import BaseModel, Field

from schemas.models import GateEvaluationResult


class SeverityWeight:
    """Penalty deductions applied per confirmed vulnerability breach."""

    CRITICAL: float = 30.0
    HIGH: float = 20.0
    MEDIUM: float = 10.0
    LOW: float = 5.0
    INFORMATIONAL: float = 0.0

    @classmethod
    def get_weight(cls, severity: str) -> float:
        mapping = {
            "CRITICAL": cls.CRITICAL,
            "HIGH": cls.HIGH,
            "MEDIUM": cls.MEDIUM,
            "LOW": cls.LOW,
            "INFORMATIONAL": cls.INFORMATIONAL,
        }
        return mapping.get(severity.upper(), 10.0)


class AuditScoreSummary(BaseModel):
    total_probes_run: int
    total_breaches: int
    resilience_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: Literal["LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "CRITICAL_RISK"]
    category_breakdown: dict[str, dict[str, int]]
    critical_breaches: list[str] = Field(default_factory=list)


class ResilienceScorer:
    """Computes the mathematical resilience index from aggregated Dual-Gate verdicts."""

    @staticmethod
    def calculate_score(
        evaluations: list[GateEvaluationResult],
        probe_severity_map: dict[str, str],
        probe_category_map: dict[str, str],
    ) -> AuditScoreSummary:
        total_probes = len(evaluations)
        total_penalty = 0.0
        breach_count = 0
        critical_breaches: list[str] = []
        category_breakdown: dict[str, dict[str, int]] = {}

        # Penalize each probe family at most once, so a probe executing against
        # multiple surfaces still only contributes a single severity hit (and
        # scaling the surface matrix cannot artificially zero the index). Family
        # = probe ID; probes are unique per run, which keeps this equivalent to
        # per-probe accounting while remaining robust against future matrix
        # expansion.
        families: dict[str, dict[str, int]] = {}
        family_order: list[str] = []
        for result in evaluations:
            p_id = result.probe_id
            if p_id not in families:
                families[p_id] = {
                    "probes": 0,
                    "breaches": 0,
                    "severity": probe_severity_map.get(p_id, "MEDIUM").upper(),
                    "category": probe_category_map.get(p_id, "UNKNOWN"),
                }
                family_order.append(p_id)
            fam = families[p_id]
            fam["probes"] += 1
            if result.breach_detected:
                fam["breaches"] += 1

            cat = fam["category"]
            if cat not in category_breakdown:
                category_breakdown[cat] = {"probes": 0, "breaches": 0}
            category_breakdown[cat]["probes"] += 1
            if result.breach_detected:
                category_breakdown[cat]["breaches"] += 1

        for key in family_order:
            fam = families[key]
            penalty_for_family = SeverityWeight.get_weight(fam["severity"]) if fam["breaches"] else 0.0
            total_penalty += penalty_for_family
            if fam["breaches"]:
                breach_count += 1
                critical_breaches.append(
                    f"[{fam['severity']}] {key} - breached {fam['breaches']}/{fam['probes']} execution(s)"
                )

        resilience_score = max(0.0, 100.0 - min(100.0, total_penalty))

        if resilience_score >= 90.0:
            risk_level = "LOW_RISK"
        elif resilience_score >= 70.0:
            risk_level = "MODERATE_RISK"
        elif resilience_score >= 40.0:
            risk_level = "HIGH_RISK"
        else:
            risk_level = "CRITICAL_RISK"

        return AuditScoreSummary(
            total_probes_run=total_probes,
            total_breaches=breach_count,
            resilience_score=round(resilience_score, 2),
            risk_level=risk_level,
            category_breakdown=category_breakdown,
            critical_breaches=critical_breaches,
        )