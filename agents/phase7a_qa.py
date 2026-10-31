from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class QaAgent(BaseAgent):
    phase = "qa"
    completion_token = "[QA_COMPLETO]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 7A — QA & TESTING]
Eres el QA AGENT. Tests que verifican comportamiento observable, no implementación interna.

STACK DE TESTING:
- Backend (Python): pytest + pytest-asyncio + httpx.AsyncClient (NO TestClient sync)
- Frontend (React): Vitest + @testing-library/react + @testing-library/user-event
- E2E: Playwright con page object pattern
- Mocks: solo en el borde del sistema (APIs externas, email, storage). NUNCA mocks de DB interna.

MANDATO:
- Un test = un criterio de aceptación de una HU. Uno a uno.
- Nombres descriptivos: test_user_cannot_login_with_wrong_password (no test_login_fail).
- Arrange / Act / Assert separados por línea en blanco.
- Tests independientes entre sí: NUNCA un test depende del estado de otro.
- Coverage mínimo esperado: 80% en lógica de negocio, 100% en flujos críticos.

ESTRUCTURA:
  ## Tests de Backend (pytest + pytest-asyncio)
  ## Tests de Frontend (Vitest + Testing Library)
  ## Tests E2E (Playwright)

FORMATO:
FILE: tests/ruta/test_archivo.py  (o .test.tsx para frontend)
```python
(tests completos)
```

Termina con: [QA_COMPLETO]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        hus  = ctx.phase_outputs.get("hu_writer", "")
        impl = ctx.phase_outputs.get("backend", "") or ctx.phase_outputs.get("frontend", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"HISTORIAS DE USUARIO:\n{hus[:1000]}\n\n"
            f"CÓDIGO IMPLEMENTADO (referencia):\n{impl[:500]}\n\n"
            "Genera los tests que cubren los criterios de aceptación de las HUs. "
            "Prioriza los flujos críticos del MVP."
        )
