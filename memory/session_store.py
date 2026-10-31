"""
Session Store — Estado de proyectos por chat_id
=================================================
Reemplaza el orchestrator_state.json con SQLite thread-safe.
Cada proyecto tiene su propio registro. Múltiples chats pueden
tener proyectos distintos sin colisión.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from core.config import ENGRAM_DB_PATH

DB_PATH = ENGRAM_DB_PATH


def _conn() -> sqlite3.Connection:
    os.makedirs(Path(DB_PATH).parent, exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_sessions():
    c = _conn()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            chat_id     TEXT PRIMARY KEY,
            project     TEXT NOT NULL DEFAULT 'nuevo_proyecto',
            phase       TEXT NOT NULL DEFAULT 'discovery',
            phase_index INTEGER NOT NULL DEFAULT 0,
            task_index  INTEGER NOT NULL DEFAULT 0,
            auto_limit  INTEGER NOT NULL DEFAULT 0,
            outputs     TEXT NOT NULL DEFAULT '{}',
            initial_prompt TEXT NOT NULL DEFAULT '',
            error_counts   TEXT NOT NULL DEFAULT '{}',
            updated_at  TEXT NOT NULL
        )
    """)
    c.commit()
    c.close()


def get(chat_id: str) -> dict:
    c = _conn()
    row = c.execute("SELECT * FROM sessions WHERE chat_id=?", (str(chat_id),)).fetchone()
    c.close()
    if not row:
        return _default(chat_id)
    d = dict(row)
    d["outputs"] = json.loads(d["outputs"])
    d["error_counts"] = json.loads(d["error_counts"])
    return d


def save(chat_id: str, state: dict):
    c = _conn()
    c.execute("""
        INSERT INTO sessions
            (chat_id, project, phase, phase_index, task_index, auto_limit,
             outputs, initial_prompt, error_counts, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(chat_id) DO UPDATE SET
            project=excluded.project,
            phase=excluded.phase,
            phase_index=excluded.phase_index,
            task_index=excluded.task_index,
            auto_limit=excluded.auto_limit,
            outputs=excluded.outputs,
            initial_prompt=excluded.initial_prompt,
            error_counts=excluded.error_counts,
            updated_at=excluded.updated_at
    """, (
        str(chat_id),
        state.get("project", "nuevo_proyecto"),
        state.get("phase", "discovery"),
        state.get("phase_index", 0),
        state.get("task_index", 0),
        state.get("auto_limit", 0),
        json.dumps(state.get("outputs", {})),
        state.get("initial_prompt", ""),
        json.dumps(state.get("error_counts", {})),
        datetime.utcnow().isoformat(),
    ))
    c.commit()
    c.close()


def reset(chat_id: str, project: str) -> dict:
    state = _default(chat_id)
    state["project"] = project
    save(chat_id, state)
    return state


def _default(chat_id: str) -> dict:
    return {
        "chat_id": str(chat_id),
        "project": "nuevo_proyecto",
        "phase": "discovery",
        "phase_index": 0,
        "task_index": 0,
        "auto_limit": 0,
        "outputs": {},
        "initial_prompt": "",
        "error_counts": {},
    }
