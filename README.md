# SDD Ecosystem

**Sistema multi-agente que convierte una descripción en lenguaje natural en un proyecto de software funcional.**

> **🇬🇧 In English — at a glance**
>
> SDD (Spec-Driven Development) Ecosystem is a Python multi-agent orchestrator: you describe a project in plain language and **11 specialised LLM agents** take it through discovery → requirements → architecture → UX/UI + user stories → tech spec → frontend + backend + DB → QA + code review.
>
> | Design point | Where to look |
> |---|---|
> | The DAG is **pure data**; the executor reads it, and phases in the same group run in parallel with `asyncio.gather` (phases 4, 6 and 7) | [`orchestrator/dag.py`](./orchestrator/dag.py) · [`orchestrator/executor.py`](./orchestrator/executor.py) |
> | **Multi-provider router** — each phase is sent to the model that fits it (Groq / NVIDIA NIM / Claude) behind one `BaseProvider` interface | [`providers/`](./providers) |
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

### 2. Configurar claves

```bash
# Windows
copy .env.example .env

# Linux / Mac
cp .env.example .env
```

Abre `.env` y rellena tus claves. Ver la sección **Obtener claves** más abajo.

### 3. Verificar instalación

```bash
python test_system.py
```

Debe mostrar `33/33 checks pasaron`. Si alguno falla, la sección **Solución de problemas** tiene el fix.

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

## Obtener las claves

### GROQ_API_KEY — Gratis, obligatoria

Groq es el LLM principal del sistema (velocidad, costo cero). También procesa la voz con Whisper.

1. Ir a [console.groq.com](https://console.groq.com)
2. Crear cuenta (gratis)
3. Ir a **API Keys** → **Create API Key**
4. Copiar la clave (empieza con `gsk_...`)
5. Pegarla en `.env`: `GROQ_API_KEY=gsk_...`

**Límites gratuitos:** 30 requests/min, 6000 tokens/min — suficiente para uso normal.

---

### NVIDIA_HEAVY_KEY — Gratis, obligatoria

NVIDIA NIM da acceso a modelos de código especializados (qwen2.5-coder-32b) sin costo.

1. Ir a [integrate.api.nvidia.com](https://integrate.api.nvidia.com)
2. Crear cuenta con email
3. Ir a **API Keys** → **Generate API Key**
4. Copiar la clave (empieza con `nvapi-...`)
5. Pegarla en `.env`: `NVIDIA_HEAVY_KEY=nvapi-...`

---

### TELEGRAM_TOKEN — Gratis, solo si usas Telegram

Si no vas a usar Telegram, puedes dejarlo en blanco y usar el modo terminal o voz.

**Pasos para crear el bot:**

1. Abrir Telegram y buscar **@BotFather**
2. Escribir `/newbot`
3. BotFather pide un **nombre para mostrar** — puede ser cualquier cosa, ej: `Mi Jarvis`
4. BotFather pide un **username** — debe terminar en `bot`, ej: `mi_jarvis_bot`
5. BotFather responde con el token: `1234567890:AAHxxxxxxxxxxxx...`
6. Copiar ese token en `.env`: `TELEGRAM_TOKEN=1234567890:AAH...`

**Obtener tu TELEGRAM_ALLOWED_CHAT_ID** (tu ID personal para que el bot solo te responda a ti):

1. Buscar **@userinfobot** en Telegram
2. Escribirle cualquier mensaje
3. Responde con tu ID: `Id: 123456789`
4. Copiar ese número en `.env`: `TELEGRAM_ALLOWED_CHAT_ID=123456789`

> Si dejas `TELEGRAM_ALLOWED_CHAT_ID` vacío el bot responde a cualquiera que le escriba.

---

### ANTHROPIC_API_KEY — Opcional

El sistema usa Claude a través de la **CLI de Claude** (suscripción Pro), no por API directa. Si tienes suscripción Pro de Claude:

```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

Si no tienes suscripción Pro, el sistema funciona igual usando Groq y NVIDIA para todas las fases.

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
├── providers/        # Abstracción de LLMs: Groq, Claude CLI, NVIDIA NIM
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
| `GROQ_API_KEY not set` | Verificar que `.env` existe y tiene la clave |
| El bot de Telegram no responde | Verificar `TELEGRAM_TOKEN` y `TELEGRAM_ALLOWED_CHAT_ID` en `.env` |
| Jarvis no escucha el micrófono | Windows → Configuración → Privacidad → Micrófono → Permitir acceso |
| Wake word no funciona bien | Hablar más despacio; el sistema se calibra al iniciar (2 segundos) |
| Error 400 de Groq | Reiniciar — puede ser rate limit momentáneo |
| `npm: command not found` | Instalar [Node.js 20+](https://nodejs.org) para proyectos web |
| Error de Edge-TTS (socket) | Problema de red momentáneo, se recupera solo al siguiente turno |
| Claude CLI no funciona | `npm i -g @anthropic-ai/claude-code` → `claude auth login` |

---

## Requisitos del sistema

- **Python 3.12+**
- **Node.js 20+** — solo para ejecutar proyectos web generados
- **Claude CLI** — opcional, para fases que usan Claude. `npm i -g @anthropic-ai/claude-code`
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

Cada fase usa el modelo más adecuado:
- **Discovery, Requirements** → Groq llama-3.3-70b (velocidad, gratis)
- **Architecture, Code Review** → Claude Sonnet via CLI (razonamiento profundo)
- **Frontend, Backend, DB** → NVIDIA qwen2.5-coder-32b (código especializado, gratis)

### Memoria del sistema
- **Engram** (SQLite FTS5): decisiones, errores y contexto institucional por proyecto
- **Session Store** (SQLite): estado del DAG — en qué fase está cada proyecto
- **Personal Memory** (SQLite): preferencias tuyas que persisten entre sesiones

### Por qué 11 agentes y no uno solo

Un agente único para generar un proyecto completo tiene limitaciones reales: el contexto de un LLM no alcanza para todo un proyecto, no hay especialización, y todo es secuencial.

El DAG resuelve esto: cada agente tiene una responsabilidad acotada, usa el modelo correcto para su tarea, y las fases independientes corren en paralelo. El resultado es código de mayor calidad en menos tiempo.

---

## Licencia

MIT — libre de usar, modificar y distribuir con atribución.

---

*Construido con Claude Code, Groq, NVIDIA NIM y mucho café.*
