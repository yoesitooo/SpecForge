"""
BaseProvider — Contrato abstracto para todos los proveedores LLM.
Cada provider implementa esta interfaz. El Orchestrator nunca sabe
qué API está llamando; solo habla con BaseProvider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        images: list[str] | None = None,   # base64 strings para vision
    ) -> LLMResponse:
        """Llamada principal al LLM. Devuelve siempre LLMResponse."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Retorna True si el provider tiene credenciales configuradas."""
        ...
