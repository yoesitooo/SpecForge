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
    for var in CLAVES + [k for k in os.environ if k.startswith("SDD_CHAIN_")]:
        monkeypatch.delenv(var, raising=False)
    from providers import router
    router._REGISTRY.clear()
    yield
    router._REGISTRY.clear()
