"""
Proveedores por CLI — usan una SUSCRIPCIÓN en vez de pagar por tokens
=====================================================================
- `claude`: Claude Code CLI (`claude --print`), con un plan Claude Pro/Max.
  Requiere: `claude` instalado y haber iniciado sesión una vez.
- `antigravity`: Antigravity CLI de Google (`agy -p`). Desde junio de 2026
  reemplaza a Gemini CLI para cuentas personales: con una cuenta de Google
  gratis o Google AI Pro/Ultra (límites más altos) da acceso a los modelos
  Gemini. Requiere: `agy` instalado y haber iniciado sesión una vez con `agy`.

Ambos se ejecutan sin shell (`create_subprocess_exec`): nada del prompt se
interpreta como comando. Claude recibe el prompt por stdin; `agy -p` lo recibe
como argumento (su modo stdin exige el protocolo stream-json), así que los
prompts muy largos se rechazan y el router pasa al siguiente proveedor.
En modo headless, `agy` deniega las herramientas que pedirían permiso
(no edita archivos ni ejecuta comandos): solo responde texto.

Nota: las suscripciones son para uso personal. Para un servicio con
usuarios, usa los proveedores con API key (openai_compat.py).
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil

from .base import BaseProvider, LLMResponse

_ANSI = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


class CLIProviderError(RuntimeError):
    pass


async def _run(cmd: list[str], stdin_text: str | None, timeout: float) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE if stdin_text is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    datos = stdin_text.encode("utf-8") if stdin_text is not None else None
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(datos), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise CLIProviderError(f"{cmd[0]} no respondió en {timeout:.0f} s")
    out = _ANSI.sub("", stdout.decode("utf-8", errors="replace")).strip()
    if proc.returncode != 0 or not out:
        err = _ANSI.sub("", stderr.decode("utf-8", errors="replace")).strip() or out
        pista = f" ¿Iniciaste sesión? Abre `{cmd[0]}` una vez en la terminal." if proc.returncode else ""
        raise CLIProviderError(
            f"{cmd[0]} falló (código {proc.returncode}): {err[:300] or 'sin mensaje'}.{pista}"
        )
    return out


def extraer_texto_json(salida: str) -> str:
    """
    Extrae la respuesta del JSON de `agy --output-format json`
    (sobre: `status`, `response`, `error`, `usage`, ...).
    Si la salida no es JSON, la devuelve tal cual.
    """
    try:
        data = json.loads(salida)
    except json.JSONDecodeError:
        return salida
    if not isinstance(data, dict):
        return salida
    status = data.get("status")
    if status and status != "SUCCESS":
        raise CLIProviderError(f"agy terminó con estado {status}: {str(data.get('error'))[:300]}")
    respuesta = data.get("response")
    if isinstance(respuesta, str) and respuesta.strip():
        return respuesta
    raise CLIProviderError("agy no devolvió respuesta")


# Margen bajo el límite de un argumento en Linux (128 KiB) y de la línea de comandos en Windows.
MAX_PROMPT_ARG = 30_000


def _unir(system: str, user: str) -> str:
    return f"{system}\n\n---\n\n{user}" if system else user


class ClaudeCLIProvider(BaseProvider):
    name = "claude"

    def is_available(self) -> bool:
        return shutil.which("claude") is not None

    async def complete(self, system, user, model, temperature=0.2, max_tokens=8000, images=None):
        cmd = ["claude", "--print", "--output-format", "text"]
        if model:
            cmd += ["--model", model]
        content = await _run(cmd, _unir(system, user), timeout=600)
        return LLMResponse(content=content, model=model, provider=self.name)


class AntigravityCLIProvider(BaseProvider):
    name = "antigravity"

    def is_available(self) -> bool:
        return shutil.which("agy") is not None

    async def complete(self, system, user, model, temperature=0.2, max_tokens=8000, images=None):
        prompt = _unir(system, user)
        if len(prompt) > MAX_PROMPT_ARG:
            raise CLIProviderError(
                f"prompt de {len(prompt)} caracteres: demasiado largo para `agy -p`"
            )
        cmd = ["agy", "--output-format", "json", "--disable-slash-commands"]
        if model:
            cmd += ["--model", model]
        cmd += ["--print", prompt]
        salida = await _run(cmd, None, timeout=600)
        return LLMResponse(content=extraer_texto_json(salida), model=model, provider=self.name)
