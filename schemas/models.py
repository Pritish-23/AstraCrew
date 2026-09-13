from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class AttackProbeExecution(BaseModel):
  """Execution trace of an individual adversarial probe."""

  probe_id: str = Field(..., description="Unique probe ID (e.g., PRB-001)")
  probe_name: str
  owasp_category: str
  severity_level: Literal["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
  injected_payload: str
  target_response: str


class GateEvaluationResult(BaseModel):
  """Evaluation verdict produced by the Dual-Gate harness."""

  probe_id: str
  breach_detected: bool
  confidence: float = Field(..., ge=0.0, le=1.0)
  gate_triggered: Literal[
      "GATE_ONE_DETERMINISTIC", "GATE_TWO_SEMANTIC", "NONE"
  ]
  detection_reason: str
  canary_leaked: bool = False


class RemediationRecommendation(BaseModel):
  """Hardening patch recommendation for flagged failure modes."""

  vulnerability_type: str
  observed_failure: str
  suggested_prompt_patch: str
  input_sanitization_regex: Optional[str] = None


class AstraCrewAuditReport(BaseModel):
  """Consolidated audit report compiling all findings and resilience metrics."""

  target_name: str
  timestamp: str
  total_probes_run: int
  total_breaches: int
  resilience_score: float = Field(
      ..., ge=0.0, le=100.0, description="100=Invulnerable, 0=Critical Defeat"
  )
  breach_rate_pct: float
  detailed_findings: List[AttackProbeExecution]
  evaluations: List[GateEvaluationResult]
  remediations: List[RemediationRecommendation]
  executive_summary: str