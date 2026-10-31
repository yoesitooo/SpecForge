"""
File Search — buscar archivos en el computador
===============================================
Busca en Desktop, Documents, Downloads y el proyecto por defecto.
"""

import logging
from pathlib import Path

log = logging.getLogger(__name__)

SEARCH_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "OneDrive" / "Escritorio",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Documents" / "Jarvis",
]


def find_files(query: str, extension: str = "") -> str:
    """
    Busca archivos por nombre o extensión.
    query: nombre parcial del archivo
    extension: filtrar por extensión (.pdf, .py, .docx, etc.)
    """
    query_low = query.lower().strip()
    ext = extension.lower().strip().lstrip(".")
    results: list[Path] = []

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        try:
            pattern = f"*.{ext}" if ext else "*"
            for p in root.rglob(pattern):
                if p.is_file() and (not query_low or query_low in p.name.lower()):
                    results.append(p)
                    if len(results) >= 15:
                        break
        except PermissionError:
            continue

    if not results:
        msg = f"No encontré archivos"
        if query_low:
            msg += f" con '{query}'"
        if ext:
            msg += f" de tipo .{ext}"
        return msg + "."

    lines = [f"{i+1}. {p.name}  ({_size(p)})  →  {p.parent}" for i, p in enumerate(results[:10])]
    header = f"{len(results)} archivo(s) encontrado(s):"
    return header + "\n" + "\n".join(lines)


def read_text_file(filepath: str) -> str:
    """Lee un archivo de texto y retorna su contenido (para leer en voz alta)."""
    p = Path(filepath)

    # Buscar en la carpeta de Jarvis si no es ruta absoluta
    if not p.is_absolute():
        candidate = Path.home() / "Documents" / "Jarvis" / filepath
        if candidate.exists():
            p = candidate

    if not p.exists():
        return f"No encontré el archivo '{filepath}'."

    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if len(text) > 2000:
            text = text[:2000] + "... (texto truncado)"
        return text.strip() or "El archivo está vacío."
    except Exception as e:
        return f"No pude leer el archivo: {e}"


def open_in_explorer(path: str = "") -> str:
    """Abre el Explorador de Windows en una carpeta."""
    import subprocess
    target = path or str(Path.home() / "Documents" / "Jarvis")
    try:
        subprocess.Popen(["explorer", target], shell=True)
        return f"Abriendo explorador en {target}"
    except Exception as e:
        return f"Error: {e}"


def _size(p: Path) -> str:
    try:
        b = p.stat().st_size
        if b > 1_000_000:
            return f"{b/1e6:.1f} MB"
        if b > 1_000:
            return f"{b/1e3:.0f} KB"
        return f"{b} B"
    except Exception:
        return "?"
