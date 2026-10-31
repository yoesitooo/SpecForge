"""
Provider Router — Enruta llamadas al provider correcto.
El Orchestrator pide por nombre de provider ("claude", "groq", "nvidia").
El router instancia y cachea los providers disponibles.
"""

from .base import BaseProvider, LLMResponse
from .claude_provider import ClaudeProvider
from .groq_provider import GroqProvider
from .nvidia_provider import NvidiaProvider


_REGISTRY: dict[str, BaseProvider] = {}


def _get_provider(name: str) -> BaseProvider:
    if name not in _REGISTRY:
        match name:
            case "claude":
                _REGISTRY[name] = ClaudeProvider()
            case "groq":
                _REGISTRY[name] = GroqProvider()
            case "nvidia":
                _REGISTRY[name] = NvidiaProvider()
            case _:
                raise ValueError(f"Provider desconocido: '{name}'. Opciones: claude, groq, nvidia")
    return _REGISTRY[name]


async def call(
    provider_name: str,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    images: list[str] | None = None,
) -> LLMResponse:
    """
    Punto de entrada único para todas las llamadas LLM del sistema.
    Uso: await router.call("groq", "llama-3.3-70b-versatile", system, user)
    """
    provider = _get_provider(provider_name)
    return await provider.complete(
        system=system,
        user=user,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        images=images,
    )
