"""
Ejecutar comandos de prueba y leer sus fallos
=============================================
Se ejecutan SIN shell (cada comando se divide con shlex). Se permite encadenar
con '&&' (p. ej. "npm install && npm test"), que se interpreta aquí, no en una shell.
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

MAX_SALIDA = 8_000  # se guarda el final de la salida, que es donde suelen estar los errores


@dataclass
class ResultadoPrueba:
    comando: str
    ok: bool
    codigo: int
    salida: str


async def correr(comando: str, cwd: str | Path, timeout: float = 900) -> ResultadoPrueba:
    salida_total = []
    codigo = 0
    for parte in [p.strip() for p in comando.split("&&") if p.strip()]:
        args = shlex.split(parte, posix=os.name != "nt")
        ejecutable = shutil.which(args[0]) or args[0]
        try:
            proc = await asyncio.create_subprocess_exec(
                ejecutable, *args[1:],
                cwd=str(cwd),
                # Sin caché de bytecode: un archivo editado en el mismo segundo y con el mismo
                # tamaño haría que Python ejecute la versión vieja y el arreglo parecería fallar.
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            return ResultadoPrueba(comando, False, 127, f"No se encontró el programa '{args[0]}'.")
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return ResultadoPrueba(comando, False, 124, f"'{parte}' superó {timeout:.0f} s.")
        salida_total.append(f"$ {parte}\n{out.decode('utf-8', errors='replace')}")
        codigo = proc.returncode or 0
        if codigo != 0:
            break
    texto = "\n".join(salida_total)
    if len(texto) > MAX_SALIDA:
        texto = "... [salida recortada]\n" + texto[-MAX_SALIDA:]
    return ResultadoPrueba(comando, codigo == 0, codigo, texto)


_PATRONES = [
    re.compile(r'File "([^"]+)", line (\d+)'),                         # traceback de Python
    re.compile(r"^([\w./\\-]+\.py):(\d+):", re.MULTILINE),               # pytest
    re.compile(r"\(?([\w./\\@-]+\.(?:[cm]?[jt]sx?)):(\d+):\d+\)?"),      # Node / TypeScript
]


def archivos_en_traza(salida: str, raiz: str | Path) -> list[str]:
    """Archivos del proyecto que aparecen en la traza del error, del más reciente al más antiguo."""
    raiz = Path(raiz).resolve()
    vistos: list[str] = []
    for patron in _PATRONES:
        for m in patron.finditer(salida):
            p = Path(m.group(1))
            p = (p if p.is_absolute() else raiz / p).resolve()
            try:
                rel = p.relative_to(raiz).as_posix()
            except ValueError:
                continue  # librerías fuera del proyecto
            if p.is_file() and "node_modules" not in rel and ".venv" not in rel and rel not in vistos:
                vistos.append(rel)
    # Lo más profundo de la traza suele estar más cerca de la causa
    return list(reversed(vistos))
