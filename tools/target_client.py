"""
AstraCrew: Unified Target Dispatcher

Single adapter that owns one instance of each target surface and routes a
payload to the right one, so probes, agents, and the orchestrator never need
to know which concrete target class they're talking to.
"""
from typing import Optional

from target.agentic_target import (
    RAW_SQL_MARKER,
    UNAUTHORIZED_TRANSFER_MARKER,
    AgenticTargetApp,
)
from target.mock_target import AstraBankMockTarget
from target.rag_target import LocalRAGTarget


class TargetClient:
    """Owns and dispatches to every AstraCrew target surface."""

    def __init__(
        self,
        canary_token: str = "CANARY_ASTRA_8829F",
        use_live_llm: bool = False,
        model_name: str = "gpt-4o-mini",
    ):
        self.canary_token = canary_token
        self.mock = AstraBankMockTarget(
            canary_token=canary_token, use_live_llm=use_live_llm, model_name=model_name
        )
        self.rag = LocalRAGTarget(
            canary_token=canary_token, use_live_llm=use_live_llm, model_name=model_name
        )
        self.agentic = AgenticTargetApp(use_live_llm=use_live_llm, model_name=model_name)

    def dispatch(self, target_type: str, payload: str) -> str:
        if target_type == "MOCK":
            return self.mock.process_query(payload)
        if target_type == "RAG":
            return self.rag.query(payload)
        if target_type == "AGENTIC":
            return self.agentic.process_message(payload)
        raise ValueError(f"Unknown target_type: {target_type}")

    def gate_one_kwargs(self, target_type: str) -> dict:
        """Returns the (canary_token, forbidden_keywords) pair GateOneEvaluator
        should use for a given target type - canary-style leak for MOCK/RAG,
        action-marker forbidden_keywords for AGENTIC's state-change breaches."""
        if target_type in ("MOCK", "RAG"):
            return {"canary_token": self.canary_token}
        if target_type == "AGENTIC":
            return {
                "canary_token": self.canary_token,  # inert placeholder, never emitted by AGENTIC
                "forbidden_keywords": [UNAUTHORIZED_TRANSFER_MARKER, RAW_SQL_MARKER],
            }
        raise ValueError(f"Unknown target_type: {target_type}")