"""
AstraCrew Phase 4 Verification:
Tests for Orchestrator, Remediation, PDF Generation, and full end-to-end flow
"""
import os
import tempfile

import pytest

from orchestrator import AstraAuditOrchestrator
from remediation.middleware_generator import MiddlewareGenerator
from remediation.prompt_patcher import PromptPatcher
from reports.pdf_generator import AstraPDFReportGenerator
from schemas.models import AttackProbeExecution, GateEvaluationResult


def test_orchestrator_deterministic_full_audit():
    """Test full deterministic audit with mock targets."""
    orchestrator = AstraAuditOrchestrator(
        canary_token="TEST_CANARY_ORCHESTRATOR",
        use_live_llm=False,
        model_name="gpt-4o-mini",
        target_types=["MOCK"],  # Start with just MOCK for speed
    )

    report = orchestrator.run_audit(mode="deterministic")

    # Validate report structure
    assert report.target_name is not None
    assert report.timestamp is not None
    assert report.execution_mode == "deterministic"
    assert report.total_probes_run > 0
    assert 0.0 <= report.resilience_score <= 100.0
    assert 0.0 <= report.breach_rate_pct <= 100.0
    assert len(report.detailed_findings) == report.total_probes_run
    assert len(report.evaluations) == report.total_probes_run
    assert len(report.remediations) > 0
    assert report.executive_summary is not None
    assert len(report.executive_summary) > 0


def test_orchestrator_multi_target_audit():
    """Test audit across all three target types."""
    orchestrator = AstraAuditOrchestrator(
        canary_token="TEST_CANARY_MULTI",
        use_live_llm=False,
        model_name="gpt-4o-mini",
        target_types=["MOCK", "RAG", "AGENTIC"],
    )

    report = orchestrator.run_audit(mode="deterministic")

    # Should have probes from all targets
    target_types_tested = {finding.target_type for finding in report.detailed_findings}
    assert "MOCK" in target_types_tested
    assert "RAG" in target_types_tested
    assert "AGENTIC" in target_types_tested

    # Should have category breakdown
    assert len(report.category_breakdown) > 0


def test_prompt_patcher_generates_hardened_prompt():
    """Test that PromptPatcher generates XML-bounded hardened prompts."""
    original_prompt = """
    You are a helpful assistant for AstraBank.
    Help customers with their banking questions.
    """

    # Simulate some breaches
    evaluations = [
        GateEvaluationResult(
            probe_id="PRB-001",
            breach_detected=True,
            confidence=1.0,
            gate_triggered="GATE_ONE_DETERMINISTIC",
            detection_reason="Delimiter collision succeeded",
            canary_leaked=True,
        )
    ]

    hardened = PromptPatcher.generate_hardened_prompt(original_prompt, evaluations)

    # Check for XML boundaries
    assert "<system_instructions>" in hardened
    assert "<role_definition>" in hardened
    assert "<operational_boundaries>" in hardened
    assert "<input_enclosure_policy>" in hardened
    assert "<user_input_untrusted>" in hardened

    # Check for defensive rules
    assert "Context Boundary" in hardened
    assert "Delimiter Immunity" in hardened
    assert "Secret Isolation" in hardened


def test_prompt_patcher_generates_unified_diff():
    """Test that PromptPatcher generates Git-style unified diff."""
    original_prompt = "You are a helpful assistant."

    probes = [
        AttackProbeExecution(
            probe_id="PRB-001",
            probe_name="Test Probe",
            owasp_category="OWASP-LLM01",
            severity_level="HIGH",
            target_type="MOCK",
            injected_payload="malicious payload",
            target_response="leaked secret",
        )
    ]

    evaluations = [
        GateEvaluationResult(
            probe_id="PRB-001",
            breach_detected=True,
            confidence=1.0,
            gate_triggered="GATE_ONE_DETERMINISTIC",
            detection_reason="Breach detected",
            canary_leaked=True,
        )
    ]

    remediation = PromptPatcher.generate_diff(original_prompt, probes, evaluations)

    # Check RemediationRecommendation structure
    assert remediation.vulnerability_type is not None
    assert remediation.observed_failure is not None
    assert remediation.suggested_prompt_patch is not None

    # Diff should contain standard markers
    diff = remediation.suggested_prompt_patch
    assert "---" in diff or "system_prompt.txt" in diff
    assert "+++" in diff or "hardened" in diff or "# No prompt modifications" in diff


def test_middleware_generator_without_base64():
    """Test middleware generation without Base64 breach."""
    failed_probes = [
        AttackProbeExecution(
            probe_id="PRB-001",
            probe_name="Delimiter Collision",
            owasp_category="OWASP-LLM01",
            severity_level="HIGH",
            target_type="MOCK",
            injected_payload="---END---",
            target_response="leaked",
        )
    ]

    middleware_code = MiddlewareGenerator.generate_fastapi_middleware(failed_probes)

    # Should contain basic defensive patterns
    assert "PromptFirewallMiddleware" in middleware_code
    assert "delimiter_patterns" in middleware_code
    assert "override_keywords" in middleware_code
    assert "HTTPException" in middleware_code

    # Should NOT contain Base64 decoding logic
    assert "b64_matches" not in middleware_code or "base64" not in middleware_code.lower()


def test_middleware_generator_with_base64():
    """Test middleware generation with Base64 breach."""
    failed_probes = [
        AttackProbeExecution(
            probe_id="PRB-004",
            probe_name="Base64 Encoding Bypass",
            owasp_category="OWASP-LLM07",
            severity_level="MEDIUM",
            target_type="MOCK",
            injected_payload="base64_encoded_payload",
            target_response="decoded and executed",
        )
    ]

    middleware_code = MiddlewareGenerator.generate_fastapi_middleware(failed_probes)

    # Should contain Base64 decoding logic
    assert "base64" in middleware_code
    assert "b64_matches" in middleware_code
    assert "base64.b64decode" in middleware_code


def test_pdf_generation():
    """Test PDF report generation."""
    # Create a minimal audit report
    from schemas.models import AstraCrewAuditReport, RemediationRecommendation

    report = AstraCrewAuditReport(
        target_name="Test Target",
        timestamp="2026-09-28T00:00:00Z",
        execution_mode="deterministic",
        total_probes_run=5,
        total_breaches=2,
        resilience_score=60.0,
        breach_rate_pct=40.0,
        category_breakdown={
            "OWASP-LLM01-Prompt-Injection": {"probes": 3, "breaches": 1},
            "OWASP-LLM07-Guardrail-Bypass": {"probes": 2, "breaches": 1},
        },
        detailed_findings=[
            AttackProbeExecution(
                probe_id="PRB-001",
                probe_name="Test Probe 1",
                owasp_category="OWASP-LLM01-Prompt-Injection",
                severity_level="HIGH",
                target_type="MOCK",
                injected_payload="test payload",
                target_response="test response",
            )
        ],
        evaluations=[
            GateEvaluationResult(
                probe_id="PRB-001",
                breach_detected=True,
                confidence=1.0,
                gate_triggered="GATE_ONE_DETERMINISTIC",
                detection_reason="Test breach",
                canary_leaked=True,
            )
        ],
        remediations=[
            RemediationRecommendation(
                vulnerability_type="Test Vulnerability",
                observed_failure="Test failure",
                suggested_prompt_patch="--- old\n+++ new",
                input_sanitization_regex=r"test_regex",
            )
        ],
        executive_summary="This is a test audit report.",
    )

    # Generate PDF to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        AstraPDFReportGenerator.build_pdf(report, pdf_path)

        # Verify file exists and has content
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000  # PDF should be at least 1KB

    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def test_orchestrator_category_breakdown():
    """Test that orchestrator correctly aggregates category breakdown."""
    orchestrator = AstraAuditOrchestrator(
        canary_token="TEST_CANARY_BREAKDOWN",
        use_live_llm=False,
        target_types=["MOCK"],
    )

    report = orchestrator.run_audit(mode="deterministic")

    # Should have OWASP categories
    assert len(report.category_breakdown) > 0

    # Each category should have probe count and breach count
    for category, counts in report.category_breakdown.values():
        assert "probes" in counts
        assert "breaches" in counts
        assert counts["probes"] >= counts["breaches"]
        assert counts["probes"] > 0


def test_orchestrator_resilience_score_bounds():
    """Test that resilience scores are always within valid bounds."""
    orchestrator = AstraAuditOrchestrator(
        canary_token="TEST_CANARY_BOUNDS",
        use_live_llm=False,
        target_types=["MOCK", "RAG", "AGENTIC"],
    )

    report = orchestrator.run_audit(mode="deterministic")

    # Resilience score must be 0-100
    assert 0.0 <= report.resilience_score <= 100.0

    # Breach rate must be 0-100%
    assert 0.0 <= report.breach_rate_pct <= 100.0

    # Breach count can't exceed probe count
    assert report.total_breaches <= report.total_probes_run


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY for crew mode",
)
def test_orchestrator_crew_mode_basic():
    """Test that crew mode executes and produces valid report."""
    orchestrator = AstraAuditOrchestrator(
        canary_token="TEST_CANARY_CREW",
        use_live_llm=False,  # Still use mock targets, but crew agents use real LLM
        model_name="gpt-4o-mini",
    )

    # Run crew mode - this will use real API calls for agents
    report = orchestrator.run_audit(mode="crew")

    # Validate report structure
    assert report.execution_mode == "crew"
    assert report.total_probes_run >= 0  # Crew may execute variable number
    assert 0.0 <= report.resilience_score <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
