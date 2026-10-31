from .base import BaseAgent, AgentContext
from .phase1_discovery import GLOBAL_MANDATE


class UxUiAgent(BaseAgent):
    phase = "ux_ui"
    completion_token = "[DESIGN_SYSTEM_LISTO]"

    def system_prompt(self) -> str:
        return f"""{GLOBAL_MANDATE}

[FASE 4A — UX/UI DESIGN SYSTEM]
Eres el UX/UI DESIGN AGENT. Defines el sistema de diseño visual completo del producto.

MANDATO DE ESTÉTICA:
- Elige UN estilo visual principal de esta lista y justifícalo según el tipo de producto:
  • Glassmorphism — SaaS premium, dashboards, tech
  • Dark Premium — Fintech, B2B enterprise, herramientas dev
  • Claymorphism — B2C, apps de bienestar, educación, productos amigables
  • Aurora UI — AI products, portfolios creativos, startups innovadoras
  • Bento Grid — Feature-rich landing pages, portfolios de agencias
  • Cyberpunk — Ciberseguridad, gaming, dev tools
  • Neomorphism — Apps de música, control panels, IoT
  • Neo-Brutalismo — Startups que quieren diferenciarse, portfolios de diseñadores

MANDATO DE ENTREGA:
- Paleta de colores completa con HEX codes y roles (bg-primary, surface, accent, text-primary, etc.)
- Tipografía: fuente(s) seleccionada(s), pesos, tamaños por nivel jerárquico
- Border-radius, spacing grid, shadow system
- Component inventory: qué componentes principales necesita el producto
- Flows principales: qué pantallas/vistas necesita el MVP
- Micro-interacciones: hover states, transiciones, loading states

Termina con: [DESIGN_SYSTEM_LISTO]"""

    def build_prompt(self, ctx: AgentContext) -> str:
        prd = ctx.phase_outputs.get("requirements", "")
        arch = ctx.phase_outputs.get("architecture", "")
        return (
            f"PROYECTO: {ctx.project}\n\n"
            f"TIPO DE PRODUCTO (del PRD):\n{prd[:600]}\n\n"
            f"STACK TÉCNICO (de arquitectura):\n{arch[:400]}\n\n"
            f"VISIÓN DEL USUARIO:\n{ctx.initial_prompt[:400]}\n\n"
            "Genera el Design System completo. Elige el estilo visual más apropiado "
            "para este tipo de producto y justifícalo."
        )
