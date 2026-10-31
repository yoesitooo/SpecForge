"""
Skills Registry — Lazy Loading de Conocimiento
================================================
El sistema de skills inyecta contexto especializado en el prompt de un agente
SOLO cuando la tarea lo requiere (triggers por keywords).
Cargar todas las skills siempre = desperdicio de tokens.

Estructura del directorio:
  skills/
  ├── visual/        ← Estilos UI (glassmorphism, clay, bento, etc.)
  ├── backend/       ← Patrones de servidor (fastapi, auth, db)
  ├── frontend/      ← Patrones de cliente (react, threejs, animaciones)
  └── product/       ← Metodología de producto (discovery, requirements, ADRs)
"""

from pathlib import Path
from typing import Optional

SKILLS_ROOT = Path(__file__).parent


# =============================================================================
# TRIGGER MAP — keywords → archivo de skill
# Cuando un agente encuentra estas palabras en su tarea, carga la skill.
# =============================================================================
TRIGGER_MAP: dict[str, str] = {
    # ── Visuales ──────────────────────────────────────────────────────────
    "glassmorphism":     "visual/skill_glassmorphism.md",
    "glass":             "visual/skill_glassmorphism.md",
    "vidrio":            "visual/skill_glassmorphism.md",
    "frosted":           "visual/skill_glassmorphism.md",
    "blur card":         "visual/skill_glassmorphism.md",

    "neomorphism":       "visual/skill_neomorphism.md",
    "neumorphism":       "visual/skill_neomorphism.md",
    "relieve":           "visual/skill_neomorphism.md",
    "soft ui":           "visual/skill_neomorphism.md",

    "claymorphism":      "visual/skill_claymorphism.md",
    "clay":              "visual/skill_claymorphism.md",
    "arcilla":           "visual/skill_claymorphism.md",
    "inflable":          "visual/skill_claymorphism.md",

    "aurora":            "visual/skill_aurora_ui.md",
    "aurora ui":         "visual/skill_aurora_ui.md",
    "mesh gradient":     "visual/skill_aurora_ui.md",
    "blob":              "visual/skill_aurora_ui.md",
    "gradient fluid":    "visual/skill_aurora_ui.md",

    "cyberpunk":         "visual/skill_cyberpunk.md",
    "synthwave":         "visual/skill_cyberpunk.md",
    "neon":              "visual/skill_cyberpunk.md",
    "glitch":            "visual/skill_cyberpunk.md",
    "terminal ui":       "visual/skill_cyberpunk.md",
    "hacker":            "visual/skill_cyberpunk.md",

    "brutalism":         "visual/skill_brutalism.md",
    "brutalismo":        "visual/skill_brutalism.md",
    "neo brutal":        "visual/skill_brutalism.md",
    "flat shadow":       "visual/skill_brutalism.md",
    "sombra plana":      "visual/skill_brutalism.md",

    "bento":             "visual/skill_bento_grid.md",
    "bento grid":        "visual/skill_bento_grid.md",
    "widget grid":       "visual/skill_bento_grid.md",
    "dashboard layout":  "visual/skill_bento_grid.md",
    "mosaic":            "visual/skill_bento_grid.md",

    "dark premium":      "visual/skill_dark_premium.md",
    "dark luxury":       "visual/skill_dark_premium.md",
    "dark mode":         "visual/skill_dark_premium.md",
    "dark saas":         "visual/skill_dark_premium.md",
    "minimalismo oscuro":"visual/skill_dark_premium.md",

    # ── UI/UX General ─────────────────────────────────────────────────────
    "ui ux":             "skill_ui_ux_pro_max.md",
    "premium ui":        "skill_ui_ux_pro_max.md",
    "design system":     "skill_ui_ux_pro_max.md",
    "glassmorphism ui":  "visual/skill_glassmorphism.md",
    "framer motion":     "skill_ui_ux_pro_max.md",
    "shadcn":            "skill_ui_ux_pro_max.md",
    "radix":             "skill_ui_ux_pro_max.md",
    "zustand":           "skill_ui_ux_pro_max.md",
    "tanstack":          "skill_ui_ux_pro_max.md",
    "next.js":           "skill_ui_ux_pro_max.md",
    "nextjs":            "skill_ui_ux_pro_max.md",

    # ── Backend ───────────────────────────────────────────────────────────
    "fastapi":           "skill_fastapi.md",
    "sqlalchemy":        "skill_fastapi.md",
    "pydantic":          "skill_fastapi.md",
    "python backend":    "skill_fastapi.md",

    "backend":           "skill_backend_pro.md",
    "api rest":          "skill_backend_pro.md",
    "microservicio":     "skill_backend_pro.md",

    "auth":              "skill_security.md",
    "jwt":               "skill_security.md",
    "autenticación":     "skill_security.md",
    "seguridad":         "skill_security.md",

    # ── Frontend ──────────────────────────────────────────────────────────
    "three.js":          "skill_threejs_pro.md",
    "threejs":           "skill_threejs_pro.md",
    "3d web":            "skill_threejs_pro.md",
    "r3f":               "skill_threejs_pro.md",
    "react three fiber": "skill_threejs_pro.md",

    "seo":               "skill_page_optimizer.md",
    "performance":       "skill_page_optimizer.md",
    "core web vitals":   "skill_page_optimizer.md",
    "lighthouse":        "skill_page_optimizer.md",

    # ── Producto / SaaS ───────────────────────────────────────────────────
    "discovery":         "saas/skill_saas_discovery.md",
    "problem framing":   "saas/skill_saas_discovery.md",
    "validar idea":      "saas/skill_saas_discovery.md",

    "requisitos":        "saas/skill_saas_requirements.md",
    "requirements":      "saas/skill_saas_requirements.md",
    "prd":               "saas/skill_saas_requirements.md",
    "historias de usuario": "saas/skill_saas_requirements.md",

    "arquitectura saas": "saas/skill_saas_architecture.md",
    "adr":               "saas/skill_saas_architecture.md",
    "stack":             "saas/skill_saas_architecture.md",
    "modelo de datos":   "saas/skill_saas_architecture.md",

    "saas ux":           "saas/skill_saas_uxui.md",
    "onboarding":        "saas/skill_saas_uxui.md",
    "dashboard":         "saas/skill_saas_uxui.md",

    # ── Nuevos tipos de proyecto ──────────────────────────────────────────
    "telegram bot":      "skill_telegram_bot.md",
    "aiogram":           "skill_telegram_bot.md",
    "telegram":          "skill_telegram_bot.md",
    "bot telegram":      "skill_telegram_bot.md",

    "agente ia":         "skill_ai_agent.md",
    "ai agent":          "skill_ai_agent.md",
    "pipeline llm":      "skill_ai_agent.md",
    "orquestador":       "skill_ai_agent.md",
    "tool calling":      "skill_ai_agent.md",
    "rag":               "skill_ai_agent.md",

    "api only":          "skill_api_only.md",
    "microservice":      "skill_api_only.md",
    "sin frontend":      "skill_api_only.md",
    "api pura":          "skill_api_only.md",
    "rest api":          "skill_api_only.md",

    "cli tool":          "skill_cli_tool.md",
    "typer":             "skill_cli_tool.md",
    "herramienta cli":   "skill_cli_tool.md",
    "línea de comandos": "skill_cli_tool.md",
}


def detect(task_description: str) -> list[str]:
    """Detecta qué skills son relevantes para una descripción de tarea."""
    task_lower = task_description.lower()
    found: list[str] = []
    for trigger, skill_path in TRIGGER_MAP.items():
        if trigger in task_lower and skill_path not in found:
            found.append(skill_path)
    return found


def load(skill_path: str) -> Optional[str]:
    """Carga el contenido de una skill. Retorna None si no existe."""
    full_path = SKILLS_ROOT / skill_path
    if full_path.exists():
        return full_path.read_text(encoding="utf-8")
    return None


def inject(task_description: str) -> str:
    """
    Detecta y carga las skills relevantes para una tarea.
    Retorna el contenido concatenado listo para inyectar en el prompt.
    Si no hay skills relevantes, retorna string vacío.
    """
    activated = detect(task_description)
    if not activated:
        return ""

    parts = ["\n\n=== CONOCIMIENTO ESPECIALIZADO ACTIVADO ==="]
    for skill_path in activated:
        content = load(skill_path)
        if content:
            parts.append(f"\n--- {skill_path} ---\n{content}")

    print(f"[SKILLS] Skills activadas: {activated}")
    return "\n".join(parts)


def list_all() -> list[str]:
    """Lista todos los archivos .md disponibles como skills."""
    return [
        str(p.relative_to(SKILLS_ROOT))
        for p in SKILLS_ROOT.rglob("*.md")
    ]
