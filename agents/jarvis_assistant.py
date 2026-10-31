"""
Jarvis General Assistant
========================
Modo libre: chat, búsqueda web, Spotify, YouTube, URLs.
Se activa cuando no hay proyecto DAG activo.
Usa Groq AsyncClient + function calling (llama-3.3-70b-versatile).
"""

import json
import logging
from core.config import GROQ_API_KEY

log = logging.getLogger(__name__)

# Historial en memoria por chat_id (no persiste entre reinicios — intencional)
_histories: dict[str, list] = {}

# Proyectos pendientes de confirmación: chat_id → {description, project_type}
_pending_projects: dict[str, dict] = {}

_CONFIRM_WORDS = {"sí", "si", "sí confirma", "confirma", "confirmado", "dale",
                  "listo", "adelante", "arranca", "sí arranca", "hazlo"}
_CANCEL_WORDS  = {"no", "cancela", "mejor no", "para", "detente", "espera"}


def get_history(chat_id: str) -> list:
    return _histories.get(str(chat_id), [])


def add_to_history(chat_id: str, role: str, content: str):
    h = _histories.setdefault(str(chat_id), [])
    h.append({"role": role, "content": content})
    # Mantener solo los últimos 10 turnos (20 mensajes)
    if len(h) > 20:
        _histories[str(chat_id)] = h[-20:]


def clear_history(chat_id: str):
    _histories.pop(str(chat_id), None)


# ── Definición de tools para Groq ────────────────────────────────────────────
# Cada tool tiene un campo extra "tags" para selección dinámica.
# _select_tools() envía máx 8 tools relevantes al modelo — más causa confusión.

_ALL_TOOLS: list[dict] = [
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the internet for current news, facts, prices, people, or any topic requiring recent information.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "open_spotify",
        "description": "Open Spotify in the browser to play a song, artist, album, or music genre.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "open_youtube",
        "description": "Open YouTube in the browser to search for a video, tutorial, or music.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "open_url",
        "description": "Open a specific URL or website in the default browser.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "look_at_screen",
        "description": "Take a screenshot and analyze it with AI. Use when user says look at my screen, what do you see, or what is failing.",
        "parameters": {"type": "object", "properties": {"question": {"type": "string", "description": "Specific question about the screen"}}, "required": ["question"]}}},
    {"type": "function", "function": {
        "name": "remember_fact",
        "description": "Save a fact or user preference to persistent memory for future conversations.",
        "parameters": {"type": "object", "properties": {
            "fact": {"type": "string", "description": "The fact or preference to remember"},
            "category": {"type": "string", "description": "Category: preference, project, personal, work"}
        }, "required": ["fact"]}}},
    {"type": "function", "function": {
        "name": "recall_memory",
        "description": "Retrieve saved facts or preferences from persistent memory.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "What to search in memory"}}}}},
    {"type": "function", "function": {
        "name": "open_app",
        "description": "Open an application on the computer: VS Code, Chrome, Spotify, Discord, terminal, calculator.",
        "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}}},
    {"type": "function", "function": {
        "name": "press_keys",
        "description": "Press a keyboard shortcut on the system. Examples: ctrl+c, alt+tab, win+d, ctrl+z.",
        "parameters": {"type": "object", "properties": {"combo": {"type": "string", "description": "Key combination separated by +"}}, "required": ["combo"]}}},
    {"type": "function", "function": {
        "name": "media_control",
        "description": "Control music/media playback: play, pause, next song, previous song, stop. Works with Spotify, YouTube, any media player.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "description": "One of: play_pause, next, previous, stop"}
        }, "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "volume_control",
        "description": "Control system volume: set level, raise, lower, or mute. Use when user says louder, quieter, mute, volume X%.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "description": "One of: up, down, mute, set"},
            "level":  {"type": "string", "description": "Volume level 0-100, only needed when action is set"}
        }, "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "system_control",
        "description": "System actions: lock screen, show desktop, turn off monitor.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "description": "One of: lock, desktop, sleep_display"}
        }, "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "request_project_confirmation",
        "description": "Use ONLY when user explicitly asks to BUILD software: app, bot, system, website, API, or AI agent. NOT for questions, searches, or documents. Starts an 11-agent development process.",
        "parameters": {"type": "object", "properties": {
            "description": {"type": "string", "description": "Description of the software to build"},
            "project_type": {"type": "string", "description": "Type: web_saas, landing, telegram_bot, api_service, ai_agent"}
        }, "required": ["description"]}}},
    {"type": "function", "function": {
        "name": "debug_error",
        "description": "Diagnose a code or system error. Takes a screenshot automatically and analyzes what is failing.",
        "parameters": {"type": "object", "properties": {"description": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "create_word_doc",
        "description": "Create a Word (.docx) document. Use for proposals, reports, contracts, briefs, letters.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "sections": {"type": "string", "description": 'JSON array: [{"heading": "Title", "content": "Body text"}]'},
            "filename": {"type": "string"}
        }, "required": ["title", "sections"]}}},
    {"type": "function", "function": {
        "name": "create_excel",
        "description": "Create an Excel spreadsheet (.xlsx). Use for budgets, lists, data tables, inventories.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "headers": {"type": "string", "description": "Column names separated by comma: Name,Price,Quantity"},
            "rows": {"type": "string", "description": 'Rows as JSON: [["Item", 1000, 3]]'},
            "filename": {"type": "string"},
            "sheet_name": {"type": "string"}
        }, "required": ["title", "headers", "rows"]}}},
    {"type": "function", "function": {
        "name": "create_presentation",
        "description": "Create a PowerPoint (.pptx) presentation. Use for pitches, demos, project presentations.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "slides": {"type": "string", "description": 'JSON array: [{"title": "Slide title", "content": "Bullet points"}]'},
            "filename": {"type": "string"}
        }, "required": ["title", "slides"]}}},
    {"type": "function", "function": {
        "name": "create_pdf",
        "description": "Create a PDF document. Use for formal documents, reports, executive summaries.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "content": {"type": "string", "description": "Full text content with sections"},
            "filename": {"type": "string"}
        }, "required": ["title", "content"]}}},
    {"type": "function", "function": {
        "name": "write_note",
        "description": "Save a quick text note. For ideas, reminders, informal lists.",
        "parameters": {"type": "object", "properties": {
            "content": {"type": "string"},
            "filename": {"type": "string"}
        }, "required": ["content"]}}},
    {"type": "function", "function": {
        "name": "open_file",
        "description": "Open a file saved by Jarvis with the default application.",
        "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}},
    {"type": "function", "function": {
        "name": "list_files",
        "description": "List files saved by Jarvis in Documents/Jarvis/ folder.",
        "parameters": {"type": "object", "properties": {"subfolder": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "run_autopilot",
        "description": "Run all remaining DAG phases automatically in background. Use when user says run everything, do it alone, or continue without me.",
        "parameters": {"type": "object", "properties": {"confirm": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "set_timer",
        "description": "Set a timer or reminder. Jarvis will speak when time is up. Use for reminders, countdowns, alerts.",
        "parameters": {"type": "object", "properties": {
            "minutes": {"type": "string", "description": "Duration in minutes (can be decimal, e.g. 1.5 for 90 seconds)"},
            "message": {"type": "string", "description": "What to say when timer ends (optional)"}
        }, "required": ["minutes"]}}},
    {"type": "function", "function": {
        "name": "pomodoro",
        "description": "Start or cancel a Pomodoro work/break cycle. Default: 25 min work, 5 min break, 4 cycles.",
        "parameters": {"type": "object", "properties": {
            "action":       {"type": "string", "description": "start or cancel"},
            "work_minutes": {"type": "string", "description": "Work duration in minutes (default 25)"},
            "break_minutes":{"type": "string", "description": "Break duration in minutes (default 5)"},
            "cycles":       {"type": "string", "description": "Number of cycles (default 4)"}
        }, "required": ["action"]}}},
    {"type": "function", "function": {
        "name": "get_datetime",
        "description": "Get the current date and time. Use when user asks what time it is, what day is today, or the date.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "get_system_info",
        "description": "Get computer status: CPU usage, RAM, disk space, battery level, top processes.",
        "parameters": {"type": "object", "properties": {
            "detail": {"type": "string", "description": "What to check: all, cpu, ram, disk, battery, processes"}
        }}}},
    {"type": "function", "function": {
        "name": "find_files",
        "description": "Search for files on the computer by name or type. Searches Desktop, Documents, Downloads.",
        "parameters": {"type": "object", "properties": {
            "query":     {"type": "string", "description": "Filename or partial name to search"},
            "extension": {"type": "string", "description": "File extension to filter by (pdf, py, docx, etc.)"}
        }}}},
    {"type": "function", "function": {
        "name": "read_file_aloud",
        "description": "Read the contents of a text file or saved note aloud. Use when user says 'read me', 'lee la nota', 'cuéntame lo que dice'.",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "Filename or path to read"}
        }, "required": ["filename"]}}},
]



# Alias público para test_system.py y otras referencias externas
TOOLS = _ALL_TOOLS

# ── Grupos por keyword para selección dinámica ────────────────────────────────
_TOOL_GROUPS: dict[str, list[str]] = {
    "search":    ["web_search"],
    "browser":   ["open_spotify", "open_youtube", "open_url"],
    "docs":      ["create_word_doc", "create_excel", "create_presentation", "create_pdf", "write_note", "open_file", "list_files"],
    "system":    ["open_app", "press_keys", "system_control"],
    "playback":  ["media_control"],
    "volume":    ["volume_control"],
    "vision":    ["look_at_screen"],
    "memory":    ["remember_fact", "recall_memory"],
    "project":   ["request_project_confirmation"],
    "debug":     ["debug_error"],
    "autopilot": ["run_autopilot"],
    "timer":     ["set_timer", "pomodoro"],
    "sysinfo":   ["get_system_info"],
    "files":     ["find_files", "read_file_aloud"],
    "datetime":  ["get_datetime"],
}

_KEYWORDS: dict[str, list[str]] = {
    # files va ANTES de docs: "léeme la nota" es leer, no crear
    "files":     ["busca el archivo", "encuentra el", "dónde está", "busca en mis", "lee la nota", "léeme", "lee el archivo", "cuéntame lo que dice", "lee mi"],
    "search":    ["busca", "buscar", "noticias", "qué es", "cuál es", "cómo funciona", "información sobre", "investiga", "clima", "temperatura"],
    "browser":   ["spotify", "youtube", "video", "entra a", "sitio", "página", "url", "http",
                  "abre ", "facebook", "instagram", "twitter", "gmail", "google", "navegador", "web", "ábreme"],
    "docs":      ["crea un word", "haz un word", "crea un excel", "haz un excel", "presentación", "powerpoint", "crea un pdf", "haz un pdf", "documento", "informe", "propuesta", "apunta", "guarda una nota", "anota"],
    "system":    ["abre ", "lanza ", "ejecuta ", "ctrl", "alt", "win+", "tecla", "minimiza", "maximiza", "bloquea", "escritorio", "monitor"],
    "playback":  ["play", "pause", "pausa", "siguiente", "anterior", "reproduce", "para la música", "reanuda"],
    "volume":    ["volumen", "sube el", "baja el", "más alto", "más bajo", "silencia", "mute", "sonido"],
    "vision":    ["pantalla", "mira", "screenshot", "captura", "qué ves", "qué hay", "qué está", "analiza lo que"],
    "memory":    ["recuerda", "recuerdo", "olvida", "preferencia", "sé que", "siempre hago"],
    "project":   ["crear app", "construir", "desarrollar", "quiero hacer una", "quiero crear", "nueva app", "nuevo sistema", "nuevo bot"],
    "debug":     ["error", "falla", "no funciona", "bug", "excepción", "traceback", "qué está mal"],
    "autopilot": ["ejecuta todo", "hazlo solo", "corre todo", "autopilot", "continúa sin mí"],
    "timer":     ["timer", "temporizador", "recordatorio", "avísame en", "en ", " minutos", "pomodoro", "descanso", "trabaj"],
    "sysinfo":   ["cpu", "ram", "memoria", "disco", "batería", "procesos", "rendimiento", "lento", "cuánta", "estado del"],
    "datetime":  ["hora", "qué día", "fecha", "qué horas", "día es hoy", "qué hora"],
}

_TOOL_BY_NAME: dict[str, dict] = {t["function"]["name"]: t for t in _ALL_TOOLS}

# Cuando NADA específico coincide (chat casual o pregunta general), solo ofrecemos
# estas 2: por si pide info reciente o quiere construir algo. Mínimo gasto de tokens.
_FALLBACK_TOOLS = ["web_search", "request_project_confirmation"]


class _SyntheticFunc:
    """Imita tc.function para tool calls extraídos de texto."""
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class _SyntheticToolCall:
    """Imita un tool_call de la API para los que el 8b escribe como texto."""
    _counter = 0

    def __init__(self, name: str, arguments: str):
        _SyntheticToolCall._counter += 1
        self.id = f"synthetic_{_SyntheticToolCall._counter}"
        self.type = "function"
        self.function = _SyntheticFunc(name, arguments)


class _SyntheticMessage:
    """Imita response.choices[0].message cuando recuperamos tool calls de un error/texto."""
    def __init__(self, tool_calls: list, content: str = ""):
        self.tool_calls = tool_calls
        self.content = content


def _parse_text_tool_calls(content: str) -> list[_SyntheticToolCall]:
    """
    Los modelos llama (sobre todo 8b) a veces escriben el tool call como texto:
      <function=open_url>{"url": "..."}</function>
      <function=open_url{"url": "..."}</function>
    Esto los extrae y convierte en tool calls reales ejecutables.
    """
    import re
    if not content or "<function=" not in content:
        return []

    calls: list[_SyntheticToolCall] = []
    # Captura: nombre + el primer objeto JSON {...} que le sigue
    pattern = re.compile(r'<function=(\w+)\s*>?\s*(\{.*?\})', re.DOTALL)
    for m in pattern.finditer(content):
        name = m.group(1)
        args_str = m.group(2)
        # Validar que sea JSON parseable
        try:
            json.loads(args_str)
        except json.JSONDecodeError:
            args_str = "{}"
        calls.append(_SyntheticToolCall(name, args_str))

    return calls


def _strip_function_tags(content: str) -> str:
    """Quita los tags <function=...></function> del texto para no leerlos en voz."""
    import re
    # Quitar el bloque completo: <function=name>{...}</function>
    cleaned = re.sub(r'<function=\w+\s*>?\s*\{.*?\}\s*(?:</function>)?', '', content, flags=re.DOTALL)
    # Limpiar cualquier tag residual suelto
    cleaned = re.sub(r'</?function[^>]*>', '', cleaned)
    return cleaned.strip()


def _select_tools(message: str) -> list[dict]:
    """
    Devuelve solo las tools que el mensaje realmente necesita (≤9).
    Chat casual → 2 tools (web_search + project). Menos tokens = sin rate limit
    y el modelo no se confunde narrando tools que no existen.
    """
    msg_low = message.lower()
    selected: list[str] = []

    for group, keywords in _KEYWORDS.items():
        if any(kw in msg_low for kw in keywords):
            selected.extend(_TOOL_GROUPS[group])

    # Si detectamos intención específica, añadir memoria (barato y útil)
    if selected:
        selected.extend(["remember_fact", "recall_memory"])
    else:
        # Chat casual o pregunta general → set mínimo
        selected = list(_FALLBACK_TOOLS)

    # Deduplicar manteniendo orden, limitar a 9
    seen: set[str] = set()
    final: list[str] = []
    for name in selected:
        if name not in seen:
            seen.add(name)
            final.append(name)
        if len(final) >= 9:
            break

    return [_TOOL_BY_NAME[n] for n in final if n in _TOOL_BY_NAME]


SYSTEM_PROMPT = """You are Jarvis, a personal AI assistant. Always respond in Colombian Spanish, natural and conversational.

Conversation style:
- Short, natural responses. Max 2-3 sentences for casual chat.
- Use casual phrases: "claro", "mira", "oye", "sí, exactamente" — natural, not robotic.
- Never start with "¡Claro que sí!" or "¡Por supuesto!" — sounds like a bot.
- No bullet points or lists. Speak in normal sentences.
- Adapt immediately if the user changes topic or interrupts.

Tool usage rules:
- Use web_search when asked about news, current facts, prices, or anything requiring recent info.
- Use open_spotify/open_youtube/open_url to open media or websites.
- Use remember_fact/recall_memory to save and retrieve user preferences.
- Use look_at_screen when asked about what's on screen or to analyze code/errors.
- Use open_app/press_keys to control the computer.
- Use document tools (create_word_doc, create_excel, etc.) to generate files.
- Use request_project_confirmation ONLY when the user explicitly asks to BUILD software
  (an app, bot, system, API, AI agent, etc.). NOT for questions, searches, or documents.

Always respond in Spanish regardless of tool results language."""


async def run(user_message: str, chat_id: str = "default") -> str:
    """
    Procesa un mensaje en modo asistente libre con herramientas.
    Mantiene historial de conversación por chat_id.
    """
    try:
        from groq import AsyncGroq
    except ImportError:
        log.error("[ASSISTANT] groq SDK no instalado")
        return "Error: groq no instalado. Ejecuta: pip install groq"

    from tools.web_search import search, format_results
    from tools.browser_actions import open_url, open_spotify, open_youtube
    from tools.screen_vision import look_at_screen
    from tools.pc_control import (
        open_app, press_keys,
        media_play_pause, media_next, media_prev, media_stop,
        volume_up, volume_down, volume_mute, set_volume,
        lock_screen, show_desktop, sleep_display,
        get_clipboard, set_clipboard,
    )
    from tools.document_writer import (
        create_word_doc, create_excel, create_presentation,
        create_pdf, write_note, open_file, list_files,
    )
    from tools.timers import set_timer, start_pomodoro, cancel_pomodoro
    from tools.system_info import get_status, get_cpu, get_ram, get_disk, get_top_processes
    from tools.file_search import find_files, read_text_file
    from memory.personal_memory import remember, recall_as_text

    # ── Confirmación pendiente de proyecto ───────────────────────────────
    pending = _pending_projects.get(str(chat_id))
    if pending:
        low = user_message.lower().strip()
        if any(w in low for w in _CONFIRM_WORDS):
            _pending_projects.pop(str(chat_id), None)
            from agents.smart_discovery import start as disc_start
            return await disc_start(str(chat_id), pending["description"])
        elif any(w in low for w in _CANCEL_WORDS):
            _pending_projects.pop(str(chat_id), None)
            add_to_history(chat_id, "user", user_message)
            add_to_history(chat_id, "assistant", "Okey, cancelado. ¿En qué más te ayudo?")
            return "Okey, cancelado. ¿En qué más te ayudo?"
        # Si dijo otra cosa mientras hay pendiente, cancelar silenciosamente y procesar normal
        _pending_projects.pop(str(chat_id), None)

    client = AsyncGroq(api_key=GROQ_API_KEY)

    # Inyectar memoria personal si existe
    memory_text = recall_as_text(limit=6)
    system = SYSTEM_PROMPT
    if "No hay recuerdos" not in memory_text:
        system += f"\n\nLo que recuerdas del usuario:\n{memory_text}"

    # Construir messages con historial recortado (últimos 3 turnos = 6 msgs)
    # Menos historial = menos tokens = no toca el rate limit del 70b.
    messages = [{"role": "system", "content": system}]
    messages.extend(get_history(chat_id)[-6:])
    messages.append({"role": "user", "content": user_message})

    # 70b primario: tool calling confiable. 8b de respaldo si 70b rate-limitea.
    # El gating de tools (solo las necesarias) mantiene el gasto de tokens bajo.
    MODEL_TOOLS = "llama-3.3-70b-versatile"    # primario: tool calling confiable
    MODEL_FAST  = "llama-3.1-8b-instant"        # respaldo y síntesis post-tool

    async def _complete(model, msgs, tools=None, temperature=0.3):
        """Wrapper con fallback 429 → 8b. El 8b TAMBIÉN soporta tools, así que
        las mantiene en el fallback para no perder la ejecución de herramientas."""
        kwargs = dict(messages=msgs, max_tokens=512, temperature=temperature)
        if tools:
            kwargs.update(tools=tools, tool_choice="auto", parallel_tool_calls=False)
        try:
            return await client.chat.completions.create(model=model, **kwargs)
        except Exception as e:
            if "429" in str(e) and model != MODEL_FAST:
                log.warning(f"[ASSISTANT] Rate limit en {model}, usando {MODEL_FAST} (con tools)")
                # 8b soporta tool calling — mantener las tools en el fallback
                return await client.chat.completions.create(model=MODEL_FAST, **kwargs)
            raise

    try:
        # Seleccionar tools relevantes (máx 9) para evitar confusión del modelo
        active_tools = _select_tools(user_message)
        log.debug(f"[ASSISTANT] Tools activos: {[t['function']['name'] for t in active_tools]}")

        # Primera llamada — 70b para decidir si usar tool (necesita razonamiento)
        msg = None
        try:
            response = await _complete(MODEL_TOOLS, messages, tools=active_tools, temperature=0.2)
            msg = response.choices[0].message
        except Exception as groq_err:
            err_str = str(groq_err)
            # El error 400 de Groq incluye el tool call fallido en failed_generation.
            # Lo extraemos y ejecutamos en vez de rendirnos.
            if "400" in err_str or "tool" in err_str.lower():
                log.warning(f"[ASSISTANT] Tool call falló: {err_str[:120]}")
                recovered = _parse_text_tool_calls(err_str)
                if recovered:
                    log.info(f"[ASSISTANT] Recuperado del error: {[c.function.name for c in recovered]}")
                    msg = _SyntheticMessage(recovered)
                else:
                    # No se pudo recuperar — respuesta de chat sin tools
                    response = await _complete(MODEL_FAST, messages, temperature=0.4)
                    final = _strip_function_tags(response.choices[0].message.content or "") or "No entendí bien, ¿me repites?"
                    add_to_history(chat_id, "user", user_message)
                    add_to_history(chat_id, "assistant", final)
                    return final
            else:
                raise

        # El 8b a veces escribe el tool call como texto en vez de estructurado.
        # Si no hay tool_calls reales pero el contenido los tiene, parsearlos.
        effective_tool_calls = msg.tool_calls
        if not effective_tool_calls and msg.content:
            parsed = _parse_text_tool_calls(msg.content)
            if parsed:
                log.info(f"[ASSISTANT] Tool calls extraídos del texto: {[c.function.name for c in parsed]}")
                effective_tool_calls = parsed

        # Si el modelo quiere usar tools, ejecutarlos
        if effective_tool_calls:
            tool_results = []

            for tc in effective_tool_calls:
                fn = tc.function.name
                try:
                    # json.loads("null") devuelve None — forzar dict vacío
                    args = json.loads(tc.function.arguments or "{}") or {}
                except (json.JSONDecodeError, TypeError):
                    args = {}

                log.info(f"[ASSISTANT] Tool: {fn}({args})")

                if fn == "web_search":
                    results = await search(args.get("query", ""))
                    result_text = format_results(results)
                elif fn == "open_spotify":
                    result_text = open_spotify(args.get("query", ""))
                elif fn == "open_youtube":
                    result_text = open_youtube(args.get("query", ""))
                elif fn == "open_url":
                    result_text = open_url(args.get("url", ""))
                elif fn == "look_at_screen":
                    result_text = await look_at_screen(args.get("question", "¿Qué ves en la pantalla?"))
                elif fn == "remember_fact":
                    result_text = remember(args.get("fact", ""), args.get("category", "general"))
                elif fn == "recall_memory":
                    result_text = recall_as_text(args.get("query", ""))
                elif fn == "open_app":
                    result_text = open_app(args.get("app_name", ""))
                elif fn == "press_keys":
                    result_text = press_keys(args.get("combo", ""))
                elif fn == "media_control":
                    action = args.get("action", "play_pause").lower()
                    if "next" in action:
                        result_text = media_next()
                    elif "prev" in action or "anterior" in action:
                        result_text = media_prev()
                    elif "stop" in action:
                        result_text = media_stop()
                    else:
                        result_text = media_play_pause()
                elif fn == "volume_control":
                    action = args.get("action", "").lower()
                    level_raw = args.get("level", "")
                    if action == "set" and level_raw:
                        try:
                            result_text = set_volume(int(str(level_raw).replace("%", "")))
                        except ValueError:
                            result_text = "Nivel de volumen inválido."
                    elif action == "up":
                        result_text = volume_up(5)
                    elif action == "down":
                        result_text = volume_down(5)
                    elif action == "mute":
                        result_text = volume_mute()
                    else:
                        result_text = f"Acción de volumen no reconocida: {action}"
                elif fn == "system_control":
                    action = args.get("action", "").lower()
                    if action == "lock":
                        result_text = lock_screen()
                    elif action == "desktop":
                        result_text = show_desktop()
                    elif action == "sleep_display":
                        result_text = sleep_display()
                    else:
                        result_text = f"Acción no reconocida: {action}"
                elif fn == "create_word_doc":
                    raw = args.get("sections", "[]")
                    sections = json.loads(raw) if isinstance(raw, str) else raw
                    result_text = create_word_doc(
                        args.get("title", "Documento"), sections, args.get("filename", "")
                    )
                elif fn == "create_excel":
                    raw_h = args.get("headers", "")
                    headers = [h.strip() for h in raw_h.split(",")] if isinstance(raw_h, str) else raw_h
                    raw_r = args.get("rows", "[]")
                    rows = json.loads(raw_r) if isinstance(raw_r, str) else raw_r
                    result_text = create_excel(
                        args.get("title", "Hoja"), headers, rows,
                        args.get("filename", ""), args.get("sheet_name", "Datos"),
                    )
                elif fn == "create_presentation":
                    raw = args.get("slides", "[]")
                    slides = json.loads(raw) if isinstance(raw, str) else raw
                    result_text = create_presentation(
                        args.get("title", "Presentación"), slides, args.get("filename", "")
                    )
                elif fn == "create_pdf":
                    result_text = create_pdf(
                        args.get("title", "Documento"),
                        args.get("content", ""),
                        args.get("filename", ""),
                    )
                elif fn == "write_note":
                    result_text = write_note(
                        args.get("content", ""),
                        args.get("filename", ""),
                    )
                elif fn == "open_file":
                    result_text = open_file(args.get("filepath", ""))
                elif fn == "list_files":
                    result_text = list_files(args.get("subfolder", ""))
                elif fn == "request_project_confirmation":
                    desc = args.get("description", "")
                    ptype = args.get("project_type", "web_saas")
                    _pending_projects[str(chat_id)] = {"description": desc, "project_type": ptype}
                    result_text = (
                        f"Perfecto. Entendí que quieres construir: {desc}. "
                        f"Esto arranca el proceso completo con 11 agentes especializados — "
                        f"discovery, arquitectura, código, QA — puede tomar varios minutos. "
                        f"¿Confirmas que quieres arrancar, o prefieres ajustar algo primero?"
                    )
                elif fn == "debug_error":
                    from agents.debug_agent import diagnose
                    result_text = await diagnose(error_text=args.get("description", ""))
                elif fn == "run_autopilot":
                    import asyncio
                    from orchestrator.executor import run_autopilot
                    asyncio.create_task(run_autopilot(chat_id))
                    result_text = "Autopilot iniciado. Te aviso cuando termine cada fase."
                elif fn == "set_timer":
                    try:
                        mins = float(str(args.get("minutes", "1")).replace(",", "."))
                    except ValueError:
                        mins = 1.0
                    result_text = set_timer(mins, args.get("message", ""))
                elif fn == "pomodoro":
                    action = args.get("action", "start").lower()
                    if "cancel" in action or "cancela" in action or "stop" in action:
                        result_text = cancel_pomodoro()
                    else:
                        try:
                            w = int(args.get("work_minutes", 25))
                            b = int(args.get("break_minutes", 5))
                            c = int(args.get("cycles", 4))
                        except (ValueError, TypeError):
                            w, b, c = 25, 5, 4
                        result_text = start_pomodoro(w, b, c)
                elif fn == "get_datetime":
                    from datetime import datetime
                    _dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
                    _meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                              "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                    now = datetime.now()
                    result_text = (
                        f"{_dias[now.weekday()]} {now.day} de {_meses[now.month-1]} "
                        f"de {now.year}, {now.hour:02d}:{now.minute:02d}"
                    )
                elif fn == "get_system_info":
                    detail = args.get("detail", "all").lower()
                    if detail == "cpu":
                        result_text = get_cpu()
                    elif detail == "ram":
                        result_text = get_ram()
                    elif detail == "disk":
                        result_text = get_disk()
                    elif detail == "processes":
                        result_text = get_top_processes()
                    else:
                        result_text = get_status()
                elif fn == "find_files":
                    result_text = find_files(
                        args.get("query", ""),
                        args.get("extension", ""),
                    )
                elif fn == "read_file_aloud":
                    content = read_text_file(args.get("filename", ""))
                    # Enviar como notificación para que la voz lo lea
                    result_text = content
                else:
                    result_text = f"Función '{fn}' no reconocida."

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

            # Tools cuyo resultado YA es texto listo para hablar → devolver directo.
            # Solo búsqueda/visión/debug necesitan que el LLM resuma. Esto ahorra una
            # llamada completa (menos rate limit) y evita que el 8b alucine la respuesta.
            SYNTHESIS_TOOLS = {"web_search", "look_at_screen", "debug_error", "get_top_processes"}
            called_names = {tc.function.name for tc in effective_tool_calls}

            if called_names & SYNTHESIS_TOOLS:
                # Reconstruir messages con el resultado de tools para que el LLM resuma
                assistant_msg = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in effective_tool_calls
                    ],
                }
                messages.append(assistant_msg)
                messages.extend(tool_results)
                response2 = await _complete(MODEL_FAST, messages, temperature=0.4)
                final = response2.choices[0].message.content or "Listo."
            else:
                # Resultado directo — ya es hablable. Unir si hubo varios tools.
                final = " ".join(tr["content"] for tr in tool_results if tr["content"])
        else:
            # Sin tool call — respuesta directa. Limpiar tags de función residuales.
            final = _strip_function_tags(msg.content or "")
            if not final:
                r2 = await _complete(MODEL_FAST, messages, temperature=0.4)
                final = _strip_function_tags(r2.choices[0].message.content or "") or "No tengo respuesta."

        # Guardar turno en historial
        add_to_history(chat_id, "user", user_message)
        add_to_history(chat_id, "assistant", final)

        return final

    except Exception as e:
        log.error(f"[ASSISTANT] Error: {e}")
        return f"Error en el asistente: {str(e)[:150]}"
