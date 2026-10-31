"""
Claude Provider — Via CLI (usa tu suscripción Pro, sin costo de API)
=====================================================================
Llama al CLI `claude --print` como subprocess.
Requiere que el CLI esté instalado y autenticado:
  → claude auth login

Ventajas vs API directa:
  - Usa tu suscripción Pro existente (sin pagar por tokens)
  - Acceso a claude-sonnet-4-6 y claude-opus-4-7
  - Sin límite de tokens separado

Limitaciones:
  - Más lento que la API (overhead del CLI)
  - No soporta imágenes vía base64 (solo texto)
  - No retorna conteo de tokens
"""

import asyncio
import tempfile
import os
import re
from .base import BaseProvider, LLMResponse
from core.config import CLAUDE_DEFAULT_MODEL


class ClaudeProvider(BaseProvider):
    name = "claude"

    def is_available(self) -> bool:
        """Verifica que el CLI `claude` está en PATH."""
        import shutil
        return shutil.which("claude") is not None

    async def complete(
        self,
        system: str,
        user: str,
        model: str = CLAUDE_DEFAULT_MODEL,
        temperature: float = 0.2,   # noqa: CLI no expone temperatura directamente
        max_tokens: int = 8000,
        images: list[str] | None = None,  # noqa: CLI no soporta imágenes base64
    ) -> LLMResponse:
        # Construir el prompt completo como texto plano
        full_prompt = f"{system}\n\n---\n\n{user}"

        # Escribir en archivo temporal (evita límites de longitud en args CLI)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tf:
            tf.write(full_prompt)
            temp_path = tf.name

        try:
            # Construir comando (mismo en Windows y Linux — shell=True maneja la redirección)
            model_flag = f"--model {model} " if model != CLAUDE_DEFAULT_MODEL else ""
            max_flag = f"--max-tokens {max_tokens} "
            cmd = f'claude --print --output-format text {model_flag}{max_flag}< "{temp_path}"'

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            output = stdout.decode("utf-8", errors="replace").strip()
            error  = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode != 0 or not output:
                detail = error or f"Código de salida: {proc.returncode}"
                raise RuntimeError(
                    f"Claude CLI falló. ¿Estás logueado? Ejecuta: claude auth login\n{detail}"
                )

            # Limpiar secuencias ANSI que el CLI puede incluir
            clean = re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", output)

            return LLMResponse(
                content=clean,
                model=model,
                provider=self.name,
            )

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
