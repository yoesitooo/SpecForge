"""
DAG Definition — El grafo de fases como datos puros.
El executor lee esto. El orchestrator no hardcodea nada.

parallel_with: lista de fases que corren al mismo tiempo que esta.
barrier_after: si True, el ejecutor espera a que TODAS las fases del grupo terminen
               antes de avanzar a depends_next.
"""

from agents.phase1_discovery   import DiscoveryAgent
from agents.phase2_requirements import RequirementsAgent
from agents.phase3_architecture import ArchitectureAgent
from agents.phase4a_ux_ui      import UxUiAgent
from agents.phase4b_hu_writer  import HuWriterAgent
from agents.phase5_tech_spec   import TechSpecAgent
from agents.phase6a_frontend   import FrontendAgent
from agents.phase6b_backend    import BackendAgent
from agents.phase6c_db         import DbAgent
from agents.phase7a_qa         import QaAgent
from agents.phase7b_code_review import CodeReviewAgent

# Orden secuencial completo del DAG (para indexación y rollback)
PHASE_ORDER = [
    "discovery",
    "requirements",
    "architecture",
    "ux_ui",       # 4a — paralelo con hu_writer
    "hu_writer",   # 4b — paralelo con ux_ui
    "tech_spec",
    "frontend",    # 6a — paralelo con backend + db
    "backend",     # 6b — paralelo con frontend + db
    "db",          # 6c — paralelo con frontend + backend
    "qa",          # 7a — paralelo con code_review
    "code_review", # 7b — paralelo con qa
]

# Grupos paralelos por fase
# Fases en el mismo grupo corren con asyncio.gather
PARALLEL_GROUPS = [
    ["ux_ui", "hu_writer"],                # Fase 4 — paralelo
    ["frontend", "backend", "db"],          # Fase 6 — paralelo
    ["qa", "code_review"],                  # Fase 7 — paralelo
]

# Mapa de instancias de agentes
AGENT_MAP = {
    "discovery":    DiscoveryAgent(),
    "requirements": RequirementsAgent(),
    "architecture": ArchitectureAgent(),
    "ux_ui":        UxUiAgent(),
    "hu_writer":    HuWriterAgent(),
    "tech_spec":    TechSpecAgent(),
    "frontend":     FrontendAgent(),
    "backend":      BackendAgent(),
    "db":           DbAgent(),
    "qa":           QaAgent(),
    "code_review":  CodeReviewAgent(),
}

# Mensajes amigables para Telegram por fase
PHASE_LABELS = {
    "discovery":    "🔍 Fase 1 — Discovery",
    "requirements": "📋 Fase 2 — Requisitos (PRD)",
    "architecture": "🏗️ Fase 3 — Arquitectura",
    "ux_ui":        "🎨 Fase 4a — UX/UI Design System",
    "hu_writer":    "📝 Fase 4b — Historias de Usuario",
    "tech_spec":    "⚙️ Fase 5 — Tech Spec (Tareas)",
    "frontend":     "💻 Fase 6a — Frontend",
    "backend":      "🔧 Fase 6b — Backend",
    "db":           "🗄️ Fase 6c — Base de Datos",
    "qa":           "🧪 Fase 7a — QA & Tests",
    "code_review":  "🔬 Fase 7b — Code Review",
}


def get_parallel_group(phase: str) -> list[str] | None:
    """Retorna el grupo paralelo al que pertenece una fase, o None si es secuencial."""
    for group in PARALLEL_GROUPS:
        if phase in group:
            return group
    return None


def next_phase(current: str) -> str | None:
    """Retorna la siguiente fase a ejecutar después de current."""
    group = get_parallel_group(current)
    if group:
        # Si es parte de un grupo paralelo, el siguiente es el primero fuera del grupo
        last_in_group = group[-1]
        idx = PHASE_ORDER.index(last_in_group)
    else:
        idx = PHASE_ORDER.index(current)

    if idx + 1 < len(PHASE_ORDER):
        candidate = PHASE_ORDER[idx + 1]
        # Si el candidato está en un grupo, retornar el primero del grupo
        grp = get_parallel_group(candidate)
        return grp[0] if grp else candidate
    return None  # Proyecto completado
