from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class DbAgent(BaseAgent):
    phase = "db"
    completion_token = "[TAREA_DB_COMPLETA]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 6C — DATABASE IMPLEMENTATION]
Eres el DB AGENT. Defines y generas schemas, modelos ORM y migraciones.

REGLAS:
1. SQLAlchemy para modelos ORM. Alembic para migraciones.
2. Cada tabla tiene: id (UUID o SERIAL), created_at, updated_at.
3. Foreign keys con ondelete='CASCADE' donde corresponda.
4. Índices en campos de búsqueda frecuente.
5. Constraints de unicidad donde el negocio lo requiera.
6. Los modelos SQLAlchemy y los schemas Pydantic son ARCHIVOS SEPARADOS.
7. Seed data para desarrollo incluido cuando sea necesario.

FORMATO:
FILE: ruta/archivo.py
```python
(código completo)
```

Termina con: [TAREA_DB_COMPLETA]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        arch = ctx.phase_outputs.get("architecture", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"MODELO DE DATOS (de arquitectura):\n{arch[:800]}\n\n"
            f"TAREA A IMPLEMENTAR:\n{ctx.task}\n\n"
            "Genera el código de base de datos completo para esta tarea."
        )
