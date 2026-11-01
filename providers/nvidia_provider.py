"""Compatibilidad: NVIDIA NIM ahora es un preset de OpenAICompatProvider."""

from .openai_compat import OpenAICompatProvider


class NvidiaProvider(OpenAICompatProvider):
    def __init__(self):
        super().__init__("nvidia")
