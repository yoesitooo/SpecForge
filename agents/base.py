"""
BaseAgent — Contrato que todos los agentes implementan.

Ciclo de vida de un agente:
  1. NACIMIENTO  — el orquestador lo instancia con el contexto del proyecto
  2. EJECUCIÓN   — build_prompt() + router.call_chain() (con respaldo entre proveedores)
  3. REPORTE     — el output se guarda en Engram y en session_store
  4. MUERTE      — el objeto no persiste entre llamadas

Cada agente tiene una sola responsabilidad (SRP).
El orquestador nunca lee los prompts internos; solo llama a run().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from providers.base import LLMResponse
from providers import router as llm
from memory import engram
from skills import registry as skills
from core.config import AGENT_MODELS, chain_for


@dataclass
class AgentContext:
    """Todo lo que un agente necesita saber para ejecutar su tarea."""
    project: str
    chat_id: str
    phase_outputs: dict = field(default_factory=dict)   # outputs de fases previas
    initial_prompt: str = ""                             # visión original del usuario
    task: str = ""                                       # tarea específica (para implementador)
    extra: dict = field(default_factory=dict)            # datos adicionales libres


@dataclass
class AgentOutput:
    phase: str
    content: str
    completed: bool          # True si el completion_token está presente
    completion_token: str = ""


class BaseAgent(ABC):
    phase: str = ""                  # ID del nodo en el DAG ("discovery", "spec", etc.)
    completion_token: str = ""       # Token que marca que el agente terminó

    @abstractmethod
    def system_prompt(self) -> str:
        """Prompt del sistema que define el rol y mandatos del agente."""
        ...

    @abstractmethod
    def build_prompt(self, ctx: AgentContext) -> str:
        """Construye el prompt de usuario con el contexto del proyecto."""
        ...

    async def run(self, ctx: AgentContext) -> AgentOutput:
        cfg   = AGENT_MODELS[self.phase]
        chain = chain_for(cfg["tier"])
        temp  = cfg["temperature"]

        system = self.system_prompt()
        user   = self.build_prompt(ctx)

        # Inyectar skills relevantes según el contenido del prompt
        skill_ctx = skills.inject(user + " " + ctx.initial_prompt)
        if skill_ctx:
            user = user + skill_ctx

        # Inyectar memoria de Engram (contexto quirúrgico del proyecto)
        memory_ctx = engram.retrieve_context(ctx.project, limit=10)
        if "No hay memoria" not in memory_ctx:
            user = f"{memory_ctx}\n\n---\n\n{user}"

        response: LLMResponse = await llm.call_chain(
            chain,
            system=system,
            user=user,
            temperature=temp,
        )

        content = response.content
        completed = not self.completion_token or self.completion_token in content

        # Guardar en Engram
        summary = content[-400:] if len(content) > 400 else content
        engram.save_signal(ctx.project, self.phase, "summary",
                           f"Fase {self.phase} completada. Resumen: {summary}")
        if not completed:
            engram.save_signal(ctx.project, self.phase, "error",
                               f"Token '{self.completion_token}' no encontrado — posible truncado")

        return AgentOutput(
            phase=self.phase,
            content=content,
            completed=completed,
            completion_token=self.completion_token,
        )
