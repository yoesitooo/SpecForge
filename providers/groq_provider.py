"""
Groq Provider — Inferencia ultrarrápida gratuita
=================================================
Usa la API de Groq (compatible con OpenAI SDK).
FREE TIER: 30 req/min, 6000 tokens/min.
Se usa para el 70% del trabajo: discovery, requirements, hu_writer, tech_spec, qa, db.
"""

import httpx
from .base import BaseProvider, LLMResponse
from core.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_DEFAULT_MODEL


class GroqProvider(BaseProvider):
    name = "groq"

    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

    def is_available(self) -> bool:
        return bool(GROQ_API_KEY)

    async def complete(
        self,
        system: str,
        user: str,
        model: str = GROQ_DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        images: list[str] | None = None,
    ) -> LLMResponse:
        # Groq soporta visión en llama-3.2-11b-vision-preview
        if images:
            user_content = [
                *[
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}
                    for img in images
                ],
                {"type": "text", "text": user},
            ]
        else:
            user_content = user

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=self._headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=model,
            provider=self.name,
            input_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            output_tokens=data.get("usage", {}).get("completion_tokens", 0),
        )
