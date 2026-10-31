"""
Personal Memory — preferencias y hechos del usuario
=====================================================
Guarda cosas que Jarvis debe recordar entre sesiones:
  - Preferencias ("le gusta el reggaetón para trabajar")
  - Hechos personales ("trabaja en un startup de IA")
  - Patrones de uso ("siempre codea de noche")
Usa la misma DB de Engram para no tener archivos extra.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from core.config import ENGRAM_DB_PATH

log = logging.getLogger(__name__)
DB = ENGRAM_DB_PATH


def _conn() -> sqlite3.Connection:
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = _conn()
    c.execute("""
        CREATE TABLE IF NOT EXISTS personal_memory (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            category   TEXT NOT NULL DEFAULT 'general',
            fact       TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    c.commit()
    c.close()


def remember(fact: str, category: str = "general") -> str:
    """Guarda un hecho. Retorna confirmación."""
    try:
        init()
        c = _conn()
        c.execute(
            "INSERT INTO personal_memory (category, fact, created_at) VALUES (?,?,?)",
            (category, fact.strip(), datetime.now().isoformat())
        )
        c.commit()
        c.close()
        log.info(f"[MEMORY] Recordado [{category}]: {fact[:60]}")
        return f"Guardado: {fact[:80]}"
    except Exception as e:
        log.error(f"[MEMORY] Error guardando: {e}")
        return f"No pude guardar: {e}"


def recall(query: str = "", limit: int = 10) -> list[dict]:
    """Recupera hechos. Si query vacío, retorna los más recientes."""
    try:
        init()
        c = _conn()
        if query:
            q = f"%{query.lower()}%"
            rows = c.execute(
                "SELECT * FROM personal_memory WHERE LOWER(fact) LIKE ? OR LOWER(category) LIKE ? ORDER BY created_at DESC LIMIT ?",
                (q, q, limit)
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM personal_memory ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        c.close()
        return [dict(r) for r in rows]
    except Exception as e:
        log.error(f"[MEMORY] Error recuperando: {e}")
        return []


def recall_as_text(query: str = "", limit: int = 8) -> str:
    """Versión formateada para incluir en prompts."""
    facts = recall(query, limit)
    if not facts:
        return "No hay recuerdos guardados aún."
    lines = [f"- [{f['category']}] {f['fact']}" for f in facts]
    return "\n".join(lines)


def forget(fact_id: int) -> str:
    """Elimina un hecho por ID."""
    try:
        init()
        c = _conn()
        c.execute("DELETE FROM personal_memory WHERE id=?", (fact_id,))
        c.commit()
        c.close()
        return f"Olvidé el recuerdo #{fact_id}"
    except Exception as e:
        return f"Error: {e}"
