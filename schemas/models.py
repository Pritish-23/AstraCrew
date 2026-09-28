"""
AstraCrew: Core Pydantic v2 Data Contracts

These schemas are the single source of truth shared across probes, targets,
evaluation gates, scoring, remediation, and reporting.
"""
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TargetType(str, Enum):
    """Identifies which application surface a probe was executed against."""

    MOCK = "MOCK"
    RAG = "RAG"
    AGENTIC = "AGENTIC"


class AttackSeverity(str, Enum):
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttackProbeExecution(BaseModel):
    """Execution trace of an individual adversarial probe against a target."""

    probe_id: str = Field(..., description="Unique probe ID (e.g., PRB-001)")
    probe_name: str
    owasp_category: str
    severity_level: Literal["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    target_type: Literal["MOCK", "RAG", "AGENTIC"] = "MOCK"
    injected_payload: str
    target_response: str


class GateEvaluationResult(BaseModel):
    """Evaluation verdict produced by the Dual-Gate harness."""

    probe_id: str
    breach_detected: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    gate_triggered: Literal["GATE_ONE_DETERMINISTIC", "GATE_TWO_SEMANTIC", "NONE"]
    detection_reason: str
    canary_leaked: bool = False


class RemediationRecommendation(BaseModel):
    """Hardening patch recommendation for flagged failure modes."""

    vulnerability_type: str
    observed_failure: str
    suggested_prompt_patch: str
    input_sanitization_regex: Optional[str] = None


class AuditConfiguration(BaseModel):
    """Validated configuration for a single audit run."""

    canary_token: str = "CANARY_ASTRA_8829F"
    target_types: List[TargetType] = Field(default_factory=lambda: [TargetType.MOCK])
    use_live_llm: bool = False
    model_name: str = "gpt-4o-mini"
    min_resilience: float = Field(70.0, ge=0.0, le=100.0)
    execution_mode: Literal["deterministic", "crew"] = "deterministic"


class AstraCrewAuditReport(BaseModel):
    """Consolidated audit deliverable compiling all findings and resilience metrics."""

    target_name: str
    timestamp: str
    execution_mode: Literal["deterministic", "crew"] = "deterministic"
    total_probes_run: int
    total_breaches: int
    resilience_score: float = Field(
        ..., ge=0.0, le=100.0, description="100=Invulnerable, 0=Critical Defeat"
    )
    breach_rate_pct: float
    category_breakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    detailed_findings: List[AttackProbeExecution]
    evaluations: List[GateEvaluationResult]
    remediations: List[RemediationRecommendation]
    executive_summary: str