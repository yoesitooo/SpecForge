# SDD Ecosystem

**Sistema multi-agente que convierte una descripción en lenguaje natural en un proyecto de software funcional.**

> **🇬🇧 In English — at a glance**
>
> SDD (Spec-Driven Development) Ecosystem is a Python multi-agent orchestrator: you describe a project in plain language and **11 specialised LLM agents** take it through discovery → requirements → architecture → UX/UI + user stories → tech spec → frontend + backend + DB → QA + code review.
>
> | Design point | Where to look |
> |---|---|
> | The DAG is **pure data**; the executor reads it, and phases in the same group run in parallel with `asyncio.gather` (phases 4, 6 and 7) | [`orchestrator/dag.py`](./orchestrator/dag.py) · [`orchestrator/executor.py`](./orchestrator/executor.py) |
> | **Multi-provider router with automatic fallback** — each phase asks for a tier; the router walks a chain of providers and moves on when one is missing a key, hits its free-tier limit (429) or fails. Runs on free tiers only (Gemini, Groq, Cerebras, OpenRouter, GitHub Models, NVIDIA) or on personal subscriptions through their CLIs (Antigravity CLI for Google AI Pro, Claude Code) | [`providers/`](./providers) · [`core/config.py`](./core/config.py) |
> | **Tested** with pytest (HTTP and CLIs mocked) in GitHub Actions | [`tests/`](./tests) |
> | **Persistent memory** in SQLite FTS5: decisions, errors and DAG state survive restarts; any phase can be rolled back | [`memory/engram.py`](./memory/engram.py) |
> | Pluggable **transports**: terminal, Telegram bot, voice (Whisper + TTS) and web (FastAPI + WebSockets) | [`transports/`](./transports) |
> | Prompt **skills** as Markdown files loaded on demand | [`skills/`](./skills) |
>
> Example output: [VexoTry](https://github.com/yoesitooo/VexoTry) was generated with an early version of this pipeline and then optimized by hand.

---

Tiene dos modos de uso:
1. **Jarvis** — asistente de IA por voz o terminal: busca en internet, crea documentos, abre apps, responde preguntas
2. **Orquestador DAG** — 11 agentes especializados que generan código completo (landing, SaaS, bot, API, etc.)

---

## Inicio rápido

### 1. Clonar e instalar

```bash
git clone https://github.com/yoesitooo/SDD-Ecosystem-core.git
cd SDD-Ecosystem-core
pip install -r requirements.txt
```

### 2. Configurar una clave (gratis)

```bash
# Windows
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

Abre `.env` y pon al menos una clave gratis, por ejemplo `GEMINI_API_KEY` (ver **Modelos: gratis primero** más abajo).

### 3. Verificar instalación

```bash
python test_system.py
```

Muestra qué dependencias y proveedores quedaron listos (basta con un proveedor). Si algo falla, la sección **Solución de problemas** tiene el arreglo.

### 4. Arrancar

**Windows — doble clic en uno de estos archivos:**

| Archivo | Qué hace |
|---------|----------|
| `jarvis_terminal.bat` | Jarvis en terminal Rich. **Sin micrófono, sin Telegram.** El más fácil para empezar. |
| `jarvis_voz.bat` | Jarvis por voz. Requiere micrófono. Abre el orb visual en `http://localhost:8000/jarvis`. Di "Jarvis" para activar. |
| `jarvis_telegram.bat` | Bot de Telegram activo. Requiere `TELEGRAM_TOKEN` en `.env`. |
| `jarvis_voz_telegram.bat` | Voz + Telegram simultáneo. Ambos activos al mismo tiempo. |

**Linux / Mac:**
```bash
TRANSPORT_MODE=cli python main.py        # terminal
TRANSPORT_MODE=voice ENABLE_HTTP=true python main.py   # voz
TRANSPORT_MODE=telegram python main.py   # telegram
```

---

## Modelos: gratis primero

No hace falta pagar nada para usarlo: **basta con una clave gratis** (recomendado: Gemini). Cada agente pide un *nivel* y el router recorre una cadena de proveedores; si uno no tiene clave, llega a su límite gratis (HTTP 429) o se cae, pasa solo al siguiente.

| Proveedor | Cómo se usa | Costo | Para qué sirve mejor |
|---|---|---|---|
| **Gemini** (Google AI Studio) | `GEMINI_API_KEY` — [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Plan gratis, sin tarjeta (modelos Flash y Flash-Lite) | Opción por defecto; contexto largo; acepta imágenes |
| **Groq** | `GROQ_API_KEY` — [console.groq.com/keys](https://console.groq.com/keys) | Plan gratis | Respuestas muy rápidas; Jarvis lo usa para la voz (Whisper) |
| **Cerebras** | `CEREBRAS_API_KEY` | Plan gratis | Mucho volumen por día |
| **OpenRouter** | `OPENROUTER_API_KEY` | Modelos `:free` | Muchos modelos con una sola clave |
| **GitHub Models** | `GITHUB_MODELS_TOKEN` | Gratis con cuenta de GitHub | Probar modelos de distintos laboratorios |
| **NVIDIA NIM** | `NVIDIA_API_KEY` | Créditos gratis | Modelos de código y visión |
| **Antigravity CLI** (`agy`) | Iniciar sesión una vez con `agy` | Cuenta de Google gratis; límites más altos con **Google AI Pro/Ultra** | Usar tu suscripción de Google en vez de pagar por tokens |
| **Claude Code CLI** (`claude`) | Iniciar sesión una vez con `claude` | Plan Claude Pro/Max | Usar tu suscripción de Claude |

**Sobre la cuenta de Google AI Pro:** la suscripción **no** aumenta los límites de la API de Gemini (eso va por Google AI Studio), pero sí da límites más altos en el CLI de Google. Desde junio de 2026 ese CLI es **Antigravity CLI** (`agy`), que reemplazó a Gemini CLI para cuentas personales. El proveedor `antigravity` lo ejecuta en modo *headless* (`agy -p`, salida JSON), sin shell y sin permisos para editar archivos. Las suscripciones son para uso personal; para un servicio con usuarios usa las APIs.

**Cadenas por defecto** (ver [`core/config.py`](./core/config.py)):

| Nivel | Fases | Cadena |
|---|---|---|
| `smart` | discovery, requirements, architecture, code_review | claude → antigravity → gemini-3.8-flash → groq gpt-oss-120b → groq llama-3.3-70b |
| `code` | frontend, backend | claude → antigravity → gemini-3.8-flash → groq gpt-oss-120b |
| `fast` | hu_writer, tech_spec, db, qa | gemini-3.5-flash-lite → groq llama-3.1-8b → groq gpt-oss-20b → antigravity |
| `vision` | ux_ui | gemini-3.8-flash → NVIDIA llama-3.2-11b-vision |

Los proveedores sin clave (o sin el CLI instalado) se saltan. Cualquier nivel se cambia desde `.env`, por ejemplo:

```bash
SDD_CHAIN_SMART=antigravity:,gemini:gemini-3.8-flash,cerebras:gpt-oss-120b
```

`python test_system.py` muestra qué proveedores quedaron listos.

### TELEGRAM_TOKEN — solo si usas Telegram

1. En Telegram, busca **@BotFather** y escribe `/newbot`.
2. Elige un nombre y un usuario que termine en `bot`; BotFather te da el token.
3. Pégalo en `.env`: `TELEGRAM_TOKEN=...`
4. Para que el bot solo te responda a ti, escríbele a **@userinfobot**, copia tu ID y ponlo en `TELEGRAM_ALLOWED_CHAT_ID`.

> Si dejas `TELEGRAM_ALLOWED_CHAT_ID` vacío, el bot responde a cualquiera que le escriba.

---

## Qué puede hacer

### Como asistente (Jarvis)

Escribe o di cualquier cosa en lenguaje natural:

**Búsqueda e información**
```
"busca las últimas noticias de inteligencia artificial"
"qué es Tailwind CSS v4 y en qué cambió"
"cuánto cuesta un desarrollador senior en Colombia"
```

**Documentos** — se crean en `Documents/Jarvis/` y se abren solos
```
"hazme un documento Word con una propuesta para una app de domicilios"
"crea un Excel con el presupuesto: diseño 2M, frontend 3M, backend 3M"
"arma una presentación de 5 slides sobre inteligencia artificial"
"genera un PDF con el resumen del proyecto"
"guarda esta idea como nota"
```

**Control del PC**
```
"abre VS Code"
"pon reggaetón en Spotify"
"busca tutoriales de Next.js en YouTube"
"abre github.com"
"minimiza todo"
```

**Ver la pantalla**
```
"mira mi pantalla, qué está fallando"
"qué hace ese código"
```

**Memoria persistente**
```
"recuerda que prefiero Python sobre JavaScript"
→ Lo guarda y lo usa en futuras sesiones
```

**Solo en modo voz**
```
Di "Jarvis" para activar (wake word — siempre escuchando)
Di "para" o "detente" para que vuelva a dormir
Habla encima mientras responde → lo interrumpe y escucha
```

---

### Como orquestador de código

Dile que quieres construir algo:

```
"quiero crear una app de reservas para restaurantes"
→ Jarvis: "¿Confirmas que quiero arrancar el proceso con 11 agentes?"
→ Di "sí" / "dale" / "confirma"
→ Hace 3 preguntas específicas del proyecto
→ Genera brief técnico
→ 11 agentes ejecutan y generan el código
→ Resultado en workspaces/<proyecto>/
```

**O con comandos directos:**
```
/new MiProyecto    → crear proyecto
/go                → avanzar un agente
/status            → ver fase actual
/auto 5            → ejecutar 5 pasos solo
/rollback fase     → volver a una fase
/spec              → ver especificación generada
```

**Tipos de proyecto soportados:**

| Tipo | Stack | Se activa con... |
|------|-------|-----------------|
| Landing page | Next.js 15 + Tailwind v4 + Framer Motion | "página de presentación" |
| SaaS / Dashboard | Next.js 15 + FastAPI + PostgreSQL + Auth.js | "app con usuarios y dashboard" |
| E-commerce | Next.js + Stripe + PostgreSQL | "tienda online, carrito" |
| API REST | FastAPI + SQLAlchemy 2.x + PostgreSQL | "solo backend, sin frontend" |
| Bot de Telegram | aiogram 3.x + FSM + PostgreSQL | "bot de telegram" |
| Bot de Discord | discord.py 2.x | "bot de discord" |
| Sistema de agentes IA | FastAPI + Groq + SQLite + tool calling | "agente de IA, pipeline LLM" |
| Pipeline de datos | Playwright + Polars + PostgreSQL | "scraper, ETL, automatización" |
| CLI tool | Typer + Rich + pyproject.toml | "herramienta de terminal" |
| App móvil | React Native (Expo) + FastAPI | "app para Android/iOS" |
| App de escritorio | Tauri v2 + React | "app de escritorio" |

Para proyectos web, después de generar:
```bash
cd workspaces/MiProyecto
npm install
npm run dev    # → http://localhost:3000
```

---

## Estructura del proyecto

```
SDD-Ecosystem/
├── agents/           # 11 agentes DAG + Jarvis assistant + smart discovery
├── orchestrator/     # Motor DAG: executor, dag, circuit breaker, autopilot
├── providers/        # Router con respaldo + APIs OpenAI-compatibles + CLIs de suscripción
├── tests/            # Pruebas (pytest) del router, proveedores, configuración y DAG
├── transports/       # Telegram, voz, HTTP, CLI
├── tools/
│   ├── voice/        # Micrófono, TTS (Edge-TTS), wake word
│   ├── vision/       # Screenshot + análisis visual
│   ├── system/       # Control PC (pyautogui), navegador
│   ├── search/       # DuckDuckGo sin API key
│   ├── documents/    # Word, Excel, PowerPoint, PDF
│   └── scaffold.py   # Genera estructura base Next.js / Python
├── memory/           # Engram (FTS5), session store, memoria personal
├── skills/           # Conocimiento especializado en Markdown
├── core/             # Config, notificaciones
├── static/           # jarvis.html — orb animado WebSocket
├── jarvis_terminal.bat      ← doble clic para modo terminal
├── jarvis_voz.bat           ← doble clic para modo voz
├── jarvis_telegram.bat      ← doble clic para modo Telegram
├── jarvis_voz_telegram.bat  ← doble clic para ambos simultáneo
├── main.py
├── test_system.py
├── requirements.txt
└── .env.example
```

---

## Personalización

**Cambiar la voz de Jarvis** — en `.env`:
```
JARVIS_VOICE=es-CO-GonzaloNeural    # Hombre Colombia (default)
JARVIS_VOICE=es-CO-SalomeNeural     # Mujer Colombia
JARVIS_VOICE=es-ES-AlvaroNeural     # Hombre España
JARVIS_RATE=+10%                    # Velocidad
```

**Agregar una skill de conocimiento:**
1. Crear `skills/mi_skill.md` con los patrones
2. Registrar triggers en `skills/registry.py`:
```python
"mi keyword": "mi_skill.md",
```

**Agregar una herramienta a Jarvis:**
1. Implementar la función en `tools/`
2. Agregar la definición JSON en `TOOLS` de `agents/jarvis_assistant.py`
3. Agregar el caso `elif fn == "nombre":` en el mismo archivo

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `Ningún proveedor pudo responder` | Agrega al menos una clave gratis (por ejemplo `GEMINI_API_KEY`) en `.env`; el mensaje lista el motivo de cada proveedor |
| El bot de Telegram no responde | Verificar `TELEGRAM_TOKEN` y `TELEGRAM_ALLOWED_CHAT_ID` en `.env` |
| Jarvis no escucha el micrófono | Windows → Configuración → Privacidad → Micrófono → Permitir acceso |
| Wake word no funciona bien | Hablar más despacio; el sistema se calibra al iniciar (2 segundos) |
| Error 429 (límite gratis) | El router pasa solo al siguiente proveedor; agrega otra clave gratis para tener más respaldo |
| `npm: command not found` | Instalar [Node.js 20+](https://nodejs.org) para proyectos web |
| Error de Edge-TTS (socket) | Problema de red momentáneo, se recupera solo al siguiente turno |
| `agy` o `claude` fallan | Abre el CLI una vez de forma interactiva para iniciar sesión; si no, el router los salta |

---

## Requisitos del sistema

- **Python 3.12+**
- **Node.js 20+** — solo para ejecutar proyectos web generados
- **Antigravity CLI / Claude Code CLI** — opcionales, para usar una suscripción en vez de claves de API
- **Micrófono** — solo para modo voz
- Windows 10/11 (los `.bat` son para Windows; en Linux/Mac usar los comandos directos)

---

## Arquitectura interna

### Los 11 agentes del DAG

```
Discovery → Requirements → Architecture
                               ↓
                     UX/UI ──┬── HU Writer     (paralelo)
                               ↓
                          Tech Spec
                               ↓
              Frontend ──┬── Backend ──┬── DB   (paralelo)
                               ↓
                     QA ──┬── Code Review       (paralelo)
```

Cada fase pide un nivel de modelo (`smart`, `code`, `fast`, `vision`) y el router elige el primer proveedor disponible de esa cadena, con respaldo automático (ver **Modelos: gratis primero**).

### Memoria del sistema
- **Engram** (SQLite FTS5): decisiones, errores y contexto institucional por proyecto
- **Session Store** (SQLite): estado del DAG — en qué fase está cada proyecto
- **Personal Memory** (SQLite): preferencias tuyas que persisten entre sesiones

### Por qué 11 agentes y no uno solo

Un agente único para generar un proyecto completo tiene limitaciones reales: el contexto de un LLM no alcanza para todo un proyecto, no hay especialización, y todo es secuencial.

El DAG resuelve esto: cada agente tiene una responsabilidad acotada, usa el modelo correcto para su tarea, y las fases independientes corren en paralelo. El resultado es código de mayor calidad en menos tiempo.

---

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest -q tests
```

Las pruebas no llaman a ningún modelo: simulan las respuestas HTTP y los CLIs para verificar el formato de las peticiones, el respaldo entre proveedores (límite 429, errores, credenciales faltantes), la lectura de la salida JSON de `agy` y la estructura del DAG. Corren en GitHub Actions en cada push.

---

## Licencia

MIT — libre de usar, modificar y distribuir con atribución.

---

*Construido con Claude Code, Groq, NVIDIA NIM y mucho café.*
