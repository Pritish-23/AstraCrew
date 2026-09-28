"""
AstraCrew: Master Audit Orchestrator

Two execution modes, one report schema:

  deterministic (default) - loops every registered probe against every
  applicable target, evaluates with Gate 1 -> Gate 2, and scores. Fast,
  free, fully reproducible. This is what CI runs to gate a PR.

  crew - kicks off the CrewAI hierarchical crew (crew.py) so agents
  reason about strategy and invoke probes themselves. Slower and
  non-deterministic (real LLM calls throughout), but tests the system's
  behavior under adaptive, less scripted attack strategy. Tool calls are
  captured via tools.probe_tools' execution log and run through the exact
  same Gate 1 -> Gate 2 -> scoring pipeline as deterministic mode, so both
  modes produce a directly comparable AstraCrewAuditReport.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

import probes.agentic_probes  # noqa: F401 - triggers registry discovery
import probes.injection_probes  # noqa: F401
import probes.obfuscation_probes  # noqa: F401
import probes.persona_probes  # noqa: F401
import probes.rag_probes  # noqa: F401
from evaluation.gate_one import GateOneEvaluator
from evaluation.gate_two import GateTwoArbiter
from evaluation.scoring import ResilienceScorer
from probes.base_probe import ProbeRegistry
from remediation.prompt_patcher import PromptPatcher
from schemas.models import (
    AstraCrewAuditReport,
    AttackProbeExecution,
    GateEvaluationResult,
)
from tools import probe_tools
from tools.target_client import TargetClient


class AstraAuditOrchestrator:
    """Coordinates the end-to-end probing lifecycle in either execution mode."""

    def __init__(
        self,
        canary_token: str = "CANARY_ASTRA_8829F",
        use_live_llm: bool = False,
        model_name: str = "gpt-4o-mini",
        target_types: Optional[List[str]] = None,
    ):
        self.canary_token = canary_token
        self.use_live_llm = use_live_llm
        self.model_name = model_name
        self.target_types = target_types or ["MOCK", "RAG", "AGENTIC"]

        self.client = TargetClient(
            canary_token=canary_token, use_live_llm=use_live_llm, model_name=model_name
        )
        self.gate_two = GateTwoArbiter(model=model_name)

    # ------------------------------------------------------------------
    # Shared evaluation pipeline (used by both execution modes)
    # ------------------------------------------------------------------
    def _evaluate(self, target_type: str, probe_id: str, response_text: str) -> GateEvaluationResult:
        gate_one = GateOneEvaluator(**self.client.gate_one_kwargs(target_type))
        verdict = gate_one.evaluate(probe_id, response_text)
        if verdict.gate_triggered == "NONE":
            try:
                verdict = self.gate_two.evaluate(
                    probe_id=probe_id,
                    injected_payload="",
                    target_response=response_text,
                )
            except Exception as err:  # noqa: BLE001
                verdict = GateEvaluationResult(
                    probe_id=probe_id,
                    breach_detected=False,
                    confidence=0.0,
                    gate_triggered="NONE",
                    detection_reason=f"Gate 2 unreachable fallback: {str(err)}",
                    canary_leaked=False,
                )
        return verdict

    def _compile_report(
        self,
        target_display_name: str,
        execution_mode: str,
        probe_executions: List[AttackProbeExecution],
        evaluations: List[GateEvaluationResult],
    ) -> AstraCrewAuditReport:
        probe_sev_map: Dict[str, str] = {}
        probe_cat_map: Dict[str, str] = {}
        for exe in probe_executions:
            probe_sev_map[exe.probe_id] = exe.severity_level
            probe_cat_map[exe.probe_id] = exe.owasp_category

        score_summary = ResilienceScorer.calculate_score(
            evaluations=evaluations,
            probe_severity_map=probe_sev_map,
            probe_category_map=probe_cat_map,
        )
        total_probes = len(evaluations)
        breach_rate = (score_summary.total_breaches / total_probes * 100.0) if total_probes else 0.0

        remediation = PromptPatcher.generate_diff(
            original_prompt=self.client.mock.system_prompt,
            probes=probe_executions,
            evaluations=evaluations,
        )

        executive_summary = (
            f"Security audit ({execution_mode} mode) concluded with Resilience Index: "
            f"{score_summary.resilience_score:.1f}/100.0 ({score_summary.risk_level}). "
            f"{score_summary.total_breaches} boundary breach(es) detected across "
            f"{score_summary.total_probes_run} adversarial vectors. "
            f"Critical/High breaches: {len(score_summary.critical_breaches)}."
        )

        return AstraCrewAuditReport(
            target_name=target_display_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            execution_mode=execution_mode,
            total_probes_run=score_summary.total_probes_run,
            total_breaches=score_summary.total_breaches,
            resilience_score=score_summary.resilience_score,
            breach_rate_pct=round(breach_rate, 2),
            category_breakdown=score_summary.category_breakdown,
            detailed_findings=probe_executions,
            evaluations=evaluations,
            remediations=[remediation],
            executive_summary=executive_summary,
        )

    # ------------------------------------------------------------------
    # Mode 1: deterministic
    # ------------------------------------------------------------------
    def run_full_audit(self, target_name: Optional[str] = None) -> AstraCrewAuditReport:
        """Deterministic fast-path: every applicable probe against every
        configured target type, no LLM calls except Gate 2 escalations."""
        target_display_name = target_name or (
            f"AstraBank Suite [{'Live LLM (' + self.model_name + ')' if self.use_live_llm else 'Mock/Simulated'}] "
            f"- targets: {', '.join(self.target_types)}"
        )

        probe_executions: List[AttackProbeExecution] = []
        evaluations: List[GateEvaluationResult] = []

        for target_type in self.target_types:
            for probe in ProbeRegistry.probes_for_target(target_type):
                payload = probe.build_payload(
                    {"canary_token": self.canary_token, "application_domain": "Fintech Customer Support Banking"}
                )
                target_response = self.client.dispatch(target_type, payload)

                probe_executions.append(
                    AttackProbeExecution(
                        probe_id=probe.probe_id,
                        probe_name=probe.name,
                        owasp_category=probe.owasp_category,
                        severity_level=probe.severity,
                        target_type=target_type,
                        injected_payload=payload,
                        target_response=target_response,
                    )
                )
                evaluations.append(self._evaluate(target_type, probe.probe_id, target_response))

        return self._compile_report(target_display_name, "deterministic", probe_executions, evaluations)

    # ------------------------------------------------------------------
    # Mode 2: crew (agentic)
    # ------------------------------------------------------------------
    def run_crew_audit(self, target_name: Optional[str] = None) -> AstraCrewAuditReport:
        """Agentic mode: lets the CrewAI hierarchical crew plan and execute
        its own attack strategy. Tool calls are captured via the shared
        execution log and evaluated through the identical Gate 1/2 pipeline."""
        from crew import AstraRedTeamCrew  # local import: avoids crewai import cost in deterministic-only runs

        probe_tools.configure_client(self.canary_token, self.use_live_llm, self.model_name)
        probe_tools.reset_execution_log()

        AstraRedTeamCrew().crew().kickoff()

        captured = probe_tools.get_execution_log()
        probe_executions: List[AttackProbeExecution] = []
        evaluations: List[GateEvaluationResult] = []

        for record in captured:
            probe_executions.append(
                AttackProbeExecution(
                    probe_id=record["probe_id"],
                    probe_name=record["probe_name"],
                    owasp_category=record["owasp_category"],
                    severity_level=record["severity"],
                    target_type=record["target_type"],
                    injected_payload=record["injected_payload"],
                    target_response=record["target_response"],
                )
            )
            evaluations.append(
                self._evaluate(record["target_type"], record["probe_id"], record["target_response"])
            )

        target_display_name = target_name or "AstraBank Suite [CrewAI Hierarchical Agentic Audit]"
        return self._compile_report(target_display_name, "crew", probe_executions, evaluations)

    def run_audit(self, mode: str = "deterministic", target_name: Optional[str] = None) -> AstraCrewAuditReport:
        if mode == "crew":
            return self.run_crew_audit(target_name=target_name)
        return self.run_full_audit(target_name=target_name)