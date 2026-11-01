import asyncio

import pytest

from specforge import llm


@pytest.mark.parametrize("texto", [
    '{"a": 1}',
    'Claro:\n```json\n{"a": 1}\n```\nListo.',
    'Respuesta: {"a": 1} espero que sirva',
])
def test_extraer_json(texto):
    assert llm.extraer_json(texto) == {"a": 1}


def test_extraer_json_sin_json():
    with pytest.raises(llm.RespuestaInvalida):
        llm.extraer_json("no hay nada aquí")


def test_reintenta_una_vez_explicando_el_error(ia_guionada):
    respuestas = iter(["esto no es json", '{"preguntas": ["¿Quién la usa?"]}'])

    async def responder(etapa, user):
        return next(respuestas)

    ia_guionada.responder = responder
    r = asyncio.run(llm.preguntar_json("descubrimiento", "DESCUBRIMIENTO", "idea", lambda d: d["preguntas"]))
    assert r == ["¿Quién la usa?"]
    assert "no cumplió el formato" in ia_guionada.llamadas[1][1]


def test_falla_si_sigue_sin_formato(ia_guionada):
    async def responder(etapa, user):
        return "nada"

    ia_guionada.responder = responder
    with pytest.raises(llm.RespuestaInvalida, match="descubrimiento"):
        asyncio.run(llm.preguntar_json("descubrimiento", "x", "idea", lambda d: d))
