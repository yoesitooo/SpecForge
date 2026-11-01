import asyncio
import json

import pytest

from providers import cli_providers
from providers.cli_providers import (
    AntigravityCLIProvider,
    ClaudeCLIProvider,
    CLIProviderError,
    extraer_texto_json,
)


def test_extrae_response_del_json_de_agy():
    salida = json.dumps({"status": "SUCCESS", "response": "hola", "usage": {"output_tokens": 1}})
    assert extraer_texto_json(salida) == "hola"


def test_estado_de_error_de_agy():
    salida = json.dumps({"status": "ERROR", "error": "quota exceeded"})
    with pytest.raises(CLIProviderError, match="quota"):
        extraer_texto_json(salida)


def test_salida_no_json_se_devuelve_tal_cual():
    assert extraer_texto_json("texto plano") == "texto plano"


def test_agy_pasa_el_prompt_como_argumento_sin_shell(monkeypatch):
    capturado = {}

    async def falso_run(cmd, stdin_text, timeout):
        capturado.update(cmd=cmd, stdin=stdin_text)
        return json.dumps({"status": "SUCCESS", "response": "ok"})

    monkeypatch.setattr(cli_providers, "_run", falso_run)
    r = asyncio.run(AntigravityCLIProvider().complete("sis", "usr; rm -rf /", model="gemini-3.8-flash-medium"))
    assert r.content == "ok"
    cmd = capturado["cmd"]
    assert cmd[0] == "agy" and cmd[-2] == "--print" and cmd[-1].endswith("usr; rm -rf /")
    assert cmd[cmd.index("--model") + 1] == "gemini-3.8-flash-medium"
    assert capturado["stdin"] is None


def test_agy_sin_modelo_usa_el_del_cli(monkeypatch):
    async def falso_run(cmd, stdin_text, timeout):
        assert "--model" not in cmd
        return json.dumps({"status": "SUCCESS", "response": "ok"})

    monkeypatch.setattr(cli_providers, "_run", falso_run)
    asyncio.run(AntigravityCLIProvider().complete("s", "u", model=""))


def test_agy_rechaza_prompts_demasiado_largos():
    with pytest.raises(CLIProviderError, match="largo"):
        asyncio.run(AntigravityCLIProvider().complete("s", "x" * 40_000, model=""))


def test_claude_recibe_el_prompt_por_stdin(monkeypatch):
    capturado = {}

    async def falso_run(cmd, stdin_text, timeout):
        capturado.update(cmd=cmd, stdin=stdin_text)
        return "respuesta"

    monkeypatch.setattr(cli_providers, "_run", falso_run)
    asyncio.run(ClaudeCLIProvider().complete("sis", "usr", model="sonnet"))
    assert capturado["cmd"][:2] == ["claude", "--print"]
    assert capturado["stdin"].startswith("sis") and capturado["stdin"].endswith("usr")


def test_run_real_reporta_codigo_de_salida():
    with pytest.raises(CLIProviderError, match="código 3"):
        asyncio.run(cli_providers._run(["python3", "-c", "import sys; sys.exit(3)"], None, 10))


def test_run_real_devuelve_stdout_sin_ansi():
    out = asyncio.run(cli_providers._run(
        ["python3", "-c", "import sys; print('\\x1b[32mverde\\x1b[0m', sys.stdin.read())"], "hola", 10
    ))
    assert out == "verde hola"
