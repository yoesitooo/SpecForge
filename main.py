"""
main.py — Entry point del SpecForge.
Inicializa DBs y arranca los transportes configurados.

Transportes disponibles (se pueden combinar con coma: TRANSPORT_MODE=voice,telegram):
  TRANSPORT_MODE=cli       → consola interactiva (default)
  TRANSPORT_MODE=telegram  → aiogram bot
  TRANSPORT_MODE=voice     → Jarvis por voz
  TRANSPORT_MODE=http      → solo la API HTTP (Docker / OpenClaw)
  ENABLE_HTTP=true         → FastAPI en HTTP_PORT (para OpenClaw y dashboard)
                             se puede activar junto a cualquier otro modo
"""

import asyncio
import logging
import os
import sys

from core.config import TELEGRAM_TOKEN, HTTP_PORT
from memory import session_store, engram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


async def _start_http():
    """Arranca el HTTP transport (FastAPI + uvicorn) de forma async."""
    import uvicorn
    from transports.http_transport import app
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=HTTP_PORT,
        log_level="warning",   # uvicorn no pisotea los logs del orchestrator
    )
    server = uvicorn.Server(config)
    log.info(f"HTTP transport en http://0.0.0.0:{HTTP_PORT} (OpenAI-compatible)")
    log.info(f"  /v1/chat/completions  → OpenClaw custom provider")
    log.info(f"  /sessions             → lista sesiones activas")
    log.info(f"  /status/<chat_id>     → estado de un proyecto")
    await server.serve()


async def run_auto_loop(chat_id: str, steps: int):
    from orchestrator.executor import advance

    for i in range(steps):
        state = session_store.get(chat_id)
        if state.get("auto_limit", 0) <= 0:
            break
        result = await advance(chat_id)
        log.info(f"Auto {i+1}/{steps}: {result[:80]}...")
        state["auto_limit"] = state.get("auto_limit", 0) - 1
        session_store.save(chat_id, state)
        if "COMPLETADO" in result or "Circuit Breaker" in result:
            break
        await asyncio.sleep(1)


async def _cli_transport():
    """CLI interactivo con Rich — funciona sin Telegram ni micrófono."""
    from orchestrator.executor import process_message

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.prompt import Prompt
        from rich.text import Text
        console = Console()
        use_rich = True
    except ImportError:
        use_rich = False
        console = None

    BANNER = """
╔══════════════════════════════════════════════════╗
║          SpecForge — Modo CLI                    ║
║                                                  ║
║  Habla con Jarvis o gestiona proyectos de código ║
║  Escribe 'ayuda' para ver comandos disponibles   ║
╚══════════════════════════════════════════════════╝"""

    HELP_TEXT = """
**Comandos del orquestador (proyectos de código):**
  /new <nombre>       — Iniciar proyecto nuevo
  /go                 — Avanzar al siguiente agente
  /status             — Ver fase actual del proyecto
  /auto <n>           — Ejecutar n pasos automáticamente
  /rollback <fase>    — Volver a una fase específica
  /spec               — Ver especificación generada
  /stop               — Detener modo automático

**Fases del DAG:**
  discovery → requirements → architecture → ux_ui → hu_writer
  → tech_spec → [frontend + backend + db] → [qa + code_review]

**Cualquier otro mensaje** → Jarvis responde como asistente
  Ejemplos: "busca X", "crea un Word con...", "qué es RAG"

**Salir:** Ctrl+C
"""

    if use_rich:
        console.print(BANNER, style="bold cyan")
        console.print()
    else:
        print(BANNER)

    while True:
        try:
            if use_rich:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: Prompt.ask("[bold cyan]Tú[/bold cyan]")
                )
            else:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Tú > "
                )

            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.lower() in {"ayuda", "help", "?"}:
                if use_rich:
                    console.print(Markdown(HELP_TEXT))
                else:
                    print(HELP_TEXT)
                continue

            if use_rich:
                console.print("[dim]Procesando...[/dim]")

            reply = await process_message("cli_user", user_input)

            if use_rich:
                # Detectar si es respuesta markdown del DAG o texto del asistente
                if any(c in reply for c in ["*", "#", "`", "✅", "🚀", "📋"]):
                    console.print(Panel(Markdown(reply), title="[bold yellow]Jarvis[/bold yellow]",
                                        border_style="yellow", padding=(1, 2)))
                else:
                    console.print(Panel(Text(reply, style="white"),
                                        title="[bold yellow]Jarvis[/bold yellow]",
                                        border_style="yellow", padding=(0, 2)))
                console.print()
            else:
                print(f"\nJarvis > {reply}\n")

        except (KeyboardInterrupt, EOFError):
            if use_rich:
                console.print("\n[dim]Hasta luego.[/dim]")
            else:
                print("\nHasta luego.")
            break


TRANSPORTES = {"telegram", "voice", "cli", "http"}


def parse_transportes(valor: str) -> set[str]:
    """'voice, telegram' → {"voice", "telegram"}. Falla si alguno no existe."""
    elegidos = {t.strip().lower() for t in valor.split(",") if t.strip()}
    desconocidos = elegidos - TRANSPORTES
    if not elegidos or desconocidos:
        log.error(
            f"TRANSPORT_MODE inválido: '{valor}'. Opciones: {', '.join(sorted(TRANSPORTES))} "
            "(se pueden combinar con coma)."
        )
        sys.exit(1)
    return elegidos


async def main():
    log.info("Iniciando SpecForge...")

    session_store.init_sessions()
    engram.init_db()
    log.info("DBs inicializadas.")

    transportes = parse_transportes(os.getenv("TRANSPORT_MODE", "cli"))
    enable_http = os.getenv("ENABLE_HTTP", "false").lower() == "true"

    tasks = []

    # ── Transportes (se pueden combinar: TRANSPORT_MODE=voice,telegram) ───────
    if "telegram" in transportes:
        if not TELEGRAM_TOKEN:
            log.error("TELEGRAM_TOKEN no configurado.")
            sys.exit(1)
        from transports.telegram_transport import start_polling
        log.info("Telegram transport activo.")
        tasks.append(start_polling())

    if "voice" in transportes:
        from transports.voice_transport import start_voice
        log.info("Voice transport (Jarvis) activo.")
        log.info(f"  Visual: http://localhost:{HTTP_PORT}/jarvis")
        tasks.append(start_voice())

    if "cli" in transportes:
        tasks.append(_cli_transport())

    # ── HTTP transport — rama OpenClaw + Jarvis visual (opcional) ────────────
    if enable_http or "http" in transportes:
        tasks.append(_start_http())
        # Inyectar broadcast al voice transport si ambos corren juntos
        if "voice" in transportes:
            from transports.http_transport import broadcast_jarvis_state
            from transports.voice_transport import get_state
            get_state().set_broadcast(broadcast_jarvis_state)

    if len(tasks) == 1:
        await tasks[0]
    else:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
