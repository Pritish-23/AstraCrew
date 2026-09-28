"""
AstraCrew: Interactive Streamlit Security Audit Dashboard
"""
import os

import streamlit as st

from orchestrator import AstraAuditOrchestrator
from remediation.middleware_generator import MiddlewareGenerator
from reports.pdf_generator import AstraPDFReportGenerator

st.set_page_config(page_title="AstraCrew Red-Team Audit", page_icon=":shield:", layout="wide")

st.title("AstraCrew: Autonomous AI Red-Teaming Suite")
st.caption("OWASP LLM Top 10 Guardrail Vulnerability Assessment & Automated Remediation")

st.sidebar.header("Audit Configuration")
exec_mode = st.sidebar.radio(
    "Execution Mode",
    ["Deterministic (fast, free, reproducible)", "CrewAI Agentic (LLM-driven strategy)"],
    index=0,
)
mode = "crew" if "CrewAI" in exec_mode else "deterministic"

target_options = st.sidebar.multiselect(
    "Target Surfaces (deterministic mode only)",
    ["MOCK", "RAG", "AGENTIC"],
    default=["MOCK", "RAG", "AGENTIC"],
)

canary_token = st.sidebar.text_input("Ground-Truth Canary Token", value="CANARY_ASTRA_8829F")
min_resilience_gate = st.sidebar.slider("Compliance Gate Threshold", 0, 100, 70)

use_live = st.sidebar.checkbox("Use live OpenAI model instead of deterministic simulator")
model_choice = "gpt-4o-mini"
if use_live or mode == "crew":
    model_choice = st.sidebar.selectbox("OpenAI Model Engine", ["gpt-4o-mini", "gpt-4o"], index=0)
    api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")
    if api_key_input:
        os.environ["OPENAI_API_KEY"] = api_key_input

start_audit_btn = st.sidebar.button("Run Red-Team Campaign", type="primary", use_container_width=True)

if "audit_report" not in st.session_state:
    st.session_state.audit_report = None

if start_audit_btn:
    with st.spinner("Dispatching attack probes and evaluating responses..."):
        orchestrator = AstraAuditOrchestrator(
            canary_token=canary_token,
            use_live_llm=use_live,
            model_name=model_choice,
            target_types=target_options or ["MOCK"],
        )
        report = orchestrator.run_audit(mode=mode)
        st.session_state.audit_report = report

report = st.session_state.audit_report
if report:
    os.makedirs("reports", exist_ok=True)
    pdf_path = "reports/audit_report.pdf"
    AstraPDFReportGenerator.build_pdf(report, pdf_path)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Resilience Score", f"{report.resilience_score:.1f} / 100.0")
    col2.metric("Breach Rate", f"{report.breach_rate_pct:.1f}%")
    col3.metric("Probes Executed", report.total_probes_run)
    col4.metric("Breaches Detected", report.total_breaches)

    if report.resilience_score >= min_resilience_gate:
        st.success(f"Audit Status: PASSED (Resilience {report.resilience_score:.1f} >= {min_resilience_gate})")
    else:
        st.error(f"Audit Status: FAILED (Resilience {report.resilience_score:.1f} < {min_resilience_gate})")

    st.markdown("---")

    tab_findings, tab_coverage, tab_diff, tab_middleware, tab_export = st.tabs(
        ["Probe Traces", "OWASP Coverage", "Prompt Remediation Diff", "Defensive Middleware", "Export Reports"]
    )

    with tab_findings:
        st.subheader(f"Executed Adversarial Vectors ({report.execution_mode} mode)")
        eval_lookup = {e.probe_id: e for e in report.evaluations}
        for p in report.detailed_findings:
            e = eval_lookup.get(p.probe_id)
            is_breached = e.breach_detected if e else False
            status_icon = "BREACH" if is_breached else "DEFENDED"
            with st.expander(f"[{status_icon}] [{p.probe_id} / {p.target_type}] {p.probe_name} ({p.severity_level})"):
                st.markdown(f"**OWASP Category:** `{p.owasp_category}`")
                st.markdown(f"**Gate Triggered:** `{e.gate_triggered if e else 'N/A'}`")
                st.markdown(f"**Detection Reason:** {e.detection_reason if e else 'N/A'}")
                st.markdown("**Injected Payload:**")
                st.code(p.injected_payload, language="markdown")
                st.markdown("**Target Output:**")
                st.code(p.target_response, language="markdown")

    with tab_coverage:
        st.subheader("OWASP LLM Top 10 Category Coverage")
        for cat, counts in sorted(report.category_breakdown.items()):
            st.write(f"**{cat}** - {counts['breaches']} / {counts['probes']} breached")
            st.progress(counts["breaches"] / counts["probes"] if counts["probes"] else 0)

    with tab_diff:
        st.subheader("Unified System Prompt Hardening Diff")
        for r in report.remediations:
            st.code(r.suggested_prompt_patch, language="diff")

    with tab_middleware:
        st.subheader("Drop-in FastAPI Pre-Execution Firewall")
        failed_probes = [
            p for p in report.detailed_findings
            if any(e.probe_id == p.probe_id and e.breach_detected for e in report.evaluations)
        ]
        st.code(MiddlewareGenerator.generate_fastapi_middleware(failed_probes), language="python")

    with tab_export:
        st.subheader("Download Campaign Deliverables")
        col_pdf, col_json = st.columns(2)
        with open(pdf_path, "rb") as f:
            col_pdf.download_button("Download Executive PDF Dossier", data=f,
                                     file_name="AstraCrew_Security_Audit.pdf", mime="application/pdf",
                                     use_container_width=True)
        col_json.download_button("Download Raw JSON Findings", data=report.model_dump_json(indent=2),
                                  file_name="AstraCrew_Audit_Findings.json", mime="application/json",
                                  use_container_width=True)
else:
    st.info("Configure your audit in the sidebar and click **Run Red-Team Campaign** to begin.")