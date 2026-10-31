"""
NVIDIA NIM Provider — Modelos pesados
======================================
Usa las llaves NVIDIA_HEAVY_KEY / NVIDIA_FAST_KEY / NVIDIA_VISION_KEY
según la tarea. Interfaz compatible con OpenAI API.
Se usa principalmente para frontend_agent (código) y tareas donde
Groq y Claude no están disponibles o se necesita un modelo de código específico.
"""

import httpx
from .base import BaseProvider, LLMResponse
from core.config import (
    NVIDIA_HEAVY_KEY, NVIDIA_FAST_KEY, NVIDIA_VISION_KEY,
    NVIDIA_BASE_URL, NVIDIA_DEFAULT_MODEL,
)


class NvidiaProvider(BaseProvider):
    name = "nvidia"

    def is_available(self) -> bool:
        return bool(NVIDIA_HEAVY_KEY or NVIDIA_FAST_KEY)

    def _pick_key(self, model: str) -> str:
        """Elige la key correcta según el modelo solicitado."""
        if "vision" in model.lower() and NVIDIA_VISION_KEY:
            return NVIDIA_VISION_KEY
        if NVIDIA_HEAVY_KEY:
            return NVIDIA_HEAVY_KEY
        return NVIDIA_FAST_KEY or ""

    async def complete(
        self,
        system: str,
        user: str,
        model: str = NVIDIA_DEFAULT_MODEL,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        images: list[str] | None = None,
    ) -> LLMResponse:
        api_key = self._pick_key(model)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

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

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers=headers,
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
