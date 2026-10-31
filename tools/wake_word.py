"""
Wake Word — escucha pasiva de "Jarvis"
=======================================
No usa modelos extra. Reutiliza Groq Whisper en ventanas cortas de 1.5s.
Solo envía audio a Whisper cuando hay actividad de voz real (VAD primero),
así el consumo de API en modo dormido es casi cero.

Variantes reconocidas: jarvis, jarvi, xarvis, harvis, jarbit, jarwis
(Whisper a veces transcribe diferente según el acento)
"""

import asyncio
import io
import logging
import wave
import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE   = 16000
CHUNK_SAMPLES = 1600          # 100ms por chunk
WAKE_WINDOW   = 2.0           # segundos de audio a analizar
SILENCE_GAP   = 0.3           # espera entre rondas si no hay voz (segundos)

WAKE_VARIANTS = {
    "jarvis", "jarvi", "xarvis", "harvis", "jarwis", "jarbit",
    "jarbis", "garvis", "jarvis,", "jarvis.", "oye jarvis",
}


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)) / 32768)


def _to_wav(frames: list) -> bytes:
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


def _contains_wakeword(text: str) -> bool:
    text = text.lower().strip()
    if any(w in text for w in WAKE_VARIANTS):
        return True
    # Fuzzy: las primeras 3 letras "jar" + longitud razonable
    words = text.split()
    return any(w.startswith("jar") and len(w) >= 4 for w in words)


async def listen_for_wakeword(threshold: float = 0.012) -> bool:
    """
    Escucha pasivamente. Retorna True cuando detecta la wake word.
    Bloquea hasta que la detecta — llamar en loop desde voice_transport.
    """
    try:
        import sounddevice as sd
    except ImportError:
        log.error("[WAKE] sounddevice no disponible")
        await asyncio.sleep(1)
        return False

    try:
        from groq import Groq
        from core.config import GROQ_API_KEY
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        log.error(f"[WAKE] Groq no disponible: {e}")
        await asyncio.sleep(1)
        return False

    loop = asyncio.get_event_loop()
    max_chunks = int(WAKE_WINDOW / 0.1)

    def _record_short():
        """Graba hasta WAKE_WINDOW segundos, solo si hay voz."""
        collected = []
        speaking = False
        silence = 0

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype="int16", blocksize=CHUNK_SAMPLES) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(CHUNK_SAMPLES)
                energy = _rms(chunk)
                if energy > threshold:
                    speaking = True
                    silence = 0
                    collected.append(chunk.copy())
                elif speaking:
                    silence += 1
                    collected.append(chunk.copy())
                    if silence >= 4:  # 400ms de silencio tras voz
                        break
                # Sin voz al inicio → seguir esperando en el siguiente ciclo
                elif not collected and _ == max_chunks - 1:
                    return None  # Nada detectado

        return collected if speaking else None

    try:
        recorded = await loop.run_in_executor(None, _record_short)
    except Exception as e:
        log.debug(f"[WAKE] Error grabando: {e}")
        await asyncio.sleep(SILENCE_GAP)
        return False

    if not recorded:
        await asyncio.sleep(SILENCE_GAP)
        return False

    # Hay voz — transcribir
    wav = _to_wav(recorded)
    try:
        result = await loop.run_in_executor(
            None,
            lambda: client.audio.transcriptions.create(
                file=("w.wav", wav, "audio/wav"),
                model="whisper-large-v3-turbo",
                language="es",
                response_format="text",
            )
        )
        text = str(result).strip()
        log.debug(f"[WAKE] Escuché: '{text}'")

        if _contains_wakeword(text):
            log.info("[WAKE] Wake word detectada!")
            return True

    except Exception as e:
        log.debug(f"[WAKE] Whisper error: {e}")

    return False
