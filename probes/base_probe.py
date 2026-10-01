"""
AstraCrew: Probe Abstraction & Dynamic Registry
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseProbe(ABC):
    """
    Abstract base class for all AstraCrew attack probes.
    Decouples payload synthesis logic from agent orchestration.

    `applicable_targets` declares which target types (see schemas.models.TargetType)
    a probe is meaningful against, so the orchestrator can route each probe only
    to the surfaces it actually tests.
    """

    def __init__(
        self,
        probe_id: str,
        name: str,
        owasp_category: str,
        severity: str,
        description: str,
        applicable_targets: list[str] | None,
    ):
        self.probe_id = probe_id
        self.name = name
        self.owasp_category = owasp_category
        self.severity = severity
        self.description = description
        self.applicable_targets = applicable_targets or ["MOCK"]

    @abstractmethod
    def build_payload(self, context: dict[str, Any]) -> str:
        """Synthesizes the adversarial payload using runtime context variables."""
        raise NotImplementedError

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "name": self.name,
            "owasp_category": self.owasp_category,
            "severity": self.severity,
            "description": self.description,
            "applicable_targets": self.applicable_targets,
        }


class ProbeRegistry:
    """Registry managing available probe classes for dynamic discovery."""

    _registry: dict[str, type[BaseProbe]] = {}

    @classmethod
    def register(cls, probe_cls: type[BaseProbe]) -> type[BaseProbe]:
        temp_instance = probe_cls()
        cls._registry[temp_instance.probe_id] = probe_cls
        return probe_cls

    @classmethod
    def get_probe(cls, probe_id: str) -> BaseProbe:
        if probe_id not in cls._registry:
            raise KeyError(f"Probe with ID '{probe_id}' is not registered.")
        return cls._registry[probe_id]()

    @classmethod
    def list_probes(cls) -> list[dict[str, Any]]:
        return [probe_cls().to_metadata_dict() for probe_cls in cls._registry.values()]

    @classmethod
    def probes_for_target(cls, target_type: str) -> list[BaseProbe]:
        """Returns instantiated probes whose applicable_targets includes target_type."""
        return [
            probe_cls()
            for probe_cls in cls._registry.values()
            if target_type in probe_cls().applicable_targets
        ]

    @classmethod
    def clear(cls) -> None:
        """Test helper: resets the registry between isolated test runs."""
        cls._registry.clear()