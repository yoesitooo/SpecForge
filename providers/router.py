"""
Provider Router — elige proveedor y cae al siguiente si uno falla
==================================================================
Los agentes no saben qué API usan: piden un nivel ("smart", "code", "fast",
"vision") y el router recorre la cadena configurada en core/config.py:

  1. Salta los proveedores sin credenciales (o sin el CLI instalado).
  2. Llama al primero disponible.
  3. Si falla (429 por límite gratis, 5xx, modelo retirado, CLI caído...),
     registra el motivo y prueba el siguiente.

Así el sistema funciona con lo que tengas: solo una clave gratis de Gemini,
solo Groq, una suscripción, o todo a la vez.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from .base import BaseProvider, LLMResponse
from .cli_providers import AntigravityCLIProvider, ClaudeCLIProvider, CLIProviderError
from .openai_compat import PRESETS, OpenAICompatProvider, ProviderHTTPError

log = logging.getLogger(__name__)

_REGISTRY: dict[str, BaseProvider] = {}

PROVEEDORES = sorted([*PRESETS, "claude", "antigravity"])


class NoProviderAvailable(RuntimeError):
    """Ningún proveedor de la cadena pudo responder."""


def _get_provider(name: str) -> BaseProvider:
    if name not in _REGISTRY:
        if name in PRESETS:
            _REGISTRY[name] = OpenAICompatProvider(name)
        elif name == "claude":
            _REGISTRY[name] = ClaudeCLIProvider()
        elif name == "antigravity":
            _REGISTRY[name] = AntigravityCLIProvider()
        else:
            raise ValueError(f"Proveedor desconocido: '{name}'. Opciones: {', '.join(PROVEEDORES)}")
    return _REGISTRY[name]


def register(name: str, provider: BaseProvider) -> None:
    """Registra (o reemplaza) un proveedor. Útil en pruebas."""
    _REGISTRY[name] = provider


_ERRORES_RECUPERABLES = (
    ProviderHTTPError,
    CLIProviderError,
    httpx.HTTPError,
    asyncio.TimeoutError,
)


async def call_chain(
    chain: list[tuple[str, str]],
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    images: list[str] | None = None,
) -> LLMResponse:
    """Recorre la cadena y devuelve la primera respuesta exitosa."""
    motivos: list[str] = []
    for provider_name, model in chain:
        provider = _get_provider(provider_name)
        etiqueta = f"{provider_name}:{model or 'default'}"
        if not provider.is_available():
            motivos.append(f"{etiqueta} — sin credenciales / CLI no instalado")
            continue
        try:
            response = await provider.complete(
                system=system,
                user=user,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                images=images,
            )
        except _ERRORES_RECUPERABLES as e:
            log.warning("Proveedor %s falló, probando el siguiente: %s", etiqueta, e)
            motivos.append(f"{etiqueta} — {e}")
            continue
        if motivos:
            log.info("Respondió %s tras %d intento(s) fallido(s).", etiqueta, len(motivos))
        return response

    raise NoProviderAvailable(
        "Ningún proveedor pudo responder. Configura al menos una clave gratis "
        "(por ejemplo GEMINI_API_KEY) en .env.\n  " + "\n  ".join(motivos)
    )


async def call(
    provider_name: str,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    images: list[str] | None = None,
) -> LLMResponse:
    """Llamada directa a un proveedor concreto (sin respaldo)."""
    return await call_chain(
        [(provider_name, model)], system, user, temperature, max_tokens, images
    )
