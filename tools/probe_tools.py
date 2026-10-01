"""
AstraCrew: Agent Tool Wrappers for Target Probing and Payload Execution
"""
import json
from typing import Any

from crewai.tools import tool

from probes.base_probe import ProbeRegistry
from tools.target_client import TargetClient

# Shared singleton dispatcher for a single audit run's agent tool calls.
_client = TargetClient()

# Execution log capturing every real probe dispatch made through this module,
# regardless of caller (deterministic orchestrator loop or a CrewAI agent's
# tool call). This is what lets crew-mode audits feed the exact same
# Gate 1 -> Gate 2 -> scoring pipeline as deterministic-mode audits: crew.py
# has no direct return value we can parse, so we capture at the dispatch
# layer instead.
_execution_log: list = []


def reset_execution_log() -> None:
    _execution_log.clear()


def get_execution_log() -> list:
    return list(_execution_log)


def configure_client(canary_token: str, use_live_llm: bool, model_name: str) -> None:
    """Rebuilds the shared TargetClient so crew-mode tool calls honor the
    same audit configuration (canary, live/mock, model) as deterministic
    mode instead of always using module-import defaults."""
    global _client
    _client = TargetClient(canary_token=canary_token, use_live_llm=use_live_llm, model_name=model_name)


@tool("List Registered Attack Probes")
def list_available_probes(category_filter: str | None = None, target_type: str | None = None) -> str:
    """
    Returns a JSON catalog of registered security probes including probe_id,
    name, owasp_category, severity, description, and applicable_targets.
    Optionally filter by OWASP category substring or by target_type
    (MOCK, RAG, or AGENTIC).
    """
    probes = ProbeRegistry.list_probes()
    if category_filter:
        probes = [p for p in probes if category_filter.lower() in p["owasp_category"].lower()]
    if target_type:
        probes = [p for p in probes if target_type in p["applicable_targets"]]
    return json.dumps(probes, indent=2)


@tool("Execute Security Attack Probe")
def execute_security_probe(
    probe_id: str,
    target_type: str = "MOCK",
    target_canary: str = "CANARY_ASTRA_8829F",
    custom_instruction: str | None = None,
    application_domain: str = "Fintech Banking Service",
) -> str:
    """
    Instantiates a registered attack probe, interpolates contextual attack
    variables, dispatches the payload to the chosen target surface
    (MOCK, RAG, or AGENTIC), and returns the raw execution trace.
    """
    try:
        probe = ProbeRegistry.get_probe(probe_id)
    except KeyError:
        return json.dumps({"status": "error", "message": f"Probe ID '{probe_id}' not found in registry."})

    if target_type not in probe.applicable_targets:
        return json.dumps(
            {
                "status": "error",
                "message": f"Probe '{probe_id}' is not applicable to target_type '{target_type}'.",
            }
        )

    context: dict[str, Any] = {"canary_token": target_canary, "application_domain": application_domain}
    if custom_instruction:
        context["hidden_instruction"] = custom_instruction

    payload = probe.build_payload(context)
    target_response = _client.dispatch(target_type, payload)

    execution_record = {
        "probe_id": probe.probe_id,
        "probe_name": probe.name,
        "owasp_category": probe.owasp_category,
        "severity": probe.severity,
        "target_type": target_type,
        "injected_payload": payload,
        "target_response": target_response,
    }
    _execution_log.append(execution_record)
    return json.dumps(execution_record, indent=2)


@tool("Query Target Direct")
def query_target_direct(custom_query: str, target_type: str = "MOCK") -> str:
    """
    Dispatches a raw natural language query directly to a target surface.
    Useful for multi-turn conversational follow-ups and prompt mutation attacks.
    """
    return _client.dispatch(target_type, custom_query)