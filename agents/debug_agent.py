"""
Debug Agent — diagnóstico por voz + pantalla
=============================================
El usuario dice "Jarvis, hay un error" o "qué está fallando".
Jarvis toma screenshot, extrae el error, diagnóstica y da la solución hablada.
"""

import logging
from core.config import GROQ_API_KEY

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un experto en debugging de software. El usuario tiene un error y necesita ayuda.

Tu respuesta debe ser:
1. Una línea identificando el error (qué es exactamente)
2. La causa más probable (1 línea)
3. La solución exacta (máximo 3 pasos, directo al punto)

Sé conciso — esto se habla en voz alta, no se lee. Sin markdown, sin listas largas.
Si ves código en la pantalla, analiza el contexto completo, no solo el error."""


async def diagnose(error_text: str = "", use_screen: bool = True) -> str:
    """
    Diagnóstica un error usando pantalla y/o texto.
    Retorna explicación hablable (sin markdown, oraciones cortas).
    """
    context_parts = []

    # Capturar pantalla si está disponible
    if use_screen:
        try:
            from tools.screen_vision import look_at_screen
            screen_desc = await look_at_screen(
                "Describe exactamente qué error aparece en la pantalla. "
                "Incluye el mensaje de error completo, el archivo y línea si se ve, "
                "y cualquier contexto de código visible."
            )
            context_parts.append(f"Pantalla actual:\n{screen_desc}")
        except Exception as e:
            log.warning(f"[DEBUG] Screen vision falló: {e}")

    if error_text:
        context_parts.append(f"El usuario describió: {error_text}")

    if not context_parts:
        return "No pude capturar información del error. Describe qué está pasando."

    full_context = "\n\n".join(context_parts)

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_context},
            ],
            max_tokens=300,
            temperature=0.1,
        )

        result = response.choices[0].message.content or "No pude diagnosticar el error."
        log.info(f"[DEBUG] Diagnóstico: {result[:80]}...")
        return result

    except Exception as e:
        log.error(f"[DEBUG] Error: {e}")
        return f"Error en el diagnóstico: {str(e)[:100]}"


async def explain_code(use_screen: bool = True, code_text: str = "") -> str:
    """Explica el código visible en pantalla en términos simples."""
    if use_screen:
        try:
            from tools.screen_vision import look_at_screen
            screen = await look_at_screen("¿Qué hace este código? Describe su propósito y lógica principal.")
            return screen
        except Exception:
            pass

    if not code_text:
        return "No hay código que analizar. Comparte el código o asegúrate de tenerlo visible en pantalla."

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Explica en 3 oraciones simples qué hace este código:\n\n{code_text[:1500]}"
            }],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content or "No pude explicar el código."
    except Exception as e:
        return f"Error: {str(e)[:80]}"
