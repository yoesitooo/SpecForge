"""
Voice Transport — Jarvis con wake word
========================================
Estados:
  dormant  → escucha pasiva solo por "Jarvis"
  idle     → despierto, esperando que el usuario hable
  listening→ mic activo grabando
  thinking → Whisper + agentes procesando
  speaking → Edge-TTS reproduciendo

Flujo:
  [dormant] → "Jarvis" detectado → "Dime." → [idle]
  [idle]    → silencio 45s        → "Voy a dormir." → [dormant]
  [idle]    → usuario habla       → [listening] → [thinking] → [speaking] → [idle]
  [speaking]→ usuario interrumpe  → [listening] inmediato → ...
"""

import logging
import os
import time
from datetime import datetime

log = logging.getLogger(__name__)

CHAT_ID    = os.getenv("VOICE_CHAT_ID", "jarvis_voice")
STOP_WORDS = {"para", "detente", "stop", "silencio", "modo texto", "apágate", "duérmete"}
IDLE_TIMEOUT = 45  # segundos sin actividad antes de volver a dormir


# ── Estado global del visual ──────────────────────────────────────────────────

class JarvisState:
    def __init__(self):
        self.current   = "idle"
        self.last_text = ""
        self.last_user = ""
        self.dormant   = True
        self._broadcast_fn = None

    def set_broadcast(self, fn):
        self._broadcast_fn = fn

    async def set(self, state: str, text: str = ""):
        self.current = state
        if text:
            if state == "listening":
                self.last_user = text
            else:
                self.last_text = text
        if self._broadcast_fn:
            try:
                await self._broadcast_fn(state, text)
            except Exception:
                pass


_state = JarvisState()


def get_state() -> JarvisState:
    return _state


# ── Rich terminal UI ──────────────────────────────────────────────────────────

def _make_panel(state: str, user_text: str, bot_text: str, dormant: bool = False):
    try:
        from rich.panel import Panel
        from rich.text import Text

        STATE_STYLE = {
            "idle":      ("dim white",    "○  En espera"),
            "listening": ("bold cyan",    "◉  Escuchando..."),
            "thinking":  ("bold magenta", "◈  Procesando..."),
            "speaking":  ("bold yellow",  "◆  Hablando..."),
        }
        color, label = STATE_STYLE.get(state, ("white", state))
        if dormant:
            color, label = "dim grey50", "·  Dormido — di 'Jarvis' para activar"

        content = Text()
        content.append(f"{label}\n\n", style=color)
        if user_text:
            content.append("Tú: ", style="dim cyan")
            content.append(f"{user_text[:120]}\n", style="cyan")
        if bot_text:
            content.append("\nJarvis: ", style="dim yellow")
            content.append(f"{bot_text[:300]}\n", style="yellow")

        ts = datetime.now().strftime("%H:%M:%S")
        return Panel(
            content,
            title=f"[bold gold1]SDD Jarvis[/bold gold1]  [dim]{ts}[/dim]",
            border_style=color,
            padding=(0, 2),
        )
    except ImportError:
        return None


# ── Loop principal ────────────────────────────────────────────────────────────

async def start_voice():
    from tools.voice_listener import listen_once, calibrate_threshold
    from tools.voice_speaker  import speak, set_barge_threshold
    from tools.wake_word      import listen_for_wakeword
    from orchestrator.executor import process_message
    from core.notifications    import pop as notif_pop

    try:
        from rich.live    import Live
        from rich.console import Console
        console  = Console()
        use_rich = True
    except ImportError:
        use_rich = False
        console  = None

    print("\n" + "="*55)
    print("  SDD JARVIS — Iniciando...")
    print("  Di 'Jarvis' para activar.")
    print("  Abre http://localhost:8000/jarvis para el visual")
    print("="*55 + "\n")

    threshold = await calibrate_threshold()
    set_barge_threshold(threshold)

    panel_holder = [_make_panel("idle", "", "", dormant=True)]

    # ── Callbacks de estado ───────────────────────────────────────────────

    if use_rich:
        from rich.live import Live
        live_holder: list = []

        async def on_state(state: str, text: str = ""):
            await _state.set(state, text)
            panel_holder[0] = _make_panel(
                state, _state.last_user, _state.last_text, dormant=_state.dormant
            )
            if live_holder:
                live_holder[0].update(panel_holder[0])
    else:
        async def on_state(state: str, text: str = ""):
            await _state.set(state, text)

    # ── Lógica compartida ─────────────────────────────────────────────────

    async def _handle_text(text: str) -> bool:
        """Procesa un mensaje. Retorna True si debe volver a dormido."""
        if any(w in text.lower() for w in STOP_WORDS):
            await speak("Okey, me duermo. Di Jarvis cuando me necesites.", on_state=on_state)
            return True

        await on_state("thinking")
        try:
            reply = await process_message(CHAT_ID, text)
        except Exception as e:
            reply = f"Error: {str(e)[:80]}"

        await on_state("thinking", reply)
        interrupted = await speak(reply, on_state=on_state)

        if interrupted:
            await on_state("listening", "...")
            interrupt_text = await listen_once(on_state=on_state)
            if interrupt_text:
                await on_state("listening", interrupt_text)
                return await _handle_text(interrupt_text)

        return False

    async def _dormant_loop():
        """Espera wake word o notificaciones. Retorna cuando Jarvis es activado."""
        _state.dormant = True
        await on_state("idle")
        log.info("[VOICE] Modo dormido")
        while True:
            notif = await notif_pop()
            if notif:
                await speak(notif, on_state=on_state)
                await on_state("idle")
                continue

            woken = await listen_for_wakeword(threshold)
            if woken:
                _state.dormant = False
                return

    async def _awake_loop():
        """Loop principal cuando Jarvis está despierto. Retorna cuando debe dormirse."""
        await speak("Dime.", on_state=on_state)
        last_activity = time.time()

        while True:
            # Timeout → volver a dormir
            if time.time() - last_activity > IDLE_TIMEOUT:
                await speak("Voy a dormir. Di Jarvis cuando me necesites.", on_state=on_state)
                return

            # Notificaciones
            notif = await notif_pop()
            if notif:
                await speak(notif, on_state=on_state)
                last_activity = time.time()
                continue

            await on_state("idle")
            text = await listen_once(on_state=on_state)

            if not text:
                continue

            last_activity = time.time()
            await on_state("listening", text)
            log.info(f"[VOICE] Usuario: {text}")

            go_sleep = await _handle_text(text)
            if go_sleep:
                return

    # ── Main loop: dormido ↔ despierto ────────────────────────────────────

    async def _main():
        while True:
            await _dormant_loop()
            await _awake_loop()

    if use_rich:
        with Live(panel_holder[0], refresh_per_second=4, console=console) as live:
            live_holder.append(live)
            await _main()
    else:
        await _main()


# ── Selector de modo al iniciar proyecto ─────────────────────────────────────

async def ask_input_mode() -> str:
    from tools.voice_speaker import speak
    from tools.voice_listener import listen_once

    prompt = (
        "Proyecto iniciado. "
        "Di 'voz' para hacer el discovery hablando, "
        "o 'texto' para escribir en Telegram."
    )
    await speak(prompt)
    response = await listen_once()
    if response and any(w in response.lower() for w in ["voz", "hablar", "audio", "mic"]):
        await speak("Perfecto. Cuéntame: ¿qué problema quieres resolver y para quién?")
        return "voice"
    else:
        await speak("Entendido. Escríbeme en Telegram cuando estés listo.")
        return "text"
