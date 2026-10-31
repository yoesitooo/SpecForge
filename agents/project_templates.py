"""
Project Templates — contexto pre-cargado por tipo de proyecto
=============================================================
Cada template define:
  - questions: preguntas críticas si el usuario no las mencionó
  - tech_stack: stack recomendado para ese tipo
  - agent_hints: contexto extra inyectado en los agentes del DAG
  - keywords: palabras clave para auto-detectar el tipo
"""

from typing import TypedDict


class ProjectTemplate(TypedDict):
    label: str
    keywords: list[str]
    questions: list[str]
    tech_stack: str
    agent_hints: str


TEMPLATES: dict[str, ProjectTemplate] = {

    "web_saas": {
        "label": "SaaS Web",
        "keywords": [
            "saas", "suscripción", "usuarios", "dashboard", "panel",
            "login", "registro", "membresía", "plan", "facturación",
        ],
        "questions": [
            "¿Cuántos tipos de usuario hay (admin, cliente, etc.) y qué puede hacer cada uno?",
            "¿Habrá planes de pago o suscripción? ¿Cuáles?",
            "¿Qué es lo primero que hace un usuario al entrar al dashboard?",
            "¿Necesitas notificaciones por email o en tiempo real?",
        ],
        "tech_stack": "Next.js 15 App Router + FastAPI + PostgreSQL + Auth.js v5 + Stripe",
        "agent_hints": (
            "Es un SaaS multi-tenant. Implementa roles de usuario desde el inicio. "
            "Auth con sesiones httpOnly (nunca JWT en localStorage). "
            "El dashboard principal debe mostrar las métricas más importantes del usuario. "
            "Diseño premium glassmorphism con modo oscuro."
        ),
    },

    "landing": {
        "label": "Landing Page",
        "keywords": [
            "landing", "página", "presentación", "marketing", "vitrina",
            "portafolio", "agencia", "negocio", "empresa", "servicios",
        ],
        "questions": [
            "¿Cuál es el objetivo principal: captar leads, vender algo, o presentar el negocio?",
            "¿Tienes un CTA principal? (ej: agendar cita, comprar, contactar)",
            "¿Necesita formulario de contacto o integración con email (Resend/Mailchimp)?",
        ],
        "tech_stack": "Next.js 15 + Tailwind v4 + Framer Motion 11 + Resend (email)",
        "agent_hints": (
            "Landing page de alto impacto visual. Glassmorphism, animaciones suaves, "
            "above-the-fold con propuesta de valor clara. CTA visible en todo momento. "
            "Sin backend complejo — solo formulario de contacto. "
            "Optimizada para conversión y SEO on-page."
        ),
    },

    "ecommerce": {
        "label": "E-commerce",
        "keywords": [
            "tienda", "venta", "producto", "carrito", "pago", "shop",
            "catálogo", "inventario", "precio", "checkout", "compra",
        ],
        "questions": [
            "¿Cuántos productos aproximadamente? ¿Tienen variantes (talla, color)?",
            "¿Qué pasarela de pago? (Stripe, PayU, Mercado Pago, etc.)",
            "¿Necesitas gestión de inventario o solo vitrina con pedidos?",
            "¿Un solo vendedor o marketplace (múltiples vendedores)?",
        ],
        "tech_stack": "Next.js 15 + FastAPI + PostgreSQL + Stripe/MercadoPago + Cloudflare R2 (imágenes)",
        "agent_hints": (
            "E-commerce completo. Catálogo con filtros, carrito persistente en DB (no localStorage), "
            "checkout en un paso, manejo de stock. "
            "Imágenes optimizadas con next/image. SEO de producto con metadata dinámica. "
            "Admin panel para gestionar productos y pedidos."
        ),
    },

    "api_service": {
        "label": "API / Microservicio",
        "keywords": [
            "api", "microservicio", "backend", "rest", "endpoint",
            "integración", "webhook", "servicio", "sin frontend",
        ],
        "questions": [
            "¿Qué recursos o entidades principales maneja la API? (ej: usuarios, pedidos, eventos)",
            "¿Quién consume esta API? ¿Otro sistema, una app móvil, o un frontend separado?",
            "¿Necesita autenticación? ¿API keys, JWT, o OAuth?",
        ],
        "tech_stack": "FastAPI 0.115+ + PostgreSQL + SQLAlchemy 2.x async + Pydantic v2 + Docker",
        "agent_hints": (
            "API pura sin frontend. Documentación automática con OpenAPI/Swagger. "
            "Rate limiting con slowapi. Auth por API key o JWT en headers. "
            "Paginación cursor-based en listados grandes. "
            "Estructura: routers/ + services/ + models/ + schemas/. "
            "Sin agente de frontend — solo backend y base de datos."
        ),
    },

    "telegram_bot": {
        "label": "Bot de Telegram",
        "keywords": [
            "telegram", "bot", "comando", "handler", "mensaje", "aiogram",
            "automatización", "notificar", "alertas", "chat bot",
        ],
        "questions": [
            "¿Qué comandos principales tendrá el bot? (ej: /start, /ayuda, /pedido)",
            "¿El bot interactúa con una base de datos o solo procesa y responde?",
            "¿Necesita teclados inline, menús, o flujos multi-paso (FSM)?",
        ],
        "tech_stack": "Python + aiogram 3.x + SQLite/PostgreSQL + Redis (FSM) + Docker",
        "agent_hints": (
            "Bot de Telegram con aiogram 3.x. Arquitectura: handlers/ + states/ + services/. "
            "FSM para flujos conversacionales multi-paso. "
            "InlineKeyboard para menús. CallbackQuery handlers. "
            "Manejo de errores y mensajes de fallback. "
            "El 'frontend' son los handlers de Telegram, no hay web."
        ),
    },

    "discord_bot": {
        "label": "Bot de Discord",
        "keywords": ["discord", "bot discord", "servidor", "slash command", "discord.py"],
        "questions": [
            "¿Qué comandos slash principales tendrá?",
            "¿Necesita moderación automática, música, o es un bot de utilidad?",
            "¿Interactúa con alguna API externa?",
        ],
        "tech_stack": "discord.py 2.x + PostgreSQL + Docker",
        "agent_hints": (
            "Bot de Discord con discord.py 2.x. Slash commands con app_commands. "
            "Cogs para organizar comandos por categoría. "
            "Embeds para respuestas visuales. Manejo de permisos por rol."
        ),
    },

    "ai_agent": {
        "label": "Sistema de Agentes IA",
        "keywords": [
            "agente", "ia", "llm", "pipeline", "orquestador", "workflow",
            "chain", "rag", "embeddings", "langchain", "herramientas", "tools",
        ],
        "questions": [
            "¿Qué problema resuelve el agente? ¿Qué decisiones toma autónomamente?",
            "¿Qué herramientas/fuentes de datos necesita? (web, DB, APIs externas)",
            "¿Necesita memoria persistente entre conversaciones?",
            "¿Es un solo agente o múltiples agentes especializados?",
        ],
        "tech_stack": "Python + FastAPI + Groq/Anthropic SDK + SQLite/Qdrant (vector) + Docker",
        "agent_hints": (
            "Sistema de agentes IA. Arquitectura: providers/ + agents/ + tools/ + memory/. "
            "Tool calling con function definitions. Memoria en SQLite o vector DB. "
            "Manejo de rate limits y fallbacks entre providers. "
            "Logging estructurado de decisiones del agente para debugging. "
            "HTTP API para exponer el agente (FastAPI + WebSocket para streaming)."
        ),
    },

    "data_pipeline": {
        "label": "Pipeline de Datos",
        "keywords": [
            "datos", "etl", "scraper", "crawler", "pipeline", "procesar",
            "csv", "excel", "análisis", "reporte", "automatizar extracción",
        ],
        "questions": [
            "¿De dónde vienen los datos? (web scraping, API, archivos, DB)",
            "¿Qué transformaciones necesitan? ¿Dónde se guardan los resultados?",
            "¿Corre una vez o se programa periódicamente?",
        ],
        "tech_stack": "Python + Playwright/httpx (scraping) + Pandas/Polars + PostgreSQL + APScheduler",
        "agent_hints": (
            "Pipeline de datos. Estructura: extractors/ + transformers/ + loaders/. "
            "Playwright para scraping dinámico, httpx para APIs. "
            "Polars para transformaciones rápidas. Logging de cada paso del pipeline. "
            "Manejo de errores con reintentos (tenacity). "
            "Sin frontend complejo — máximo un pequeño dashboard de monitoreo."
        ),
    },

    "cli_tool": {
        "label": "Herramienta CLI",
        "keywords": [
            "cli", "terminal", "comando", "herramienta", "script", "typer",
            "click", "línea de comandos", "automatizar", "util",
        ],
        "questions": [
            "¿Qué comandos principales tendrá? ¿Qué argumentos reciben?",
            "¿Se instala como paquete pip o es un script suelto?",
            "¿Necesita configuración persistente (archivo config)?",
        ],
        "tech_stack": "Python + Typer + Rich (output) + click + pyproject.toml (packaging)",
        "agent_hints": (
            "CLI con Typer + Rich para output colorido. "
            "Estructura: cli.py (comandos) + core/ (lógica) + config.py. "
            "Manejo de errores con mensajes amigables. "
            "Autocompletion con Typer. Instalable via pip. "
            "No hay frontend ni backend web — solo la herramienta."
        ),
    },

    "mobile_app": {
        "label": "App Móvil",
        "keywords": [
            "móvil", "celular", "android", "ios", "react native",
            "flutter", "app", "nativa", "play store", "app store",
        ],
        "questions": [
            "¿Android, iOS, o ambas? ¿React Native o Flutter?",
            "¿Qué hace la app en términos simples — cuáles son las 3 pantallas principales?",
            "¿Necesita notificaciones push? ¿Login con Google/Apple?",
        ],
        "tech_stack": "React Native (Expo) + FastAPI backend + PostgreSQL + Firebase (push notifs)",
        "agent_hints": (
            "App móvil con React Native + Expo. "
            "Navegación con expo-router (file-based). "
            "Zustand para estado, TanStack Query para datos. "
            "Backend FastAPI separado. Auth con expo-auth-session. "
            "UI components de react-native-paper o NativeWind."
        ),
    },

    "desktop_app": {
        "label": "App de Escritorio",
        "keywords": [
            "escritorio", "desktop", "windows", "mac", "electron",
            "tauri", "aplicación local", "offline",
        ],
        "questions": [
            "¿Windows, Mac, Linux, o multiplataforma?",
            "¿Necesita acceso al sistema de archivos o recursos del sistema?",
            "¿Tauri (más ligero, Rust) o Electron (más compatible, Node)?",
        ],
        "tech_stack": "Tauri v2 + React 19 + Tailwind v4 + SQLite local",
        "agent_hints": (
            "App de escritorio con Tauri v2 + React frontend. "
            "Comandos Rust para operaciones del sistema. "
            "SQLite local con tauri-plugin-sql. "
            "Sistema de archivos con tauri-plugin-fs. "
            "Auto-updater incluido."
        ),
    },

    "dashboard": {
        "label": "Dashboard / Admin Panel",
        "keywords": [
            "dashboard", "admin", "panel", "métricas", "estadísticas",
            "reporte", "monitoreo", "visualización", "gráficas", "tablas",
        ],
        "questions": [
            "¿Qué datos se visualizan? ¿De dónde vienen (DB propia, API externa)?",
            "¿Quién lo usa: solo admins o también clientes?",
            "¿Necesita exportar reportes (PDF, Excel)?",
        ],
        "tech_stack": "Next.js 15 + Recharts/Tremor + FastAPI + PostgreSQL + Auth.js",
        "agent_hints": (
            "Dashboard de datos con gráficas interactivas. "
            "Recharts o Tremor para visualizaciones. "
            "Tablas con TanStack Table (paginación, filtros, sorting server-side). "
            "Exportación a CSV/Excel con exceljs. "
            "Modo oscuro por defecto, diseño glassmorphism."
        ),
    },
}


def detect_type(description: str) -> str:
    """Detecta el tipo de proyecto por palabras clave. Retorna el tipo más probable."""
    desc_lower = description.lower()
    scores: dict[str, int] = {}

    for ptype, template in TEMPLATES.items():
        score = sum(1 for kw in template["keywords"] if kw in desc_lower)
        if score > 0:
            scores[ptype] = score

    if not scores:
        return "web_saas"  # Default más común

    return max(scores, key=lambda k: scores[k])


def get_template(project_type: str) -> ProjectTemplate:
    return TEMPLATES.get(project_type, TEMPLATES["web_saas"])


TYPE_LABELS = {k: v["label"] for k, v in TEMPLATES.items()}
