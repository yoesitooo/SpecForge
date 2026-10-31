"""
HTTP Transport — OpenAI-compatible API para OpenClaw y cualquier cliente externo.
=================================================================================
Expone el orchestrator como si fuera un modelo de LLM estándar.
OpenClaw lo configura como "custom provider" y habla con él igual que con GPT-4.

Endpoints:
  POST /v1/chat/completions  → recibe mensaje, retorna respuesta del DAG
  GET  /v1/models            → lista el "modelo" disponible
  GET  /health               → estado del sistema
  GET  /status/{chat_id}     → estado del proyecto de una sesión

El chat_id viene del campo "user" en la request de OpenAI, o del primer
mensaje del system prompt. Si no viene, se genera uno por IP.
"""

import uuid
import time
import logging
from pathlib import Path
from typing import Set

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent.parent / "static"

from orchestrator.executor import process_message
from orchestrator.dag import PHASE_ORDER, PHASE_LABELS
from memory import session_store as store

log = logging.getLogger(__name__)

# ── WebSocket state broadcast ─────────────────────────────────────────────────
_ws_clients: Set[WebSocket] = set()

async def broadcast_jarvis_state(state: str, text: str = "") -> None:
    """Empuja cambios de estado a todos los browsers conectados al visual."""
    dead = set()
    for ws in _ws_clients:
        try:
            await ws.send_json({"state": state, "text": text})
        except Exception:
            dead.add(ws)
    _ws_clients -= dead

app = FastAPI(
    title="SDD Orchestrator API",
    description="SDD multi-agent system — OpenAI-compatible interface",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (jarvis.html, etc.)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Schemas OpenAI-compatible ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "sdd-orchestrator"
    messages: list[ChatMessage]
    stream: bool = False
    user: str | None = None         # OpenClaw pasa el session ID aquí
    temperature: float | None = None
    max_tokens: int | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_chat_id(req: ChatRequest, request: Request) -> str:
    """
    Prioridad para determinar el chat_id de la sesión:
    1. Campo 'user' de la request (OpenClaw lo envía)
    2. Header X-Session-ID
    3. IP del cliente como fallback
    """
    if req.user:
        return req.user
    if sid := request.headers.get("x-session-id"):
        return sid
    return request.client.host or f"http-{uuid.uuid4().hex[:8]}"


def _last_user_message(messages: list[ChatMessage]) -> str:
    """Extrae el último mensaje del usuario."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def _openai_response(content: str, model: str = "sdd-orchestrator") -> dict:
    """Formatea la respuesta en formato OpenAI chat completion."""
    return {
        "id": f"sdd-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sdd-orchestrator", "transport": "http"}


@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible model listing. OpenClaw lo usa para descubrir qué modelos hay."""
    return {
        "object": "list",
        "data": [
            {
                "id": "sdd-orchestrator",
                "object": "model",
                "created": 1700000000,
                "owned_by": "un-laps",
                "description": "SDD multi-agent software development orchestrator (11 agents, 7 phases)",
            }
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest, request: Request):
    """
    Endpoint principal — recibe mensajes de OpenClaw (u otro cliente OpenAI-compatible)
    y los procesa con el orchestrator del DAG.
    """
    chat_id = _resolve_chat_id(req, request)
    text = _last_user_message(req.messages)

    if not text:
        raise HTTPException(status_code=400, detail="No user message found")

    log.info(f"[HTTP] chat_id={chat_id} | msg={text[:80]}")

    try:
        reply = await process_message(chat_id, text)
        # Limpiar markdown pesado que puede confundir a algunos clientes
        reply_clean = reply.replace("```", "").strip() if req.model.endswith("-plain") else reply
        return JSONResponse(_openai_response(reply_clean))
    except Exception as e:
        log.exception(f"[HTTP] Error procesando mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])


@app.get("/status/{chat_id}")
async def session_status(chat_id: str):
    """Estado completo de una sesión — útil para el dashboard de OpenClaw."""
    state = store.get(chat_id)
    phase = state["phase"]
    idx = PHASE_ORDER.index(phase) + 1

    return {
        "chat_id": chat_id,
        "project": state["project"],
        "phase": phase,
        "phase_label": PHASE_LABELS.get(phase, phase),
        "progress": {"current": idx, "total": len(PHASE_ORDER)},
        "auto_limit": state.get("auto_limit", 0),
        "phases_completed": list(state.get("outputs", {}).keys()),
        "error_counts": state.get("error_counts", {}),
    }


@app.get("/sessions")
async def list_sessions():
    """Lista todas las sesiones activas — para el panel de OpenClaw."""
    import sqlite3
    from core.config import ENGRAM_DB_PATH
    from pathlib import Path

    db_path = ENGRAM_DB_PATH
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT chat_id, project, phase, updated_at FROM sessions ORDER BY updated_at DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return {"sessions": [dict(r) for r in rows]}
    except Exception:
        return {"sessions": []}


# ── Jarvis visual web ─────────────────────────────────────────────────────────

@app.get("/jarvis", response_class=HTMLResponse)
async def jarvis_ui():
    """Sirve el visual animado del Jarvis. Abrir en browser mientras corre el voice transport."""
    html_path = STATIC_DIR / "jarvis.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>jarvis.html no encontrado en static/</h1>", status_code=404)


@app.websocket("/ws/jarvis")
async def jarvis_ws(websocket: WebSocket):
    """WebSocket que recibe cambios de estado del voice transport y los empuja al browser."""
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        # Mandar estado inicial
        await websocket.send_json({"state": "idle", "text": ""})
        # Mantener conexión viva — el server empuja, el cliente solo escucha
        while True:
            try:
                await websocket.receive_text()   # ping keepalive del browser
            except WebSocketDisconnect:
                break
    except Exception:
        pass
    finally:
        _ws_clients.discard(websocket)
