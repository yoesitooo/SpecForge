"""
Voice Speaker — texto → Edge-TTS → audio con barge-in
=======================================================
Edge-TTS usa la infraestructura de Microsoft Edge (gratis, sin key, sin límite).
Pygame reproduce el MP3. Si el usuario habla mientras Jarvis habla, se interrumpe.

Voces disponibles en español:
  es-CO-GonzaloNeural  — hombre, Colombia (el más parecido a Jarvis)
  es-CO-SalomeNeural   — mujer, Colombia
  es-ES-AlvaroNeural   — hombre, España
  es-419-AndresNeural  — hombre, Latinoamérica
"""

import asyncio
import io
import logging
import os
import tempfile
import threading

log = logging.getLogger(__name__)

VOICE  = os.getenv("JARVIS_VOICE", "es-CO-GonzaloNeural")
RATE   = os.getenv("JARVIS_RATE",  "+5%")   # ligeramente más rápido = más natural
VOLUME = os.getenv("JARVIS_VOL",   "+0%")

# Umbral de barge-in — se actualiza con la calibración del mic
_barge_threshold: float = 0.02


def set_barge_threshold(t: float):
    global _barge_threshold
    _barge_threshold = t * 2.5  # más alto que el threshold de escucha para evitar falsos


async def speak(text: str, on_state=None) -> bool:
    """
    Convierte texto a voz y lo reproduce.
    Retorna True si el usuario interrumpió, False si terminó normal.
    on_state: callback async para notificar "speaking" / "idle"
    """
    if not text or not text.strip():
        return False

    try:
        import edge_tts
    except ImportError:
        log.error("edge-tts no instalado")
        print(f"\n[JARVIS]: {text}\n")
        return False

    try:
        import pygame
    except ImportError:
        log.error("pygame no instalado")
        print(f"\n[JARVIS]: {text}\n")
        return False

    if on_state:
        await on_state("speaking")

    clean = _clean_for_speech(text)

    try:
        communicate = edge_tts.Communicate(clean, VOICE, rate=RATE, volume=VOLUME)
        audio_buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buf.write(chunk["data"])

        audio_buf.seek(0)
        mp3_data = audio_buf.read()

        if not mp3_data:
            log.warning("Edge-TTS no retornó audio.")
            return False

        loop = asyncio.get_event_loop()
        interrupted = await loop.run_in_executor(
            None, _play_mp3_interruptible, mp3_data, _barge_threshold
        )
        return interrupted

    except Exception as e:
        log.error(f"Error en TTS: {e}")
        print(f"\n[JARVIS]: {clean}\n")
        return False
    finally:
        if on_state:
            await on_state("idle")


def _rms(chunk) -> float:
    import numpy as np
    return float(np.sqrt(np.mean(chunk.astype("float32") ** 2)) / 32768)


def _play_mp3_interruptible(mp3_data: bytes, threshold: float) -> bool:
    """
    Reproduce MP3 mientras monitorea el micrófono.
    Si detecta voz del usuario, para el audio inmediatamente.
    Retorna True si fue interrumpido.
    """
    interrupted = [False]
    stop_event = threading.Event()

    def _mic_watcher():
        try:
            import sounddevice as sd
            import numpy as np

            SAMPLE_RATE = 16000
            BLOCK = 1600  # 100ms
            # Necesita 2 chunks consecutivos de voz para evitar falsos positivos
            hits = 0

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                 dtype="int16", blocksize=BLOCK) as stream:
                while not stop_event.is_set():
                    chunk, _ = stream.read(BLOCK)
                    if _rms(chunk) > threshold:
                        hits += 1
                        if hits >= 2:  # 200ms de voz sostenida
                            interrupted[0] = True
                            stop_event.set()
                            break
                    else:
                        hits = 0
        except Exception as e:
            log.debug(f"[BARGE-IN] Mic watcher error: {e}")

    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(mp3_data)
            tmp_path = tmp.name

        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()

            mic_thread = threading.Thread(target=_mic_watcher, daemon=True)
            mic_thread.start()

            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                pygame.time.Clock().tick(20)

            stop_event.set()
            if interrupted[0]:
                pygame.mixer.music.stop()

        finally:
            pygame.mixer.music.stop()
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except Exception as e:
        log.error(f"Error en pygame playback: {e}")
        stop_event.set()

    return interrupted[0]


def _clean_for_speech(text: str) -> str:
    """Elimina markdown y caracteres que suenan raro en TTS."""
    import re
    text = re.sub(r"```[\s\S]*?```", "bloque de código omitido.", text)
    text = re.sub(r"`[^`]+`", lambda m: m.group().strip("`"), text)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[✅⚠️❌🎉🚀🔍📋🏗️🎨📝⚙️💻🔧🗄️🧪🔬⏪🛑🤖📊💬⏳🛑]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


async def list_voices_es() -> None:
    try:
        import edge_tts
        voices = await edge_tts.list_voices()
        es_voices = [v for v in voices if v["Locale"].startswith("es")]
        print("\nVoces en español disponibles:")
        for v in es_voices:
            gender = "H" if v["Gender"] == "Male" else "M"
            print(f"  [{gender}] {v['ShortName']:35s} — {v['LocaleName']}")
    except Exception as e:
        print(f"Error listando voces: {e}")
