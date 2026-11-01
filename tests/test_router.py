import asyncio

import pytest

from providers import router
from providers.base import BaseProvider, LLMResponse
from providers.openai_compat import ProviderHTTPError


class Falso(BaseProvider):
    def __init__(self, nombre, disponible=True, error=None):
        self.name = nombre
        self._disponible = disponible
        self._error = error
        self.llamadas = []

    def is_available(self):
        return self._disponible

    async def complete(self, system, user, model, temperature=0.2, max_tokens=4096, images=None):
        self.llamadas.append(model)
        if self._error:
            raise self._error
        return LLMResponse(content=f"ok de {self.name}", model=model, provider=self.name)


def _registrar(*proveedores):
    for p in proveedores:
        router.register(p.name, p)
    return proveedores


def test_usa_el_primero_disponible():
    a, b = _registrar(Falso("a"), Falso("b"))
    r = asyncio.run(router.call_chain([("a", "m1"), ("b", "m2")], "s", "u"))
    assert r.provider == "a" and a.llamadas == ["m1"] and b.llamadas == []


def test_salta_proveedores_sin_credenciales():
    a, b = _registrar(Falso("a", disponible=False), Falso("b"))
    r = asyncio.run(router.call_chain([("a", "m1"), ("b", "m2")], "s", "u"))
    assert r.provider == "b" and a.llamadas == []


def test_cae_al_siguiente_si_hay_limite_429():
    a, b = _registrar(Falso("a", error=ProviderHTTPError("a", 429, "rate limit")), Falso("b"))
    r = asyncio.run(router.call_chain([("a", "m1"), ("b", "m2")], "s", "u"))
    assert r.provider == "b" and a.llamadas == ["m1"]


def test_sin_ningun_proveedor_explica_cada_motivo():
    _registrar(Falso("a", disponible=False), Falso("b", error=ProviderHTTPError("b", 503, "caído")))
    with pytest.raises(router.NoProviderAvailable) as e:
        asyncio.run(router.call_chain([("a", "x"), ("b", "y")], "s", "u"))
    mensaje = str(e.value)
    assert "a:x — sin credenciales" in mensaje and "503" in mensaje and "GEMINI_API_KEY" in mensaje


def test_errores_de_programacion_no_se_esconden():
    _registrar(Falso("a", error=KeyError("bug")), Falso("b"))
    with pytest.raises(KeyError):
        asyncio.run(router.call_chain([("a", "x"), ("b", "y")], "s", "u"))


def test_proveedor_desconocido():
    with pytest.raises(ValueError):
        router._get_provider("no-existe")


def test_conoce_todos_los_proveedores():
    assert {"gemini", "groq", "cerebras", "openrouter", "github", "nvidia",
            "claude", "antigravity"} <= set(router.PROVEEDORES)
