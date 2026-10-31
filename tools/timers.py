"""
Timers — recordatorios, pomodoro y temporizadores por voz
==========================================================
Usa el bus de notificaciones para hablar cuando el timer vence,
sin bloquear el loop principal.
"""

import asyncio
import logging

log = logging.getLogger(__name__)

# timers activos: id → task
_active: dict[str, asyncio.Task] = {}
_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"timer_{_counter}"


async def _run_timer(timer_id: str, seconds: int, message: str):
    try:
        await asyncio.sleep(seconds)
        from core.notifications import push
        await push(message)
        log.info(f"[TIMER] Vencido: {timer_id} — {message}")
    except asyncio.CancelledError:
        log.info(f"[TIMER] Cancelado: {timer_id}")
    finally:
        _active.pop(timer_id, None)


def set_timer(minutes: float, message: str = "") -> str:
    """
    Crea un timer. Cuando vence, Jarvis habla el mensaje.
    Funciona en background — no bloquea la conversación.
    """
    seconds = int(minutes * 60)
    if seconds <= 0:
        return "El tiempo debe ser mayor a 0."

    msg = message or f"Pasaron los {_fmt_time(seconds)}."
    tid = _next_id()

    try:
        task = asyncio.create_task(_run_timer(tid, seconds, msg))
        _active[tid] = task
        log.info(f"[TIMER] Creado {tid}: {_fmt_time(seconds)}")
        return f"Timer de {_fmt_time(seconds)} activado. Te aviso cuando venza."
    except RuntimeError:
        # No hay loop activo (modo CLI síncrono)
        return f"Timer anotado: {_fmt_time(seconds)} — {msg}"


def cancel_all_timers() -> str:
    """Cancela todos los timers activos."""
    if not _active:
        return "No hay timers activos."
    count = len(_active)
    for task in list(_active.values()):
        task.cancel()
    _active.clear()
    return f"{count} timer(s) cancelado(s)."


def list_timers() -> str:
    """Lista los timers activos."""
    if not _active:
        return "No hay timers activos."
    return f"Timers activos: {', '.join(_active.keys())}"


# ── Pomodoro ──────────────────────────────────────────────────────────────────

_pomodoro_task: asyncio.Task | None = None


async def _run_pomodoro(work_min: int, break_min: int, cycles: int):
    from core.notifications import push
    for i in range(1, cycles + 1):
        await push(f"Pomodoro {i} de {cycles}. A trabajar por {work_min} minutos.")
        await asyncio.sleep(work_min * 60)
        if i < cycles:
            await push(f"Descanso de {break_min} minutos. Relájate.")
            await asyncio.sleep(break_min * 60)
        else:
            await push(f"Terminaste el ciclo completo de {cycles} pomodoros. Bien hecho.")


def start_pomodoro(work_minutes: int = 25, break_minutes: int = 5, cycles: int = 4) -> str:
    """Inicia un ciclo Pomodoro."""
    global _pomodoro_task
    if _pomodoro_task and not _pomodoro_task.done():
        return "Ya hay un Pomodoro corriendo. Di 'cancela el pomodoro' para detenerlo."
    try:
        _pomodoro_task = asyncio.create_task(
            _run_pomodoro(work_minutes, break_minutes, cycles)
        )
        total = cycles * work_minutes + (cycles - 1) * break_minutes
        return (
            f"Pomodoro iniciado: {cycles} ciclos de {work_minutes} min trabajo "
            f"/ {break_minutes} min descanso. Total: {total} min."
        )
    except RuntimeError:
        return f"Pomodoro anotado: {cycles} x {work_minutes} min."


def cancel_pomodoro() -> str:
    """Cancela el Pomodoro activo."""
    global _pomodoro_task
    if _pomodoro_task and not _pomodoro_task.done():
        _pomodoro_task.cancel()
        _pomodoro_task = None
        return "Pomodoro cancelado."
    return "No hay Pomodoro activo."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_time(seconds: int) -> str:
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}min" if m else f"{h} hora{'s' if h > 1 else ''}"
    if seconds >= 60:
        m = seconds // 60
        s = seconds % 60
        return f"{m} minuto{'s' if m > 1 else ''}" + (f" {s}s" if s else "")
    return f"{seconds} segundo{'s' if seconds > 1 else ''}"
