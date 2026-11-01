import asyncio
import json
from pathlib import Path

import httpx
import pytest

from specforge import telegram
from specforge.telegram import BotTelegram, ConfigTelegramInvalida, RepoPermitido, leer_repos, trocear


class TelegramFalso:
    """Simula la API de Telegram y guarda lo que el bot envía."""

    def __init__(self, updates=()):
        self.updates = list(updates)
        self.enviados: list[str] = []
        self.archivos: list[str] = []

    def transporte(self):
        def handler(req: httpx.Request):
            metodo = req.url.path.rsplit("/", 1)[-1]
            if metodo == "getUpdates":
                lote, self.updates = self.updates, []
                return httpx.Response(200, json={"ok": True, "result": lote})
            if metodo == "sendMessage":
                self.enviados.append(json.loads(req.content)["text"])
            elif metodo == "sendDocument":
                self.archivos.append(req.content.decode("utf-8", "replace"))
            return httpx.Response(200, json={"ok": True, "result": {}})
        return httpx.MockTransport(handler)


def update(texto, chat=111, uid=1):
    return {"update_id": uid, "message": {"chat": {"id": chat}, "text": texto}}


def bot(api, repos=None):
    return BotTelegram("TOKEN", "111", repos or {}, transport=api.transporte())


async def procesar(b):
    for u in await b.recibir(espera=0):
        await b.manejar(u)
    await asyncio.gather(*list(b._tareas))
    await asyncio.gather(*list(b._tareas))  # avisos encolados por los trabajos


def test_exige_token_y_chat_permitido():
    with pytest.raises(ConfigTelegramInvalida, match="TELEGRAM_TOKEN"):
        BotTelegram("", "1")
    with pytest.raises(ConfigTelegramInvalida, match="obligatorio"):
        BotTelegram("t", "")


def test_ignora_chats_no_autorizados_y_avanza_el_offset():
    api = TelegramFalso([update("/ayuda", chat=999, uid=41)])
    b = bot(api)
    asyncio.run(procesar(b))
    assert api.enviados == [] and b._offset == 42


def test_ayuda_estado_y_comando_desconocido():
    api = TelegramFalso([update("/ayuda"), update("/estado", uid=2), update("hola", uid=3)])
    asyncio.run(procesar(bot(api)))
    assert "/generar <idea>" in api.enviados[0]
    assert api.enviados[1].startswith("Libre")
    assert api.enviados[2].startswith("No entendí")


def test_reparar_solo_proyectos_declarados(monkeypatch):
    llamados = []

    class ReparadorFalso:
        def __init__(self, ruta, prueba, avisar):
            llamados.append((ruta, prueba))

        async def ejecutar(self):
            class R:
                def resumen(self):
                    return "Estado: arreglado"
            return R()

    import specforge.reparar
    monkeypatch.setattr(specforge.reparar, "Reparador", ReparadorFalso)
    repos = {"api": RepoPermitido("api", "/code/api", "pytest -q")}
    api = TelegramFalso([update("/reparar ../../etc"), update("/reparar API", uid=2), update("/proyectos", uid=3)])
    asyncio.run(procesar(bot(api, repos)))

    assert "no está en SPECFORGE_REPOS" in api.enviados[0]
    assert llamados == [("/code/api", "pytest -q")]  # el comando sale de la config, nunca del chat
    assert "Estado: arreglado" in api.enviados
    assert any("• api — pytest -q" in m for m in api.enviados)


def test_generar_envia_avance_e_informe(monkeypatch, tmp_path):
    class InformeFalso:
        proyecto = tmp_path / "citas"
        tareas = {}

    (tmp_path / "citas" / "specs").mkdir(parents=True)
    (tmp_path / "citas" / "specs" / "informe.md").write_text("# Informe de prueba")
    recibido = {}

    class GeneradorFalso:
        def __init__(self, idea, carpeta=None, avisar=print):
            recibido["idea"] = idea
            self.avisar = avisar

        async def ejecutar(self, verificar):
            recibido["verificar"] = verificar
            self.avisar("📋 Requisitos…")
            return InformeFalso()

    import specforge.generar
    monkeypatch.setattr(specforge.generar, "Generador", GeneradorFalso)
    api = TelegramFalso([update("/generar agenda de citas")])
    asyncio.run(procesar(bot(api)))

    assert recibido == {"idea": "agenda de citas", "verificar": False}  # no ejecuta código generado
    assert "📋 Requisitos…" in api.enviados
    assert any(m.startswith("✅ Listo") for m in api.enviados)
    assert "# Informe de prueba" in api.archivos[0]


def test_un_trabajo_a_la_vez():
    api = TelegramFalso()
    b = bot(api)
    b.trabajo = "/generar algo"
    asyncio.run(b.manejar(update("/generar otra cosa")))
    assert "Ya estoy trabajando" in api.enviados[0]


def test_leer_repos():
    repos = leer_repos("LexAI=C:/code/LexAI|npm test; api=/home/yo/api|pytest -q")
    assert repos["lexai"] == RepoPermitido("lexai", "C:/code/LexAI", "npm test")
    assert repos["api"].prueba == "pytest -q"
    assert leer_repos("") == {}
    with pytest.raises(ConfigTelegramInvalida):
        leer_repos("roto=/sin/comando")


def test_trocear_respeta_el_limite():
    texto = "\n".join(f"línea {i}" for i in range(2000))
    partes = trocear(texto, 500)
    assert all(len(p) <= 500 for p in partes)
    assert "\n".join(partes).replace("\n", "") == texto.replace("\n", "")


def test_cli_sin_configuracion_explica_que_falta(monkeypatch, capsys):
    from specforge.__main__ import main
    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    assert main(["telegram"]) == 2
    assert "TELEGRAM_TOKEN" in capsys.readouterr().out
