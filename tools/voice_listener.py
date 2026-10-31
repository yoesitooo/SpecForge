"""
Voice Listener — Mic → Groq Whisper → texto
============================================
VAD (Voice Activity Detection) por energía RMS.
Graba hasta que detecta silencio prolongado, luego transcribe con Whisper.

Flujo:
  1. Escucha el mic continuamente en chunks de 100ms
  2. Cuando la energía supera el umbral → empieza a grabar
  3. Cuando hay >1.5s de silencio tras hablar → detiene y transcribe
  4. Retorna el texto transcripto
"""

import asyncio
import io
import logging
import wave
import numpy as np

log = logging.getLogger(__name__)

SAMPLE_RATE    = 16000   # Whisper espera 16kHz
CHUNK_DURATION = 0.1     # segundos por chunk
CHUNK_SAMPLES  = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_THRESH = 0.01    # RMS threshold — ajustar según micrófono
SILENCE_LIMIT  = 1.5     # segundos de silencio para cortar
MAX_DURATION   = 30      # máximo de grabación en segundos
LANGUAGE       = "es"    # idioma para Whisper


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)) / 32768)


def _to_wav_bytes(frames: list[np.ndarray]) -> bytes:
    """Convierte lista de frames numpy a bytes WAV en memoria."""
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)       # int16 = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


async def listen_once(on_state=None) -> str | None:
    """
    Escucha el micrófono hasta detectar silencio y retorna el texto transcripto.

    on_state: callback async opcional para notificar cambios de estado
              on_state("listening") / on_state("thinking") / on_state("idle")

    Retorna None si no se detectó voz o hubo error.
    """
    try:
        import sounddevice as sd
    except ImportError:
        log.error("sounddevice no instalado. Ejecuta: pip install sounddevice")
        return None

    try:
        from groq import Groq
        from core.config import GROQ_API_KEY
        client = Groq(api_key=GROQ_API_KEY)
    except ImportError:
        log.error("groq SDK no instalado. Ejecuta: pip install groq")
        return None

    if on_state:
        await on_state("listening")

    silent_chunks = 0
    speaking = False
    total_chunks = 0
    max_chunks = int(MAX_DURATION / CHUNK_DURATION)
    silence_chunks_needed = int(SILENCE_LIMIT / CHUNK_DURATION)

    loop = asyncio.get_event_loop()

    def _record_blocking():
        nonlocal silent_chunks, speaking, total_chunks
        collected: list[np.ndarray] = []

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                            blocksize=CHUNK_SAMPLES) as stream:
            while total_chunks < max_chunks:
                chunk, _ = stream.read(CHUNK_SAMPLES)
                total_chunks += 1
                energy = _rms(chunk)

                if energy > SILENCE_THRESH:
                    speaking = True
                    silent_chunks = 0
                    collected.append(chunk.copy())
                elif speaking:
                    silent_chunks += 1
                    collected.append(chunk.copy())
                    if silent_chunks >= silence_chunks_needed:
                        break

        return collected

    try:
        recorded = await loop.run_in_executor(None, _record_blocking)
    except Exception as e:
        log.error(f"Error grabando audio: {e}")
        return None

    if not speaking or len(recorded) < 3:
        if on_state:
            await on_state("idle")
        return None

    if on_state:
        await on_state("thinking")

    wav_bytes = _to_wav_bytes(recorded)

    try:
        transcription = await loop.run_in_executor(
            None,
            lambda: client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes, "audio/wav"),
                model="whisper-large-v3-turbo",
                language=LANGUAGE,
                response_format="text",
            )
        )
        text = str(transcription).strip()
        log.info(f"[STT] Transcripto: {text[:100]}")
        return text if text else None
    except Exception as e:
        log.error(f"Error en Whisper: {e}")
        return None


async def calibrate_threshold() -> float:
    """
    Calibra el umbral de silencio grabando 2s de ambiente.
    Llama esto al inicio del voice transport para ajustar al micrófono del usuario.
    """
    try:
        import sounddevice as sd
        duration = 2.0
        print("Calibrando nivel de ruido ambiente... (2 segundos)")
        loop = asyncio.get_event_loop()
        recording = await loop.run_in_executor(
            None,
            lambda: sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                           channels=1, dtype="int16", blocking=True)
        )
        ambient_rms = _rms(recording)
        threshold = max(ambient_rms * 3.5, 0.008)
        print(f"Umbral calibrado: {threshold:.4f} (ambiente: {ambient_rms:.4f})")
        return threshold
    except Exception as e:
        log.warning(f"Calibración fallida, usando default: {e}")
        return SILENCE_THRESH
