"""
OpenAI-compatible Provider — un solo cliente para todos los proveedores gratis
==============================================================================
Groq, Google Gemini (AI Studio), Cerebras, OpenRouter, GitHub Models y
NVIDIA NIM exponen la misma API `/chat/completions` de OpenAI. En lugar de un
archivo por proveedor, este módulo define un PRESET por proveedor (URL base +
variable de entorno de la clave) y una sola implementación.

Agregar un proveedor nuevo = agregar una línea a PRESETS.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from .base import BaseProvider, LLMResponse


@dataclass(frozen=True)
class Preset:
    base_url: str
    key_envs: tuple[str, ...]          # se usa la primera variable que exista
    supports_images: bool = False
    extra_headers: tuple[tuple[str, str], ...] = ()


PRESETS: dict[str, Preset] = {
    # Google AI Studio — clave gratis en https://aistudio.google.com/apikey
    "gemini": Preset(
        "https://generativelanguage.googleapis.com/v1beta/openai",
        ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        supports_images=True,
    ),
    # Groq — https://console.groq.com/keys (muy rápido, cuota diaria por modelo)
    "groq": Preset("https://api.groq.com/openai/v1", ("GROQ_API_KEY",)),
    # Cerebras — https://cloud.cerebras.ai (alto volumen; contexto limitado en el plan gratis)
    "cerebras": Preset("https://api.cerebras.ai/v1", ("CEREBRAS_API_KEY",)),
    # OpenRouter — https://openrouter.ai/keys (modelos con sufijo :free)
    "openrouter": Preset(
        "https://openrouter.ai/api/v1",
        ("OPENROUTER_API_KEY",),
        extra_headers=(("X-Title", "SDD Ecosystem"),),
    ),
    # GitHub Models — token de GitHub con permiso "models:read"
    "github": Preset("https://models.github.ai/inference", ("GITHUB_MODELS_TOKEN", "GITHUB_TOKEN")),
    # NVIDIA NIM — https://build.nvidia.com (créditos gratis)
    "nvidia": Preset(
        "https://integrate.api.nvidia.com/v1",
        ("NVIDIA_API_KEY", "NVIDIA_HEAVY_KEY", "NVIDIA_FAST_KEY"),
        supports_images=True,
    ),
}


class ProviderHTTPError(RuntimeError):
    """Error HTTP de un proveedor; `status` permite al router decidir si reintenta con otro."""

    def __init__(self, provider: str, status: int, detail: str):
        super().__init__(f"{provider} respondió {status}: {detail[:300]}")
        self.provider = provider
        self.status = status


class OpenAICompatProvider(BaseProvider):
    def __init__(self, name: str, transport: httpx.AsyncBaseTransport | None = None):
        if name not in PRESETS:
            raise ValueError(f"Proveedor OpenAI-compatible desconocido: '{name}'")
        self.name = name
        self._preset = PRESETS[name]
        self._transport = transport  # inyectable en pruebas

    def _api_key(self) -> str:
        for var in self._preset.key_envs:
            value = os.environ.get(var, "").strip()
            if value:
                return value
        return ""

    def is_available(self) -> bool:
        return bool(self._api_key())

    async def complete(
        self,
        system: str,
        user: str,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        images: list[str] | None = None,
    ) -> LLMResponse:
        if images and self._preset.supports_images:
            user_content: str | list = [
                *[
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                    for img in images
                ],
                {"type": "text", "text": user},
            ]
        else:
            user_content = user

        payload = {
            "model": model,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
            **dict(self._preset.extra_headers),
        }

        async with httpx.AsyncClient(timeout=180, transport=self._transport) as client:
            response = await client.post(
                f"{self._preset.base_url}/chat/completions", headers=headers, json=payload
            )
        if response.status_code >= 400:
            raise ProviderHTTPError(self.name, response.status_code, response.text)

        data = response.json()
        choices = data.get("choices") or []
        content = (choices[0].get("message", {}).get("content") if choices else None) or ""
        if not content.strip():
            raise ProviderHTTPError(self.name, 502, "respuesta vacía")

        usage = data.get("usage") or {}
        return LLMResponse(
            content=content,
            model=model,
            provider=self.name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
