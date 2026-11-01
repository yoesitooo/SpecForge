"""Compatibilidad: Groq ahora es un preset de OpenAICompatProvider."""

from .openai_compat import OpenAICompatProvider


class GroqProvider(OpenAICompatProvider):
    def __init__(self):
        super().__init__("groq")
