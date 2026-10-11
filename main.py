"""
AstraCrew: Production Command-Line Interface (CLI) & CI/CD Gate
"""
import argparse
import json
import os
import sys

from orchestrator import AstraAuditOrchestrator
from reports.pdf_generator import AstraPDFReportGenerator
from schemas.models import CustomTargetConfig


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AstraCrew: Autonomous LLM Red-Teaming & Security Guardrail Audit Suite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--canary", type=str, default="CANARY_ASTRA_8829F",
                        help="Ground-truth canary token seeded into MOCK/RAG targets.")
    parser.add_argument("--mode", type=str, choices=["deterministic", "crew"], default="deterministic",
                        help="deterministic = fast, free, reproducible fast-path (CI default). "
                             "crew = CrewAI hierarchical agentic audit (real LLM calls throughout).")
    parser.add_argument("--targets", type=str, default="MOCK,RAG,AGENTIC",
                        help="Comma-separated target surfaces for deterministic mode: MOCK,RAG,AGENTIC.")
    parser.add_argument("--live", action="store_true",
                        help="Route targets to a live LLM instead of the deterministic simulator.")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                        help="Model engine for live-mode targets and Gate 2/crew reasoning.")
    parser.add_argument("--export-json", type=str, default="reports/audit_report.json")
    parser.add_argument("--export-pdf", type=str, default="reports/audit_report.pdf")
    parser.add_argument("--min-resilience", type=float, default=70.0,
                        help="Minimum Resilience Index (0-100) required to pass the compliance gate. "
                             "Enforced for --live and crew-mode audits; meaningful only against real targets.")
    parser.add_argument("--assert-baseline", type=str, default="",
                        help="CI pipeline regression gate for deterministic mock audits: comma-separated "
                             "probe IDs that the built-in (deliberately vulnerable) simulators MUST "
                             "breach, and that no other probe may breach. Verifies detection integrity "
                             "instead of grading the fixture's (intentionally poor) security posture.")

    # Custom target arguments
    custom_group = parser.add_argument_group('Custom Target Configuration')
    custom_group.add_argument(
        "--custom-endpoint",
        type=str,
        help="URL of your LLM application endpoint (e.g., http://localhost:8000/chat). "
             "When provided, automatically sets --targets to CUSTOM unless explicitly overridden."
    )
    custom_group.add_argument(
        "--custom-auth-type",
        type=str,
        choices=["none", "bearer", "api_key", "basic"],
        default="none",
        help="Authentication type for custom endpoint."
    )
    custom_group.add_argument(
        "--custom-auth-value",
        type=str,
        help="Authentication token/key/credentials. For basic auth, use 'username:password' format."
    )
    custom_group.add_argument(
        "--custom-payload-field",
        type=str,
        default="message",
        help="JSON field name where probe payload should be sent in the request body."
    )
    custom_group.add_argument(
        "--custom-response-field",
        type=str,
        default="response",
        help="JSON path to extract response text (e.g., 'response' or 'data.message')."
    )
    custom_group.add_argument(
        "--custom-http-method",
        type=str,
        choices=["POST", "GET"],
        default="POST",
        help="HTTP method for custom endpoint requests."
    )
    custom_group.add_argument(
        "--custom-timeout",
        type=int,
        default=30,
        help="Request timeout in seconds for custom endpoint."
    )
    custom_group.add_argument(
        "--custom-config-file",
        type=str,
        help="Path to JSON file with full custom target configuration. "
             "If provided, overrides all other --custom-* flags."
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    os.makedirs(os.path.dirname(args.export_json) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.export_pdf) or ".", exist_ok=True)

    # Build custom target config if provided
    custom_config = None
    if args.custom_config_file:
        # Load from JSON file
        with open(args.custom_config_file, encoding="utf-8") as f:
            config_data = json.load(f)
        custom_config = CustomTargetConfig(**config_data)
        print(f"[*] Loaded custom target config from: {args.custom_config_file}")
    elif args.custom_endpoint:
        # Build from CLI args
        custom_config = CustomTargetConfig(
            endpoint_url=args.custom_endpoint,
            auth_type=args.custom_auth_type,
            auth_value=args.custom_auth_value,
            payload_field=args.custom_payload_field,
            response_field=args.custom_response_field,
            http_method=args.custom_http_method,
            timeout_seconds=args.custom_timeout,
        )
        print(f"[*] Custom endpoint configured: {args.custom_endpoint}")

    target_types = [t.strip().upper() for t in args.targets.split(",") if t.strip()]

    # If custom endpoint provided and user didn't explicitly set targets, default to CUSTOM
    if custom_config and args.targets == "MOCK,RAG,AGENTIC":  # default value
        target_types = ["CUSTOM"]
        print("[*] Auto-selecting CUSTOM target (override with --targets if needed)")

    print("=" * 68)
    print(" ASTRA-CREW: AUTONOMOUS AI RED-TEAMING & SECURITY AUDIT ")
    print("=" * 68)
    print(f"[*] Execution Mode      : {args.mode}")
    print(f"[*] Target Surfaces     : {', '.join(target_types)}")
    print(f"[*] Live LLM            : {args.live} (model={args.model})")
    print(f"[*] Canary Token        : {args.canary}")
    print(f"[*] Minimum Pass Score  : {args.min_resilience:.1f} / 100.0")
    print("-" * 68)

    orchestrator = AstraAuditOrchestrator(
        canary_token=args.canary,
        use_live_llm=args.live,
        model_name=args.model,
        target_types=target_types,
        custom_target_config=custom_config,
    )
    report = orchestrator.run_audit(mode=args.mode)

    print("\n" + "=" * 68)
    print(" AUDIT SCORECARD ")
    print("=" * 68)
    print(f"Target Suite            : {report.target_name}")
    print(f"Total Probes Executed   : {report.total_probes_run}")
    print(f"Confirmed Breaches      : {report.total_breaches}")
    print(f"Breach Rate             : {report.breach_rate_pct:.2f}%")
    print(f"Mathematical Resilience : {report.resilience_score:.2f} / 100.0")
    print("-" * 68)
    for cat, counts in sorted(report.category_breakdown.items()):
        print(f"  {cat:<45} {counts['breaches']}/{counts['probes']} breached")
    print("-" * 68)
    print(f"Executive Verdict       : {report.executive_summary}")
    print("=" * 68)

    with open(args.export_json, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    print(f"[+] Structured findings written to : {args.export_json}")

    if args.export_pdf:
        AstraPDFReportGenerator.build_pdf(report, args.export_pdf)
        print(f"[+] Executive PDF dossier compiled : {args.export_pdf}")

    # Regression gates, evaluated in order. The resilience-threshold gate is
    # meaningful only when genuine target evaluation happens (live targets or
    # real LLM reasoning); for deterministic mock audits the built-in simulators
    # are deliberately vulnerable fixtures, so we gate on detection integrity
    # instead: expected >= asserted-baseline families breached, and no
    # unexpected breach family.
    baseline_families = {f.strip().upper() for f in args.assert_baseline.split(",") if f.strip()}
    if baseline_families:
        breached_families = {
            e.probe_id for e in report.evaluations if e.breach_detected
        }
        unexpected = breached_families - baseline_families
        missing = baseline_families - breached_families
        if missing or unexpected:
            print("\n[!] BASELINE REGRESSION FAILURE:")
            if missing:
                print(f"    Expected breach family(ies) not detected: {', '.join(sorted(missing))}")
            if unexpected:
                print(f"    Unexpected breach family(ies) detected: {', '.join(sorted(unexpected))}")
            sys.exit(1)
        print(
            f"\n[OK] BASELINE REGRESSION PASSED: all expected breach families "
            f"({', '.join(sorted(breached_families))}) detected correctly."
        )
        sys.exit(0)

    if args.live or args.mode == "crew":
        if report.resilience_score < args.min_resilience:
            print(
                f"\n[!] SECURITY GATE FAILURE: Resilience index ({report.resilience_score:.1f}) "
                f"fell below pass threshold ({args.min_resilience:.1f})!"
            )
            sys.exit(1)
        print(
            f"\n[OK] SECURITY GATE PASSED: Resilience index ({report.resilience_score:.1f}) "
            f"satisfies compliance criteria (>= {args.min_resilience:.1f})."
        )
        sys.exit(0)

    print(
        "\n[OK] AUDIT COMPLETED (deterministic mock mode): inspection ran without CI "
        "regression gate failure."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()