import asyncio
import json

import httpx
import pytest

from providers.openai_compat import PRESETS, OpenAICompatProvider, ProviderHTTPError


def _transporte(status=200, cuerpo=None, capturar=None):
    def handler(request: httpx.Request):
        if capturar is not None:
            capturar.append(request)
        return httpx.Response(status, json=cuerpo if cuerpo is not None else {})
    return httpx.MockTransport(handler)


RESPUESTA_OK = {
    "choices": [{"message": {"content": "hola"}}],
    "usage": {"prompt_tokens": 7, "completion_tokens": 2},
}


def test_todos_los_presets_usan_https():
    for nombre, preset in PRESETS.items():
        assert preset.base_url.startswith("https://"), nombre


def test_disponible_solo_con_clave(monkeypatch):
    p = OpenAICompatProvider("gemini")
    assert not p.is_available()
    monkeypatch.setenv("GOOGLE_API_KEY", "k")   # clave alternativa del preset
    assert p.is_available()


def test_envia_formato_openai_y_lee_respuesta(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "secreta")
    peticiones = []
    p = OpenAICompatProvider("groq", transport=_transporte(cuerpo=RESPUESTA_OK, capturar=peticiones))

    r = asyncio.run(p.complete("sis", "usr", model="llama-3.1-8b-instant", temperature=0.1))

    assert (r.content, r.provider, r.input_tokens, r.output_tokens) == ("hola", "groq", 7, 2)
    req = peticiones[0]
    assert str(req.url) == "https://api.groq.com/openai/v1/chat/completions"
    assert req.headers["Authorization"] == "Bearer secreta"
    cuerpo = json.loads(req.content)
    assert cuerpo["model"] == "llama-3.1-8b-instant"
    assert cuerpo["messages"] == [
        {"role": "system", "content": "sis"},
        {"role": "user", "content": "usr"},
    ]


def test_imagenes_solo_en_proveedores_con_vision(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    for nombre, multimodal in (("gemini", True), ("groq", False)):
        peticiones = []
        p = OpenAICompatProvider(nombre, transport=_transporte(cuerpo=RESPUESTA_OK, capturar=peticiones))
        asyncio.run(p.complete("s", "u", model="m", images=["AAAA"]))
        contenido = json.loads(peticiones[0].content)["messages"][1]["content"]
        assert isinstance(contenido, list) is multimodal


@pytest.mark.parametrize("status", [401, 404, 429, 500])
def test_errores_http_llevan_el_codigo(monkeypatch, status):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    p = OpenAICompatProvider("groq", transport=_transporte(status=status, cuerpo={"error": "x"}))
    with pytest.raises(ProviderHTTPError) as e:
        asyncio.run(p.complete("s", "u", model="m"))
    assert e.value.status == status


def test_respuesta_vacia_es_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    vacia = {"choices": [{"message": {"content": "  "}}]}
    p = OpenAICompatProvider("groq", transport=_transporte(cuerpo=vacia))
    with pytest.raises(ProviderHTTPError):
        asyncio.run(p.complete("s", "u", model="m"))


def test_sin_system_no_envia_mensaje_de_sistema_vacio(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    peticiones = []
    p = OpenAICompatProvider("gemini", transport=_transporte(cuerpo=RESPUESTA_OK, capturar=peticiones))
    asyncio.run(p.complete("", "solo usuario", model="m"))
    assert json.loads(peticiones[0].content)["messages"] == [{"role": "user", "content": "solo usuario"}]
