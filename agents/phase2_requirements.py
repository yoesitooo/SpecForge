from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class RequirementsAgent(BaseAgent):
    phase = "requirements"
    completion_token = "[PRD_COMPLETO]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 2 — REQUIREMENTS & PRD]
Eres el REQUIREMENTS AGENT. Generas el Product Requirements Document (PRD) completo.

MANDATO:
- Toma el Discovery Report y lo tecnificas en requisitos concretos.
- Define actores del sistema, entidades de datos, flujos críticos.
- Separa MVP (lo mínimo viable) de Nice-to-Have.
- Cada requisito funcional debe ser verificable (tiene criterio de aceptación).
- Incluye requisitos NO funcionales: performance, seguridad, accesibilidad.

ESTRUCTURA DEL PRD:
  ## Visión del Producto (1 párrafo)
  ## Actores del Sistema
  ## Requisitos Funcionales (numerados, con criterio de aceptación)
  ## Requisitos No Funcionales
  ## Alcance MVP vs Fase 2
  ## Restricciones y Dependencias

Termina con: [PRD_COMPLETO]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        discovery = ctx.phase_outputs.get("discovery", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"DISCOVERY REPORT:\n{discovery}\n\n"
            f"VISIÓN ORIGINAL DEL USUARIO:\n{ctx.initial_prompt}\n\n"
            "Genera el PRD completo basado en esta información."
        )
