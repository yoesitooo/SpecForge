"""
Telegram Transport — Bot async con aiogram 3.x
================================================
Recibe mensajes de Telegram y los pasa al orquestador.
Maneja: mensajes largos (fragmentación), Markdown, errores del bot.
"""

import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from core.config import TELEGRAM_TOKEN, TELEGRAM_ALLOWED_CHAT_ID
from orchestrator.executor import process_message

log = logging.getLogger(__name__)

bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
)
dp = Dispatcher()


def _allowed(chat_id: int) -> bool:
    """Si TELEGRAM_ALLOWED_CHAT_ID está configurado, solo ese chat puede usar el bot."""
    if not TELEGRAM_ALLOWED_CHAT_ID:
        return True
    return str(chat_id) == str(TELEGRAM_ALLOWED_CHAT_ID)


async def _send(chat_id: int, text: str):
    """Envía respuesta fragmentando si supera el límite de Telegram (4096 chars)."""
    # Fragmentar por párrafos para no romper el Markdown
    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) < 3800:
            current += paragraph + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = paragraph + "\n\n"
    if current:
        chunks.append(current.strip())

    for chunk in chunks:
        try:
            await bot.send_message(chat_id, chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Fallback a texto plano si el Markdown está malformado
            clean = chunk.replace("```", "").replace("**", "").replace("*", "")
            try:
                await bot.send_message(chat_id, clean, parse_mode=None)
            except Exception as e:
                log.error(f"Error enviando mensaje a {chat_id}: {e}")


@dp.message(CommandStart())
async def cmd_start(msg: Message):
    if not _allowed(msg.chat.id):
        return
    await _send(msg.chat.id,
        "👋 *SDD Ecosystem — Un Laps*\n\n"
        "Soy el orquestador de agentes de desarrollo. Puedo construir proyectos "
        "completos de software guiándote por 7 fases.\n\n"
        "Comandos disponibles:\n"
        "`/new [nombre]` — Iniciar proyecto nuevo\n"
        "`/go` — Avanzar al siguiente paso\n"
        "`/status` — Ver estado actual\n"
        "`/rollback [fase]` — Volver a una fase\n"
        "`/auto [n]` — Ejecutar N pasos automáticamente\n"
        "`/stop` — Detener modo automático\n"
        "`/spec` — Ver spec del proyecto actual"
    )


@dp.message(F.text)
async def handle_message(msg: Message):
    if not _allowed(msg.chat.id):
        await msg.answer("⛔ No autorizado.")
        return

    # Indicador de "procesando" para mensajes que tardan
    if not msg.text.startswith("/status"):
        await bot.send_chat_action(msg.chat.id, "typing")

    try:
        reply = await process_message(str(msg.chat.id), msg.text)
        await _send(msg.chat.id, reply)
    except Exception as e:
        log.exception(f"Error procesando mensaje: {e}")
        await _send(msg.chat.id, f"❌ Error interno: `{str(e)[:200]}`")


async def start_polling():
    """Arranca el bot en modo polling."""
    log.info("Bot de Telegram iniciado. Esperando mensajes...")
    await dp.start_polling(bot, allowed_updates=["message"])
