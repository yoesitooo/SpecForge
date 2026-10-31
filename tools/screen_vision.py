"""
Screen Vision — screenshot + Groq Vision
=========================================
Toma captura de pantalla, la codifica en base64 y la analiza
con llama-3.2-11b-vision-preview (gratis en Groq).
"""

import asyncio
import base64
import io
import logging

log = logging.getLogger(__name__)


async def look_at_screen(question: str = "¿Qué ves en la pantalla? Sé específico y conciso.") -> str:
    """
    Captura la pantalla completa y hace una pregunta sobre ella.
    Retorna la respuesta del modelo de visión.
    """
    loop = asyncio.get_event_loop()

    # Capturar pantalla
    try:
        screenshot_b64 = await loop.run_in_executor(None, _capture_screen)
    except Exception as e:
        return f"No pude capturar la pantalla: {e}"

    # Analizar con Groq Vision
    try:
        from groq import AsyncGroq
        from core.config import GROQ_API_KEY

        client = AsyncGroq(api_key=GROQ_API_KEY)

        response = await client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": question,
                        },
                    ],
                }
            ],
            max_tokens=512,
            temperature=0.3,
        )
        return response.choices[0].message.content or "No pude analizar la pantalla."

    except Exception as e:
        log.error(f"[VISION] Error: {e}")
        return f"Error analizando pantalla: {str(e)[:100]}"


def _capture_screen() -> str:
    """Captura la pantalla y devuelve base64 PNG. Comprime para reducir tokens."""
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
    except Exception:
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
        except Exception as e:
            raise RuntimeError(f"No se pudo capturar pantalla: {e}")

    # Reducir a 50% para no exceder límites del modelo
    w, h = screenshot.size
    screenshot = screenshot.resize((w // 2, h // 2))

    buf = io.BytesIO()
    screenshot.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
