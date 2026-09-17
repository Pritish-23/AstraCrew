from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type


class BaseProbe(ABC):
    """
    Abstract Base Class for all AstraCrew attack probes.
    Decouples vector mutation logic from agent orchestration.
    """

    def __init__(
        self,
        probe_id: str,
        name: str,
        owasp_category: str,
        severity: str,
        description: str,
    ):
        self.probe_id = probe_id
        self.name = name
        self.owasp_category = owasp_category
        self.severity = severity
        self.description = description

    @abstractmethod
    def build_payload(self, context: Dict[str, Any]) -> str:
        """
        Synthesizes the prompt injection or boundary-escape payload
        using provided target variables (e.g., target canary, application domain).
        """
        pass

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Returns metadata representation for reporting and agent context."""
        return {
            "probe_id": self.probe_id,
            "name": self.name,
            "owasp_category": self.owasp_category,
            "severity": self.severity,
            "description": self.description,
        }


class ProbeRegistry:
    """Registry managing available probe classes for dynamic discovery."""

    _registry: Dict[str, Type[BaseProbe]] = {}

    @classmethod
    def register(cls, probe_cls: Type[BaseProbe]) -> Type[BaseProbe]:
        """Class decorator or direct method to register a probe implementation."""
        temp_instance = probe_cls()
        cls._registry[temp_instance.probe_id] = probe_cls
        return probe_cls

    @classmethod
    def get_probe(cls, probe_id: str) -> BaseProbe:
        """Retrieves an instantiated probe by its unique ID."""
        if probe_id not in cls._registry:
            raise KeyError(f"Probe with ID '{probe_id}' is not registered.")
        return cls._registry[probe_id]()

    @classmethod
    def list_probes(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all currently registered probes."""
        return [probe_cls().to_metadata_dict() for probe_cls in cls._registry.values()]