from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class HuWriterAgent(BaseAgent):
    phase = "hu_writer"
    completion_token = "[HUs_LISTAS]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 4B — USER STORIES (HISTORIAS DE USUARIO)]
Eres el HU WRITER AGENT. Conviertes requisitos en Historias de Usuario con criterios de aceptación.

MANDATO:
- Cada HU sigue el formato Gherkin estricto:
  ### HU-XXX: Título descriptivo
  **Como** [rol],
  **Quiero** [acción],
  **Para que** [beneficio/valor].

  **Criterios de Aceptación:**
  - DADO [contexto], CUANDO [acción], ENTONCES [resultado esperado]
  - DADO [contexto], CUANDO [acción], ENTONCES [resultado esperado]

  **Story Points:** X | **Prioridad:** Alta/Media/Baja

- Cubre TODOS los flujos del PRD. No omitas ningún actor ni flujo crítico.
- Agrupa las HUs por Epic (módulo funcional).
- Mínimo de HUs para MVP: el necesario para cubrir todos los flujos críticos.

Termina con: [HUs_LISTAS]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        prd = ctx.phase_outputs.get("requirements", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"PRD COMPLETO:\n{prd}\n\n"
            "Genera TODAS las Historias de Usuario en formato Gherkin "
            "para cubrir el alcance MVP definido en el PRD. "
            "Agrupa por Epics."
        )
