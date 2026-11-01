"""
Modo REPARAR — reproducir, localizar, parchear y validar con pruebas reales
==========================================================================
Basado en el enfoque "Agentless" (Xia et al., 2024): un proceso fijo y
simple supera a agentes autónomos complejos, y cuesta menos.

  1. Reproducir  corre el comando de pruebas; si pasa, no hay nada que arreglar
  2. Localizar   archivos de la traza del error + el modelo elige los sospechosos
  3. Parche      ediciones mínimas SEARCH/REPLACE sobre esos archivos
  4. Validar     vuelve a correr las pruebas; si fallan, repite con la nueva salida

Seguridad: trabaja en una rama nueva de git (no toca tu rama actual) y exige
que el repositorio no tenga cambios sin guardar. Si no logra arreglarlo,
deshace todo y vuelve a tu rama.
"""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from memory import engram

from . import llm, prompts
from .espacio import Espacio, extraer_ediciones
from .pruebas import ResultadoPrueba, archivos_en_traza, correr

MAX_SOSPECHOSOS = 5


def firma_error(salida: str, max_lineas: int = 3) -> str:
    """Las líneas que identifican el error (para buscar y recordar arreglos parecidos)."""
    claves = [l.strip() for l in salida.splitlines()
              if any(k in l for k in ("Error", "FAILED", "assert", "Exception", "✕", "failed"))]
    return " | ".join(dict.fromkeys(claves[-max_lineas:]))[:400]


class ErrorReparacion(RuntimeError):
    pass


def _git(raiz: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise ErrorReparacion(f"git {' '.join(args)} falló: {r.stderr.strip()}")
    return r.stdout.strip()


def _commit(raiz: Path, mensaje: str) -> None:
    autor = [] if _git(raiz, "config", "user.name", check=False) else ["-c", "user.name=SpecForge", "-c", "user.email=specforge@localhost"]
    subprocess.run(["git", "-C", str(raiz), *autor, "commit", "-q", "-m", mensaje], capture_output=True, check=True)


def preparar_git(raiz: Path, mensaje: str) -> None:
    """Para proyectos recién generados: inicia git y guarda el estado inicial."""
    if not (Path(raiz) / ".git").exists():
        _git(Path(raiz), "init", "-q")
    _git(Path(raiz), "add", "-A")
    if _git(Path(raiz), "status", "--porcelain"):
        _commit(Path(raiz), mensaje)


@dataclass
class Intento:
    numero: int
    sospechosos: list[str]
    hipotesis: str
    explicacion: str
    editados: list[str]
    errores_edicion: list[str]
    prueba: ResultadoPrueba | None


@dataclass
class ResultadoReparacion:
    estado: str  # "ya_pasaba" | "arreglado" | "sin_arreglo"
    rama: str = ""
    intentos: list[Intento] = field(default_factory=list)
    diff: str = ""

    def resumen(self) -> str:
        if self.estado == "ya_pasaba":
            return "Las pruebas ya pasaban: no había nada que arreglar."
        l = [f"Estado: **{'arreglado ✅' if self.estado == 'arreglado' else 'sin arreglo ❌'}** en {len(self.intentos)} intento(s)."]
        if self.rama:
            l.append(f"Rama: `{self.rama}`" + (" (con el arreglo en un commit)" if self.estado == "arreglado" else " (eliminada; tu código quedó como estaba)"))
        for it in self.intentos:
            l.append(f"\n**Intento {it.numero}** — sospechosos: {', '.join(it.sospechosos) or '—'}")
            if it.hipotesis:
                l.append(f"- Hipótesis: {it.hipotesis}")
            if it.explicacion:
                l.append(f"- Causa: {it.explicacion}")
            l.append(f"- Editados: {', '.join(it.editados) or 'ninguno'}")
            l += [f"- ⚠ {e}" for e in it.errores_edicion]
            if it.prueba:
                l.append(f"- Pruebas: {'pasan ✅' if it.prueba.ok else 'fallan ❌'}")
        return "\n".join(l)


class Reparador:
    def __init__(
        self,
        raiz: str | Path,
        comando_prueba: str,
        max_intentos: int = 3,
        avisar: Callable[[str], None] = print,
    ):
        self.raiz = Path(raiz).resolve()
        self.espacio = Espacio(self.raiz)
        self.comando = comando_prueba
        self.max_intentos = max_intentos
        self.avisar = avisar

    def recordar(self, salida: str) -> str:
        """Arreglos anteriores de errores parecidos en este repositorio (memoria FTS5)."""
        firma = firma_error(salida)
        if not firma:
            return ""
        try:
            encontrado = engram.search_signals(firma, project=self.raiz.name, limit=3)
        except Exception:  # la memoria es una ayuda, nunca un bloqueo
            return ""
        return "" if "Sin resultados" in encontrado else encontrado

    async def localizar(self, salida: str) -> tuple[list[str], str]:
        de_traza = archivos_en_traza(salida, self.raiz)
        archivos = self.espacio.listar()
        recuerdos = self.recordar(salida)
        user = (
            f"# Salida de las pruebas\n{salida}\n\n"
            + (f"# Arreglos anteriores parecidos en este repositorio\n{recuerdos}\n\n" if recuerdos else "")
            + 
            f"# Archivos que aparecen en la traza\n{de_traza}\n\n"
            "# Archivos del repositorio\n" + "\n".join(archivos)
        )

        def validar(d: dict) -> tuple[list[str], str]:
            elegidos = [a for a in d["archivos"] if a in archivos]
            return elegidos, str(d.get("hipotesis", ""))

        try:
            del_modelo, hipotesis = await llm.preguntar_json("localizar", prompts.LOCALIZAR, user, validar)
        except llm.RespuestaInvalida:
            del_modelo, hipotesis = [], ""
        sospechosos = list(dict.fromkeys(del_modelo + de_traza))[:MAX_SOSPECHOSOS]
        return sospechosos, hipotesis

    async def parchear(self, salida: str, sospechosos: list[str], hipotesis: str, previos: list[Intento]) -> tuple[str, list[str], list[str]]:
        contenidos = "\n\n".join(f"--- {r} ---\n{self.espacio.leer(r, max_chars=20_000)}" for r in sospechosos)
        historial = "".join(
            f"\n- Intento {it.numero}: editó {it.editados or 'nada'}; las pruebas siguieron fallando."
            for it in previos
        )
        user = (
            f"# Salida de las pruebas\n{salida}\n\n# Diagnóstico\n{hipotesis or 'sin hipótesis'}\n"
            + (f"\n# Intentos anteriores (no repitas lo mismo){historial}\n" if historial else "")
            + f"\n# Archivos sospechosos\n{contenidos}"
        )
        texto = await llm.preguntar("parche", prompts.PARCHE, user, max_tokens=8000)
        explicacion = texto.split("=== EDIT:")[0].strip()[:600]
        editados, errores = [], []
        for ed in extraer_ediciones(texto):
            try:
                self.espacio.aplicar(ed)
                editados.append(ed.ruta)
            except ValueError as e:
                errores.append(str(e))
        if not editados and not errores:
            errores.append("el modelo no devolvió ediciones en el formato pedido")
        return explicacion, sorted(set(editados)), errores

    async def ejecutar(self) -> ResultadoReparacion:
        if not (self.raiz / ".git").exists():
            raise ErrorReparacion("La carpeta no es un repositorio git. SpecForge trabaja en una rama aparte; ejecuta `git init` y haz un commit primero.")
        if _git(self.raiz, "status", "--porcelain", "--untracked-files=no"):
            raise ErrorReparacion("Hay cambios sin guardar. Haz commit o `git stash` antes de reparar, para no mezclarlos.")

        self.avisar(f"🧪 Reproduciendo: {self.comando}")
        prueba = await correr(self.comando, self.raiz)
        if prueba.ok:
            return ResultadoReparacion("ya_pasaba")
        salida_inicial = prueba.salida
        engram.init_db()

        rama_original = _git(self.raiz, "rev-parse", "--abbrev-ref", "HEAD")
        base = f"specforge/reparacion-{datetime.now():%Y%m%d-%H%M%S}"
        existentes = set(_git(self.raiz, "branch", "--list", f"{base}*", "--format=%(refname:short)").splitlines())
        rama = next(r for r in (base, *(f"{base}-{i}" for i in range(2, 100))) if r not in existentes)
        _git(self.raiz, "switch", "-q", "-c", rama)
        resultado = ResultadoReparacion("sin_arreglo", rama=rama)

        for n in range(1, self.max_intentos + 1):
            self.avisar(f"🔎 Intento {n}: localizando el error…")
            sospechosos, hipotesis = await self.localizar(prueba.salida)
            if not sospechosos:
                resultado.intentos.append(Intento(n, [], hipotesis, "", [], ["no se encontraron archivos sospechosos"], None))
                break
            self.avisar(f"🩹 Parcheando {', '.join(sospechosos)}…")
            explicacion, editados, errores = await self.parchear(prueba.salida, sospechosos, hipotesis, resultado.intentos)
            prueba = await correr(self.comando, self.raiz) if editados else prueba
            resultado.intentos.append(Intento(n, sospechosos, hipotesis, explicacion, editados, errores, prueba if editados else None))
            if editados and prueba.ok:
                resultado.estado = "arreglado"
                break

        if resultado.estado == "arreglado":
            resultado.diff = _git(self.raiz, "diff")
            tocados = sorted({r for it in resultado.intentos for r in it.editados})
            _git(self.raiz, "add", "--", *tocados)  # solo lo editado: no se cuelan cachés de las pruebas
            _commit(self.raiz, "SpecForge: arreglo validado con las pruebas\n\n" + resultado.resumen())
            final = resultado.intentos[-1]
            try:
                engram.save_signal(
                    self.raiz.name, "reparar", "error",
                    f"Error: {firma_error(salida_inicial)}. Causa: {final.explicacion or final.hipotesis}. "
                    f"Arreglo en: {', '.join(tocados)}.",
                )
            except Exception:
                pass
            self.avisar(f"✅ Arreglado. Revisa la rama {rama} y únela si te convence.")
        else:
            _git(self.raiz, "reset", "-q", "--hard")  # el parche solo edita archivos ya versionados
            _git(self.raiz, "switch", "-q", rama_original)
            _git(self.raiz, "branch", "-q", "-D", rama)
            self.avisar("❌ No se logró arreglar; tu código quedó exactamente como estaba.")
        return resultado


def correr_sincrono(raiz: str, comando: str, intentos: int = 3) -> ResultadoReparacion:
    return asyncio.run(Reparador(raiz, comando, intentos).ejecutar())
