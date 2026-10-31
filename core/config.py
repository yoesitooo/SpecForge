"""
Core Config — SDD Ecosystem
============================
Única fuente de verdad para toda la configuración del sistema.
Lee desde .env via python-dotenv. CERO fallbacks hardcodeados.
Si una var es obligatoria y no existe, el sistema falla al arrancar (correcto).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


def _require(var: str) -> str:
    """Obtiene una variable de entorno obligatoria. Falla con mensaje claro si no existe."""
    value = os.environ.get(var)
    if not value:
        raise EnvironmentError(
            f"\n[CONFIG ERROR] Variable '{var}' no está definida.\n"
            f"Copia .env.example a .env y rellena con tus claves reales.\n"
            f"Ver instrucciones en .env.example"
        )
    return value


def _optional(var: str, default: str = "") -> str:
    return os.environ.get(var, default)


# =============================================================================
# ANTHROPIC / CLAUDE — Se usa vía CLI (claude --print), no API directa.
# ANTHROPIC_API_KEY es opcional. Si no está, ClaudeProvider usa el CLI.
# =============================================================================
ANTHROPIC_API_KEY      = _optional("ANTHROPIC_API_KEY")   # opcional — usamos CLI Pro
CLAUDE_DEFAULT_MODEL   = _optional("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-6")
CLAUDE_HEAVY_MODEL     = _optional("CLAUDE_HEAVY_MODEL",   "claude-opus-4-7")
CLAUDE_FAST_MODEL      = _optional("CLAUDE_FAST_MODEL",    "claude-haiku-4-5-20251001")


# =============================================================================
# GROQ — Inferencia gratuita ultrarrápida
# =============================================================================
GROQ_API_KEY           = _require("GROQ_API_KEY")
GROQ_BASE_URL          = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL     = _optional("GROQ_DEFAULT_MODEL",   "llama-3.3-70b-versatile")
GROQ_FAST_MODEL        = _optional("GROQ_FAST_MODEL",      "llama-3.1-8b-instant")
GROQ_VISION_MODEL      = _optional("GROQ_VISION_MODEL",    "llama-3.2-11b-vision-preview")
GROQ_LONG_CTX_MODEL    = _optional("GROQ_LONG_CTX_MODEL",  "mixtral-8x7b-32768")


# =============================================================================
# NVIDIA NIM — Modelos pesados
# =============================================================================
NVIDIA_HEAVY_KEY       = _optional("NVIDIA_HEAVY_KEY")
NVIDIA_FAST_KEY        = _optional("NVIDIA_FAST_KEY")
NVIDIA_VISION_KEY      = _optional("NVIDIA_VISION_KEY")
NVIDIA_BASE_URL        = "https://integrate.api.nvidia.com/v1"
NVIDIA_DEFAULT_MODEL   = _optional("NVIDIA_DEFAULT_MODEL",  "meta/llama-3.1-70b-instruct")
NVIDIA_CODE_MODEL      = _optional("NVIDIA_CODE_MODEL",     "qwen/qwen2.5-coder-32b-instruct")
NVIDIA_VISION_MODEL    = _optional("NVIDIA_VISION_MODEL",   "meta/llama-3.2-11b-vision-instruct")


# =============================================================================
# TELEGRAM
# =============================================================================
TELEGRAM_TOKEN          = _require("TELEGRAM_TOKEN")
TELEGRAM_ALLOWED_CHAT_ID = _optional("TELEGRAM_ALLOWED_CHAT_ID")


# =============================================================================
# SISTEMA
# =============================================================================
_raw_engram       = _optional("ENGRAM_DB_PATH",    str(ROOT_DIR / "memory" / "engram.db"))
ENGRAM_DB_PATH    = str((ROOT_DIR / _raw_engram).resolve()) if not Path(_raw_engram).is_absolute() else _raw_engram
WORKSPACES_PATH   = _optional("WORKSPACES_PATH",   str(ROOT_DIR / "workspaces"))
LOG_LEVEL         = _optional("LOG_LEVEL",         "INFO")
HTTP_PORT         = int(_optional("HTTP_PORT",     "8000"))
TRANSPORT_MODE    = _optional("TRANSPORT_MODE",    "telegram")

# Directorio de skills
SKILLS_DIR        = ROOT_DIR / "skills"


# =============================================================================
# TABLA DE MODELOS POR AGENTE DEL DAG
# Aquí se decide qué provider + modelo usa cada agente.
# Cambiar el modelo de un agente = cambiar UNA línea aquí.
# =============================================================================
AGENT_MODELS: dict[str, dict] = {
    # Fase 1 — Discovery (conversacional, necesita inteligencia)
    "discovery":        {"provider": "groq",      "model": GROQ_DEFAULT_MODEL,   "temperature": 0.8},

    # Fase 2 — Requirements (estructurado, PRD)
    "requirements":     {"provider": "groq",      "model": GROQ_DEFAULT_MODEL,   "temperature": 0.4},

    # Fase 3 — Architecture (contexto largo para ADRs)
    "architecture":     {"provider": "claude",    "model": CLAUDE_DEFAULT_MODEL, "temperature": 0.2},

    # Fase 4a — UX/UI (necesita visión)
    "ux_ui":            {"provider": "groq",      "model": GROQ_VISION_MODEL,    "temperature": 0.5},

    # Fase 4b — HU Writer (formato rígido Gherkin)
    "hu_writer":        {"provider": "groq",      "model": GROQ_FAST_MODEL,      "temperature": 0.15},

    # Fase 5 — Tech Spec (máxima estructura, tareas atómicas)
    "tech_spec":        {"provider": "groq",      "model": GROQ_FAST_MODEL,      "temperature": 0.05},

    # Fase 6a — Frontend (código React/TS)
    "frontend":         {"provider": "nvidia",    "model": NVIDIA_CODE_MODEL,    "temperature": 0.1},

    # Fase 6b — Backend (APIs complejas, necesita el modelo grande)
    "backend":          {"provider": "claude",    "model": CLAUDE_DEFAULT_MODEL, "temperature": 0.1},

    # Fase 6c — DB (schema SQL, muy determinístico)
    "db":               {"provider": "groq",      "model": GROQ_FAST_MODEL,      "temperature": 0.05},

    # Fase 7a — QA (tests según criterios de HU)
    "qa":               {"provider": "groq",      "model": "gemma2-9b-it",       "temperature": 0.1},

    # Fase 7b — Code Review (Sonnet es suficiente para auditoría; Opus gasta rate limits 5x más rápido)
    "code_review":      {"provider": "claude",    "model": CLAUDE_DEFAULT_MODEL, "temperature": 0.1},
}
