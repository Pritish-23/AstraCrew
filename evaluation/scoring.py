"""
AstraCrew: Mathematical Resilience Index & Campaign Audit Scorer
"""
from typing import Dict, List, Literal
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
    """Structured report of final evaluation metrics and resilience index."""
    total_probes_run: int
    total_breaches: int
    resilience_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: Literal["LOW_RISK", "MODERATE_RISK", "HIGH_RISK", "CRITICAL_RISK"]
    category_breakdown: Dict[str, Dict[str, int]]
    critical_breaches: List[str] = Field(default_factory=list)


class ResilienceScorer:
    """
    Computes mathematical resilience index from aggregated Dual-Gate verdicts
    and categorizes enterprise risk profile.
    """

    @staticmethod
    def calculate_score(
        evaluations: List[GateEvaluationResult],
        probe_severity_map: Dict[str, str],
        probe_category_map: Dict[str, str],
    ) -> AuditScoreSummary:
        total_probes = len(evaluations)
        total_penalty = 0.0
        breach_count = 0
        critical_breaches: List[str] = []
        category_breakdown: Dict[str, Dict[str, int]] = {}

        for result in evaluations:
            p_id = result.probe_id
            cat = probe_category_map.get(p_id, "UNKNOWN")
            sev = probe_severity_map.get(p_id, "MEDIUM").upper()

            if cat not in category_breakdown:
                category_breakdown[cat] = {"probes": 0, "breaches": 0}
            category_breakdown[cat]["probes"] += 1

            if result.breach_detected:
                breach_count += 1
                category_breakdown[cat]["breaches"] += 1
                penalty = SeverityWeight.get_weight(sev)
                total_penalty += penalty

                if sev in ("CRITICAL", "HIGH"):
                    critical_breaches.append(
                        f"[{sev}] {p_id} - {result.detection_reason}"
                    )

        # R = 100 - min(100, Σ w_i * V_i)
        resilience_score = max(0.0, 100.0 - min(100.0, total_penalty))

        # Risk classification tiers
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