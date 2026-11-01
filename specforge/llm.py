"""
Llamadas al modelo por etapa
============================
Cada etapa del proceso (requisitos, diseño, tareas, implementación...) tiene
un nivel y una temperatura en core/config.py:AGENT_MODELS. Este módulo hace la
llamada con la cadena de proveedores de ese nivel (con respaldo automático) y,
cuando la etapa produce un artefacto estructurado, exige y valida JSON.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, TypeVar

from core.config import AGENT_MODELS, chain_for
from providers import router

T = TypeVar("T")

_BLOQUE_JSON = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class RespuestaInvalida(ValueError):
    """El modelo respondió algo que no cumple el formato pedido."""


async def preguntar(etapa: str, system: str, user: str, max_tokens: int = 8000) -> str:
    cfg = AGENT_MODELS[etapa]
    r = await router.call_chain(
        chain_for(cfg["tier"]),
        system=system,
        user=user,
        temperature=cfg["temperature"],
        max_tokens=max_tokens,
    )
    return r.content


def extraer_json(texto: str) -> Any:
    """Acepta JSON puro, dentro de ```json ...``` o rodeado de texto."""
    candidatos = [m.strip() for m in _BLOQUE_JSON.findall(texto)] + [texto.strip()]
    for c in candidatos:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            pass
    # Último recurso: el primer objeto o lista balanceado del texto
    for abre, cierra in (("{", "}"), ("[", "]")):
        inicio = texto.find(abre)
        fin = texto.rfind(cierra)
        if 0 <= inicio < fin:
            try:
                return json.loads(texto[inicio : fin + 1])
            except json.JSONDecodeError:
                continue
    raise RespuestaInvalida("La respuesta no contiene JSON válido.")


async def preguntar_json(
    etapa: str,
    system: str,
    user: str,
    validar: Callable[[Any], T],
    max_tokens: int = 8000,
    intentos: int = 2,
) -> T:
    """
    Pide JSON y lo valida con `validar` (que lanza ValueError si algo falta).
    Si falla, repite UNA vez diciéndole al modelo exactamente qué corregir.
    """
    error: Exception | None = None
    prompt = user
    for _ in range(intentos):
        texto = await preguntar(etapa, system, prompt, max_tokens)
        try:
            return validar(extraer_json(texto))
        except (ValueError, KeyError, TypeError) as e:
            error = e
            prompt = (
                f"{user}\n\n---\nTu respuesta anterior no cumplió el formato: {e}\n"
                "Responde de nuevo SOLO con el JSON corregido, sin texto adicional."
            )
    raise RespuestaInvalida(f"Etapa '{etapa}': el modelo no devolvió un formato válido ({error}).")
