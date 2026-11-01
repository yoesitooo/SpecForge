"""Aísla las pruebas de las claves reales del .env del desarrollador."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CLAVES = [
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY",
    "OPENROUTER_API_KEY", "GITHUB_MODELS_TOKEN", "GITHUB_TOKEN",
    "NVIDIA_API_KEY", "NVIDIA_HEAVY_KEY", "NVIDIA_FAST_KEY",
]


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for var in CLAVES + ["SPECFORGE_MODO"] + [k for k in os.environ if k.startswith("SDD_CHAIN_")]:
        monkeypatch.delenv(var, raising=False)
    from providers import router
    router._REGISTRY.clear()
    yield
    router._REGISTRY.clear()


@pytest.fixture(autouse=True)
def memoria_temporal(tmp_path, monkeypatch):
    """Engram escribe en una base temporal durante las pruebas."""
    from memory import engram
    monkeypatch.setattr(engram, "DB_PATH", str(tmp_path / "engram.db"))


@pytest.fixture
def ia_guionada(monkeypatch):
    """
    Reemplaza a todos los proveedores por uno falso. `responder(etapa, user)`
    devuelve el texto para cada llamada; la etapa se reconoce por su prompt.
    """
    from providers import router
    from providers.base import BaseProvider, LLMResponse
    from specforge import prompts

    etapas = {getattr(prompts, n): n.lower() for n in dir(prompts) if n.isupper()}

    class Guionado(BaseProvider):
        name = "falso"

        def __init__(self):
            self.llamadas = []
            self.responder = None

        def is_available(self):
            return True

        async def complete(self, system, user, model, temperature=0.2, max_tokens=4096, images=None):
            etapa = etapas.get(system, "desconocida")
            self.llamadas.append((etapa, user))
            texto = await self.responder(etapa, user)
            return LLMResponse(content=texto, model=model, provider="falso")

    falso = Guionado()
    router.register("falso", falso)
    for nivel in ("DEEP", "CODE", "SMART", "FAST"):
        monkeypatch.setenv(f"SDD_CHAIN_{nivel}", "falso:m")
    return falso
