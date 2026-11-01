"""
Espacio de trabajo — leer y escribir archivos del proyecto con seguridad
=======================================================================
Los modelos devuelven archivos y ediciones como texto. Aquí se interpretan y
se aplican solo dentro de la carpeta del proyecto (nada de rutas absolutas,
'..' ni .git).

Formatos que se piden al modelo:

  Archivo completo (modo generar):
      === FILE: src/app.py ===
      <contenido>
      === END FILE ===

  Edición puntual (modo reparar; el texto SEARCH debe aparecer UNA vez):
      === EDIT: src/app.py ===
      <<<<<<< SEARCH
      texto actual
      =======
      texto nuevo
      >>>>>>> REPLACE
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .artefactos import ruta_segura

_ARCHIVO = re.compile(r"^=== FILE: (.+?) ===\n(.*?)^=== END FILE ===", re.DOTALL | re.MULTILINE)
_EDICION = re.compile(
    r"^=== EDIT: (.+?) ===\n<<<<<<< SEARCH\n(.*?)^=======\n(.*?)^>>>>>>> REPLACE",
    re.DOTALL | re.MULTILINE,
)


@dataclass
class Edicion:
    ruta: str
    buscar: str
    reemplazar: str


def extraer_archivos(texto: str) -> dict[str, str]:
    archivos = {}
    for ruta, contenido in _ARCHIVO.findall(texto):
        archivos[ruta_segura(ruta)] = contenido
    return archivos


def extraer_ediciones(texto: str) -> list[Edicion]:
    return [Edicion(ruta_segura(r), b, n) for r, b, n in _EDICION.findall(texto)]


class Espacio:
    def __init__(self, raiz: str | Path):
        self.raiz = Path(raiz).resolve()

    def ruta(self, relativa: str) -> Path:
        destino = (self.raiz / ruta_segura(relativa)).resolve()
        if self.raiz not in destino.parents:
            raise ValueError(f"ruta fuera del proyecto: {relativa}")
        return destino

    def escribir(self, relativa: str, contenido: str) -> None:
        destino = self.ruta(relativa)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding="utf-8")
        if destino.suffix == ".py":
            # Borra el bytecode viejo: si la edición conserva tamaño y segundo de
            # modificación, Python podría seguir usando la versión anterior.
            for pyc in (destino.parent / "__pycache__").glob(f"{destino.stem}.*.pyc"):
                pyc.unlink(missing_ok=True)

    def leer(self, relativa: str, max_chars: int = 12_000) -> str | None:
        try:
            texto = self.ruta(relativa).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            return None
        if len(texto) > max_chars:
            return texto[:max_chars] + f"\n... [recortado: {len(texto) - max_chars} caracteres más]"
        return texto

    def aplicar(self, edicion: Edicion) -> None:
        """Aplica una edición si el texto buscado aparece exactamente una vez."""
        actual = self.leer(edicion.ruta, max_chars=10**9)
        if actual is None:
            raise ValueError(f"{edicion.ruta}: el archivo no existe")
        veces = actual.count(edicion.buscar)
        if veces != 1:
            raise ValueError(f"{edicion.ruta}: el texto a reemplazar aparece {veces} veces (debe ser 1)")
        self.escribir(edicion.ruta, actual.replace(edicion.buscar, edicion.reemplazar, 1))

    def listar(self, limite: int = 400) -> list[str]:
        ignorar = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "specs"}
        rutas = []
        for p in sorted(self.raiz.rglob("*")):
            rel = p.relative_to(self.raiz)
            if p.is_file() and not (set(rel.parts) & ignorar):
                rutas.append(rel.as_posix())
                if len(rutas) >= limite:
                    break
        return rutas
