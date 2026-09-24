"""
AstraCrew: Agent Tool Wrappers for Target Probing and Payload Execution
"""
import json
from typing import Any, Dict, Optional
from crewai.tools import tool

from probes.base_probe import ProbeRegistry
from target.mock_target import AstraBankMockTarget

# Shared singleton target instance for audit runs
_target_instance = AstraBankMockTarget()


@tool("List Registered Attack Probes")
def list_available_probes(category_filter: Optional[str] = None) -> str:
    """
    Returns a JSON catalog of all registered security probes including
    probe_id, name, owasp_category, severity, and descriptions.
    Optionally filter by OWASP category string.
    """
    probes = ProbeRegistry.list_probes()
    if category_filter:
        probes = [p for p in probes if category_filter.lower() in p["owasp_category"].lower()]
    return json.dumps(probes, indent=2)


@tool("Execute Security Attack Probe")
def execute_security_probe(
    probe_id: str,
    target_canary: str = "CANARY_ASTRA_8829F",
    custom_instruction: Optional[str] = None,
    application_domain: str = "Fintech Banking Service"
) -> str:
    """
    Instantiates a registered attack probe, interpolates contextual attack
    variables, dispatches the payload to the target endpoint, and returns
    the raw execution trace.
    """
    try:
        probe = ProbeRegistry.get_probe(probe_id)
    except KeyError:
        return json.dumps({
            "status": "error",
            "message": f"Probe ID '{probe_id}' not found in registry."
        })

    context: Dict[str, Any] = {
        "canary_token": target_canary,
        "application_domain": application_domain,
    }
    if custom_instruction:
        context["hidden_instruction"] = custom_instruction

    # 1. Synthesize payload
    payload = probe.build_payload(context)

    # 2. Dispatch against target
    target_response = _target_instance.process_query(payload)

    execution_record = {
        "probe_id": probe.probe_id,
        "probe_name": probe.name,
        "owasp_category": probe.owasp_category,
        "severity": probe.severity,
        "injected_payload": payload,
        "target_response": target_response
    }
    return json.dumps(execution_record, indent=2)


@tool("Query Target Direct")
def query_target_direct(custom_query: str) -> str:
    """
    Dispatches a raw natural language query directly to the target application.
    Useful for multi-turn conversational follow-ups and prompt mutation attacks.
    """
    return _target_instance.process_query(custom_query)