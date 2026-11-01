"""
Core Config — SpecForge
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
# PROVEEDORES DE MODELOS
# Las claves se leen directamente en providers/openai_compat.py (GEMINI_API_KEY,
# GROQ_API_KEY, CEREBRAS_API_KEY, OPENROUTER_API_KEY, GITHUB_MODELS_TOKEN,
# NVIDIA_API_KEY). Todas son opcionales: basta con una. Ver .env.example.
# GROQ_API_KEY también la usa Jarvis para la voz (Whisper).
# =============================================================================
GROQ_API_KEY = _optional("GROQ_API_KEY")


# =============================================================================
# TELEGRAM
# =============================================================================
TELEGRAM_TOKEN          = _optional("TELEGRAM_TOKEN")   # solo se exige con TRANSPORT_MODE=telegram (ver main.py)
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
# CADENAS DE PROVEEDORES (con respaldo automático)
# Cada agente pide un "nivel" (tier). Cada nivel es una lista ordenada de
# "proveedor:modelo". El router usa el primero que tenga credenciales y, si
# falla (límite de uso 429, caída, modelo retirado...), pasa al siguiente.
#
#   - claude / antigravity → tus SUSCRIPCIONES vía CLI (Claude Pro, cuenta de
#     Google / Google AI Pro). Se saltan solas si el CLI no está instalado.
#   - gemini, groq, cerebras, openrouter, github, nvidia → APIs con plan gratis.
#
# Se puede reemplazar cualquier nivel desde .env, por ejemplo:
#   SDD_CHAIN_SMART=gemini:gemini-3.8-flash,cerebras:gpt-oss-120b
# Un modelo vacío ("antigravity:") usa el modelo por defecto del CLI.
# =============================================================================
DEFAULT_CHAINS: dict[str, str] = {
    # Razonamiento: discovery, requisitos, arquitectura, revisión de código
    "smart":  "claude:sonnet,antigravity:,gemini:gemini-3.8-flash,"
              "groq:openai/gpt-oss-120b,groq:llama-3.3-70b-versatile",
    # Generación de código: frontend y backend
    "code":   "claude:sonnet,antigravity:,gemini:gemini-3.8-flash,groq:openai/gpt-oss-120b",
    # Tareas estructuradas y rápidas: historias de usuario, spec, BD, QA
    "fast":   "gemini:gemini-3.5-flash-lite,groq:llama-3.1-8b-instant,"
              "groq:openai/gpt-oss-20b,antigravity:",
    # Entrada con imágenes: UX/UI
    "vision": "gemini:gemini-3.8-flash,nvidia:meta/llama-3.2-11b-vision-instruct",
}


def parse_chain(spec: str) -> list[tuple[str, str]]:
    """'gemini:gemini-3.8-flash, groq:x' → [("gemini", "gemini-3.8-flash"), ("groq", "x")]"""
    chain = []
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        provider, _, model = item.partition(":")
        chain.append((provider.strip(), model.strip()))
    return chain


# Proveedores que usan una cuenta con sesión iniciada (suscripción) en vez de clave de API.
PROVEEDORES_CUENTA = {"claude", "antigravity"}

# SPECFORGE_MODO decide qué se usa:
#   auto    → tus cuentas primero (si el CLI tiene sesión) y las APIs gratis de respaldo
#   cuentas → solo tus cuentas (Claude Pro, Google AI Pro); sin APIs
#   gratis  → solo APIs con plan gratis; ignora los CLIs
MODOS = ("auto", "cuentas", "gratis")


def modo() -> str:
    valor = _optional("SPECFORGE_MODO", "auto").strip().lower()
    if valor not in MODOS:
        raise EnvironmentError(f"SPECFORGE_MODO='{valor}' no es válido. Opciones: {', '.join(MODOS)}")
    return valor


def chain_for(tier: str) -> list[tuple[str, str]]:
    spec = _optional(f"SDD_CHAIN_{tier.upper()}") or DEFAULT_CHAINS[tier]
    cadena = parse_chain(spec)
    m = modo()
    if m == "gratis":
        cadena = [(p, mod) for p, mod in cadena if p not in PROVEEDORES_CUENTA]
    elif m == "cuentas":
        cadena = [(p, mod) for p, mod in cadena if p in PROVEEDORES_CUENTA]
        # Los niveles sin CLI en su cadena (p. ej. visión) usan la cuenta de Google.
        cadena = cadena or [("antigravity", "")]
    return cadena


# =============================================================================
# NIVEL Y TEMPERATURA POR AGENTE DEL DAG
# Cambiar el modelo de un agente = cambiar su nivel aquí o la cadena en .env.
# =============================================================================
AGENT_MODELS: dict[str, dict] = {
    "discovery":    {"tier": "smart",  "temperature": 0.8},   # Fase 1 — conversacional
    "requirements": {"tier": "smart",  "temperature": 0.4},   # Fase 2 — PRD
    "architecture": {"tier": "smart",  "temperature": 0.2},   # Fase 3 — ADRs
    "ux_ui":        {"tier": "vision", "temperature": 0.5},   # Fase 4a — necesita visión
    "hu_writer":    {"tier": "fast",   "temperature": 0.15},  # Fase 4b — Gherkin
    "tech_spec":    {"tier": "fast",   "temperature": 0.05},  # Fase 5 — tareas atómicas
    "frontend":     {"tier": "code",   "temperature": 0.1},   # Fase 6a
    "backend":      {"tier": "code",   "temperature": 0.1},   # Fase 6b
    "db":           {"tier": "fast",   "temperature": 0.05},  # Fase 6c — SQL
    "qa":           {"tier": "fast",   "temperature": 0.1},   # Fase 7a
    "code_review":  {"tier": "smart",  "temperature": 0.1},   # Fase 7b
}
