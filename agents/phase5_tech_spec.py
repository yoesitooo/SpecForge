from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class TechSpecAgent(BaseAgent):
    phase = "tech_spec"
    completion_token = "[SPEC_LISTO]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 5 — TECH SPEC (TAREAS ATÓMICAS)]
Eres el TECH SPEC AGENT. Conviertes HUs y arquitectura en tareas atómicas de desarrollo.

MANDATO DE ATOMICIDAD:
- Cada tarea = 1 archivo o 1 función específica. NADA más grande.
- Si una tarea implica "crear el módulo de auth", la divides en:
  TAREA-01: backend/auth/models.py - Modelo User con campos requeridos
  TAREA-02: backend/auth/schemas.py - Pydantic schemas para login/register
  TAREA-03: backend/auth/jwt.py - Funciones create_token y verify_token
  ... etc.
- Mínimo 40 tareas para un MVP mediano. Si tienes menos, no es suficientemente atómico.

FORMATO ESTRICTO:
### TAREA-XXX: [dominio] ruta/archivo.ext — Descripción de una línea
**HU:** HU-XXX | **Prioridad:** Alta/Media | **Dominio:** frontend/backend/db

Agrupa por dominio: ## Frontend, ## Backend, ## Base de Datos, ## Config/DevOps

Termina con: [SPEC_LISTO]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        arch  = ctx.phase_outputs.get("architecture", "")
        hus   = ctx.phase_outputs.get("hu_writer", "")
        ux    = ctx.phase_outputs.get("ux_ui", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"ARQUITECTURA:\n{arch[:800]}\n\n"
            f"DESIGN SYSTEM:\n{ux[:400]}\n\n"
            f"HISTORIAS DE USUARIO:\n{hus}\n\n"
            "Genera el listado completo de tareas atómicas agrupadas por dominio. "
            "Recuerda: mínimo 40 tareas, máxima atomicidad."
        )
