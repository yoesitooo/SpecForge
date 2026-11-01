"""
ENGRAM - Memoria persistente de SpecForge (SQLite + búsqueda FTS5)
=========================================================
Basado en el "Model Context Protocol (MCP)" descrito en el Marco Operativo SDD.
Utiliza SQLite con FTS5 para búsquedas de alta relevancia ("señales raras").

No guarda todo el historial (ruido). Captura quirúrgicamente:
  - Decisiones de diseño (por qué se eligió una solución)
  - Errores detectados (para no repetirlos)
  - Patrones establecidos (estándares del proyecto)
"""

import logging
import sqlite3
import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from core.config import ENGRAM_DB_PATH
DB_PATH = ENGRAM_DB_PATH
log = logging.getLogger(__name__)


def _get_conn() -> sqlite3.Connection:
    """Obtiene conexión a SQLite y asegura que FTS5 esté disponible."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Inicializa el esquema de la base de datos Engram.
    Llama esto una vez al arrancar el orquestador.
    """
    conn = _get_conn()
    cursor = conn.cursor()

    # Tabla principal de memorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engram (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            project     TEXT NOT NULL,
            rol         TEXT NOT NULL,
            tipo        TEXT NOT NULL CHECK(tipo IN ('decision','error','pattern','summary')),
            contenido   TEXT NOT NULL,
            metadata    TEXT DEFAULT '{}',
            hash        TEXT UNIQUE,
            timestamp   TEXT NOT NULL
        )
    """)

    # Tabla FTS5 para búsqueda de texto completo (Full Text Search)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS engram_fts
        USING fts5(
            project,
            rol,
            tipo,
            contenido,
            content='engram',
            content_rowid='id'
        )
    """)

    # Triggers para mantener FTS5 sincronizado automáticamente
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS engram_ai AFTER INSERT ON engram BEGIN
            INSERT INTO engram_fts(rowid, project, rol, tipo, contenido)
            VALUES (new.id, new.project, new.rol, new.tipo, new.contenido);
        END
    """)
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS engram_ad AFTER DELETE ON engram BEGIN
            INSERT INTO engram_fts(engram_fts, rowid, project, rol, tipo, contenido)
            VALUES ('delete', old.id, old.project, old.rol, old.tipo, old.contenido);
        END
    """)

    conn.commit()
    conn.close()
    log.debug(f"[ENGRAM] Base de datos inicializada en: {DB_PATH}")


def save_signal(project: str, rol: str, tipo: str, contenido: str, metadata: dict = None) -> int:
    """
    Guarda una 'señal' (decisión, error, patrón o summary) en Engram.
    Deduplica por hash del contenido para evitar ruido repetido.

    Args:
        project:   Nombre del proyecto (ej: 'LawFirmPro')
        rol:       Rol del agente que genera la señal (ej: 'spec_writer')
        tipo:      Tipo de señal: 'decision', 'error', 'pattern', 'summary'
        contenido: El texto de la señal (debe ser conciso, no el historial completo)
        metadata:  Dict opcional con contexto adicional

    Returns:
        ID del registro insertado (o -1 si era duplicado)
    """
    content_hash = hashlib.sha256(contenido.encode()).hexdigest()
    conn = _get_conn()
    cursor = conn.cursor()

    # Verificar si ya existe esta señal exacta (deduplicación)
    cursor.execute("SELECT id FROM engram WHERE hash = ?", (content_hash,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return -1  # Señal duplicada, no guardamos ruido

    cursor.execute("""
        INSERT INTO engram (project, rol, tipo, contenido, metadata, hash, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project,
        rol,
        tipo,
        contenido,
        json.dumps(metadata or {}),
        content_hash,
        datetime.now(timezone.utc).isoformat()
    ))

    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log.debug(f"[ENGRAM] OK: Senal guardada [{tipo.upper()}] por {rol} en proyecto '{project}' (ID: {inserted_id})")
    return inserted_id


def retrieve_context(project: str, limit: int = 10) -> str:
    """
    Recupera las señales más recientes de un proyecto para inyectar como contexto.
    El Orquestador usa esto antes de lanzar un subagente para que tenga memoria.

    Returns:
        String formateado listo para incluir en un system prompt.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rol, tipo, contenido, timestamp
        FROM engram
        WHERE project = ?
        ORDER BY id DESC
        LIMIT ?
    """, (project, limit))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No hay memoria previa para este proyecto."

    lines = [f"=== MEMORIA ENGRAM: {project} ==="]
    for row in reversed(rows):  # Orden cronológico
        ts = row["timestamp"][:16].replace("T", " ")
        lines.append(f"[{ts}] [{row['tipo'].upper()}] ({row['rol']}): {row['contenido']}")
    return "\n".join(lines)


def list_signals(project: str, limit: int = 10) -> list:
    """
    Recupera las señales crudas (lista de tuplas) de un proyecto.
    Útil para el orquestador cuando necesita procesar la memoria programáticamente.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rol, tipo, contenido, timestamp
        FROM engram
        WHERE project = ?
        ORDER BY id DESC
        LIMIT ?
    """, (project, limit))
    rows = cursor.fetchall()
    conn.close()
    return [(r["rol"], r["tipo"], r["contenido"], r["timestamp"]) for r in rows]


def _fts_escape(query: str) -> str:
    """
    Convierte la query a tokens FTS5 seguros.
    FTS5 tokeniza con unicode61 (split en no-alfanumérico), así que
    "Next.js" → "Next" + "js". Buscamos cada token individualmente con OR.
    """
    import re
    tokens = re.findall(r'[a-zA-Z0-9À-ɏ]+', query)
    if not tokens:
        return '""'
    # Cada token entre comillas para evitar conflictos con operadores FTS5
    return " OR ".join(f'"{t}"' for t in tokens)


def search_signals(query: str, project: str = None, limit: int = 5) -> str:
    """
    Busca señales relevantes por texto completo (FTS5).
    Permite recuperar 'señales raras' — decisiones tomadas hace semanas.

    Args:
        query:   Término de búsqueda (ej: 'autenticación JWT', 'error SQLite')
        project: Filtrar por proyecto (opcional)
        limit:   Máximo de resultados

    Returns:
        String formateado con los resultados más relevantes.
    """
    safe_query = _fts_escape(query)
    conn = _get_conn()
    cursor = conn.cursor()

    if project:
        cursor.execute("""
            SELECT e.rol, e.tipo, e.contenido, e.timestamp
            FROM engram_fts f
            JOIN engram e ON f.rowid = e.id
            WHERE engram_fts MATCH ? AND e.project = ?
            ORDER BY rank
            LIMIT ?
        """, (safe_query, project, limit))
    else:
        cursor.execute("""
            SELECT e.project, e.rol, e.tipo, e.contenido, e.timestamp
            FROM engram_fts f
            JOIN engram e ON f.rowid = e.id
            WHERE engram_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (safe_query, limit))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return f"[ENGRAM] Sin resultados para: '{query}'"

    lines = [f"=== ENGRAM SEARCH: '{query}' ==="]
    for row in rows:
        ts = row["timestamp"][:16].replace("T", " ")
        proj = row["project"] if "project" in row.keys() else project
        lines.append(f"[{ts}] [{proj}] [{row['tipo'].upper()}] ({row['rol']}): {row['contenido']}")
    return "\n".join(lines)


def engram_sync(output_path: str = None):
    """
    Exporta la base de datos Engram a JSON para Git Sync.
    El equipo puede hacer commit de este archivo para compartir la memoria institucional.
    """
    if output_path is None:
        output_path = str(Path(DB_PATH).parent / "engram_export.json")

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM engram ORDER BY id")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    log.debug(f"[ENGRAM] SYNC: Sincronizacion exportada: {len(rows)} senales -> {output_path}")
    return output_path


def migrate_from_json(json_path: str, project: str = "migrated"):
    """
    Migra datos del antiguo project_state.json al nuevo sistema Engram.
    Solo se ejecuta una vez durante la transición.
    """
    if not os.path.exists(json_path):
        log.debug(f"[ENGRAM] No se encontró {json_path}, nada que migrar.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        old_state = json.load(f)

    project_name = old_state.get("project_name", project)
    phase = old_state.get("phase", "unknown")
    context = old_state.get("context", "")
    history = old_state.get("history", [])

    # Guardar la fase como un patrón
    if phase:
        save_signal(project_name, "orchestrator", "pattern",
                    f"Proyecto estaba en fase: {phase} al momento de la migración")

    # Guardar el contexto como summary
    if context:
        save_signal(project_name, "orchestrator", "summary",
                    f"Contexto previo del proyecto:\n{context[:500]}")  # Máx 500 chars

    # Guardar el historial resumido
    for entry in history[-5:]:  # Solo los últimos 5 mensajes
        save_signal(project_name, "director_legacy", "summary", entry)

    log.debug(f"[ENGRAM] OK: Migracion completada desde {json_path} -> proyecto '{project_name}'")


if __name__ == "__main__":
    # Test de integración
    init_db()
    save_signal("TestProject", "spec_writer", "decision",
                "Se usará SQLite en lugar de PostgreSQL por simplicidad de deploy")
    save_signal("TestProject", "disenador", "pattern",
                "Todos los endpoints REST deben seguir el formato /api/v1/recurso")
    save_signal("TestProject", "verificador", "error",
                "Error detectado: falta validación de email en el formulario de contacto")

    log.debug("\n" + retrieve_context("TestProject"))
    log.debug("\n" + search_signals("SQLite", project="TestProject"))

    engram_sync("/tmp/engram_test_export.json")
    log.debug("[ENGRAM] ✅ Test completado exitosamente.")
