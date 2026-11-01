"""
Bot de Telegram (opcional) — usar SpecForge desde el celular
============================================================
Corre en TU computador: recibe los mensajes por long polling (no necesita
servidor ni puertos abiertos) y responde con el avance y el informe.

Seguridad, porque el bot ejecuta trabajo en tu máquina:
  - Solo responde al chat de TELEGRAM_ALLOWED_CHAT_ID (obligatorio: sin él no arranca).
  - /generar solo crea archivos dentro de la carpeta de proyectos; no ejecuta
    el código generado.
  - /reparar solo funciona con los proyectos declarados en SPECFORGE_REPOS,
    cada uno con SU comando de pruebas. Desde Telegram no se puede escribir
    un comando ni una ruta arbitraria.

Comandos:
  /generar <idea>     crea el proyecto y envía el informe
  /reparar <nombre>   arregla un proyecto declarado y envía el resultado
  /proyectos          lista los proyectos que se pueden reparar
  /estado             qué está haciendo el bot
  /ayuda
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

API = "https://api.telegram.org"
MAX_MENSAJE = 4000  # Telegram admite 4096 caracteres

AYUDA = (
    "SpecForge 🤖\n\n"
    "/generar <idea> — crea un proyecto con especificaciones, tareas y código\n"
    "/reparar <nombre> — arregla un proyecto declarado cuyas pruebas fallan\n"
    "/proyectos — proyectos que se pueden reparar\n"
    "/estado — qué estoy haciendo\n\n"
    "Ejemplo: /generar agenda de citas para un consultorio"
)


class ConfigTelegramInvalida(ValueError):
    pass


@dataclass(frozen=True)
class RepoPermitido:
    nombre: str
    ruta: str
    prueba: str


def leer_repos(valor: str) -> dict[str, RepoPermitido]:
    """
    SPECFORGE_REPOS = "nombre=ruta|comando de pruebas; otro=ruta|comando"
    Ejemplo: "lexai=C:/code/LexAI|npm test; api=/home/yo/api|pytest -q"
    """
    repos = {}
    for parte in [p.strip() for p in valor.split(";") if p.strip()]:
        nombre, _, resto = parte.partition("=")
        ruta, _, prueba = resto.partition("|")
        if not (nombre.strip() and ruta.strip() and prueba.strip()):
            raise ConfigTelegramInvalida(f"SPECFORGE_REPOS mal escrito en '{parte}' (formato: nombre=ruta|comando)")
        repos[nombre.strip().lower()] = RepoPermitido(nombre.strip().lower(), ruta.strip(), prueba.strip())
    return repos


def trocear(texto: str, tam: int = MAX_MENSAJE) -> list[str]:
    """Divide un texto largo en mensajes, cortando preferiblemente en saltos de línea."""
    partes = []
    while len(texto) > tam:
        corte = texto.rfind("\n", 0, tam)
        corte = corte if corte > tam // 2 else tam
        partes.append(texto[:corte])
        texto = texto[corte:].lstrip("\n")
    return partes + ([texto] if texto else [])


class BotTelegram:
    def __init__(
        self,
        token: str,
        chat_permitido: str,
        repos: dict[str, RepoPermitido] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        carpeta_proyectos: str | None = None,
    ):
        if not token:
            raise ConfigTelegramInvalida("Falta TELEGRAM_TOKEN en .env (créalo con @BotFather).")
        if not chat_permitido:
            raise ConfigTelegramInvalida(
                "Falta TELEGRAM_ALLOWED_CHAT_ID en .env. Es obligatorio: sin él cualquiera "
                "podría usar tu bot. Tu ID te lo da @userinfobot."
            )
        self._base = f"{API}/bot{token}"
        self.chat = str(chat_permitido)
        self.repos = repos or {}
        self.carpeta = carpeta_proyectos
        self._cliente = httpx.AsyncClient(timeout=70, transport=transport)
        self._offset = 0
        self.trabajo: str | None = None  # una tarea pesada a la vez
        self._tareas: set[asyncio.Task] = set()

    # ── API de Telegram ─────────────────────────────────────────────────────

    async def _llamar(self, metodo: str, **kwargs) -> dict:
        r = await self._cliente.post(f"{self._base}/{metodo}", **kwargs)
        datos = r.json()
        if not datos.get("ok"):
            raise RuntimeError(f"Telegram {metodo}: {datos.get('description', r.status_code)}")
        return datos

    async def enviar(self, texto: str) -> None:
        for parte in trocear(texto):
            await self._llamar("sendMessage", json={"chat_id": self.chat, "text": parte})

    async def enviar_archivo(self, ruta: Path, titulo: str = "") -> None:
        with open(ruta, "rb") as f:
            await self._llamar(
                "sendDocument",
                data={"chat_id": self.chat, "caption": titulo[:1000]},
                files={"document": (ruta.name, f)},
            )

    async def recibir(self, espera: int = 50) -> list[dict]:
        datos = await self._llamar(
            "getUpdates",
            json={"offset": self._offset, "timeout": espera, "allowed_updates": ["message"]},
        )
        updates = datos.get("result", [])
        if updates:
            self._offset = updates[-1]["update_id"] + 1
        return updates

    # ── lógica ──────────────────────────────────────────────────────────────

    def _avisador(self):
        """avisar() de los procesos es síncrono: encola el envío sin bloquear."""
        def avisar(texto: str) -> None:
            t = asyncio.get_running_loop().create_task(self.enviar(texto))
            self._tareas.add(t)
            t.add_done_callback(self._tareas.discard)
        return avisar

    async def manejar(self, update: dict) -> None:
        msg = update.get("message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        texto = (msg.get("text") or "").strip()
        if chat != self.chat:
            log.warning("Mensaje ignorado de un chat no autorizado: %s", chat)
            return
        comando, _, arg = texto.partition(" ")
        comando = comando.split("@")[0].lower()
        arg = arg.strip()

        if comando in ("/start", "/ayuda", "/help"):
            await self.enviar(AYUDA)
        elif comando == "/estado":
            await self.enviar(f"Trabajando en: {self.trabajo}" if self.trabajo else "Libre. Mándame /generar o /reparar.")
        elif comando == "/proyectos":
            if not self.repos:
                await self.enviar("No hay proyectos declarados. Agrégalos en SPECFORGE_REPOS dentro de .env.")
            else:
                await self.enviar("Proyectos que puedo reparar:\n" + "\n".join(f"• {r.nombre} — {r.prueba}" for r in self.repos.values()))
        elif comando in ("/generar", "/reparar"):
            if self.trabajo:
                await self.enviar(f"Ya estoy trabajando en: {self.trabajo}. Espera a que termine.")
            elif not arg:
                await self.enviar(f"Uso: {comando} <{'idea' if comando == '/generar' else 'nombre'}>")
            elif comando == "/reparar" and arg.lower() not in self.repos:
                await self.enviar(f"'{arg}' no está en SPECFORGE_REPOS. Usa /proyectos para ver los disponibles.")
            else:
                trabajo = self._generar(arg) if comando == "/generar" else self._reparar(self.repos[arg.lower()])
                t = asyncio.create_task(self._ejecutar(f"{comando} {arg}", trabajo))
                self._tareas.add(t)
                t.add_done_callback(self._tareas.discard)
        else:
            await self.enviar("No entendí. " + AYUDA)

    async def _ejecutar(self, descripcion: str, trabajo) -> None:
        self.trabajo = descripcion
        try:
            await trabajo
        except Exception as e:
            log.exception("Fallo en %s", descripcion)
            await self.enviar(f"❌ {descripcion} falló: {e}")
        finally:
            self.trabajo = None

    async def _generar(self, idea: str) -> None:
        from .generar import Generador

        await self.enviar(f"🚀 Generando: {idea}\nTe aviso cada etapa.")
        g = Generador(idea, carpeta=self.carpeta, avisar=self._avisador())
        inf = await g.ejecutar(verificar=False)  # el código generado no se ejecuta desde Telegram
        malas = [t for t, r in inf.tareas.items() if not r.ok]
        await self.enviar(
            f"✅ Listo: {inf.proyecto}\n"
            + (f"⚠️ Tareas con problemas: {', '.join(malas)}\n" if malas else "")
            + "Te envío el informe."
        )
        await self.enviar_archivo(inf.proyecto / "specs" / "informe.md", "Informe de SpecForge")

    async def _reparar(self, repo: RepoPermitido) -> None:
        from .reparar import Reparador

        await self.enviar(f"🔧 Reparando {repo.nombre} con: {repo.prueba}")
        r = await Reparador(repo.ruta, repo.prueba, avisar=self._avisador()).ejecutar()
        await self.enviar(r.resumen())

    async def correr(self) -> None:
        await self.enviar("SpecForge conectado ✅\n\n" + AYUDA)
        while True:
            try:
                for u in await self.recibir():
                    await self.manejar(u)
            except (httpx.HTTPError, RuntimeError) as e:
                log.warning("Error de conexión con Telegram, reintento en 5 s: %s", e)
                await asyncio.sleep(5)


def desde_entorno() -> BotTelegram:
    return BotTelegram(
        token=os.environ.get("TELEGRAM_TOKEN", "").strip(),
        chat_permitido=os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip(),
        repos=leer_repos(os.environ.get("SPECFORGE_REPOS", "")),
    )
