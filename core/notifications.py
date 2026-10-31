"""
Notification bus — DAG → voz
============================
El executor empuja mensajes aquí cuando completa una fase.
El voice_transport los saca y los habla, incluso en modo dormido.
"""

import asyncio
import logging

log = logging.getLogger(__name__)

_queue: asyncio.Queue | None = None


def _q() -> asyncio.Queue:
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def push(message: str):
    """Llamado desde el executor cuando termina una fase DAG."""
    await _q().put(message)
    log.info(f"[NOTIF] Encolado: {message[:60]}")


def push_sync(message: str):
    """Versión síncrona — usa cuando no hay loop activo."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_q().put(message))
        else:
            loop.run_until_complete(_q().put(message))
    except Exception as e:
        log.warning(f"[NOTIF] No se pudo encolar: {e}")


async def pop() -> str | None:
    """Retorna el siguiente mensaje o None si no hay."""
    try:
        return _q().get_nowait()
    except asyncio.QueueEmpty:
        return None
