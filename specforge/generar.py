"""
Modo GENERAR — de una idea a un proyecto, con especificaciones primero
=====================================================================

  1. Descubrimiento   preguntas que cambian el alcance (opcional)
  2. Requisitos       historias de usuario + criterios EARS + casos de uso
  3. Diseño           arquitectura, modelo de datos, CONTRATOS, comandos
  4. Tareas           porciones de funcionalidad con dueño de archivos y dependencias
  5. Implementación   un agente por tarea; las tareas de una misma ola corren en paralelo
  6. Verificación     corre las pruebas del proyecto (opcional) y, si fallan, el modo reparar
  7. Revisión         matriz de trazabilidad (criterio → tarea → archivos) + revisión del modelo

Ahorro de tokens: cada agente de implementación recibe SOLO sus historias,
sus criterios, los contratos y los archivos que declara leer — no todo el historial.
Todos los documentos quedan en <proyecto>/specs/.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable

from core.config import MAX_PARALELO, WORKSPACES_PATH
from memory import engram
from skills import registry as skills

from . import llm, planificador, prompts
from .artefactos import Diseno, Plan, Requisitos, Tarea, a_dict
from .espacio import Espacio, extraer_archivos

log = logging.getLogger(__name__)

PreguntarUsuario = Callable[[list[str]], Awaitable[list[str]]]


@dataclass
class ResultadoTarea:
    id: str
    escritos: list[str] = field(default_factory=list)
    rechazados: list[str] = field(default_factory=list)   # archivos de otra tarea: no se escriben
    faltantes: list[str] = field(default_factory=list)    # declarados pero no entregados
    error: str = ""
    contexto_chars: int = 0

    @property
    def ok(self) -> bool:
        return not self.error and not self.faltantes


@dataclass
class Informe:
    proyecto: Path
    requisitos: Requisitos
    diseno: Diseno
    plan: Plan
    olas: list[list[str]]
    tareas: dict[str, ResultadoTarea]
    verificacion: dict | None = None
    revision: dict | None = None


def nombre_proyecto(texto: str) -> str:
    limpio = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return (limpio[:40].rstrip("-") or "proyecto")


class Generador:
    def __init__(
        self,
        idea: str,
        nombre: str | None = None,
        carpeta: str | Path | None = None,
        preguntar_usuario: PreguntarUsuario | None = None,
        paralelo: int = MAX_PARALELO,
        avisar: Callable[[str], None] = print,
    ):
        self.idea = idea.strip()
        self.nombre = nombre or nombre_proyecto(idea)
        self.espacio = Espacio(Path(carpeta or WORKSPACES_PATH) / self.nombre)
        self.preguntar_usuario = preguntar_usuario
        self.paralelo = max(1, paralelo)
        self.avisar = avisar

    # ── utilidades ──────────────────────────────────────────────────────────

    def _guardar(self, nombre: str, datos: dict, markdown: str) -> None:
        specs = self.espacio.raiz / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / f"{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        (specs / f"{nombre}.md").write_text(markdown, encoding="utf-8")

    # ── etapas ──────────────────────────────────────────────────────────────

    async def descubrir(self) -> str:
        brief = f"Idea: {self.idea}"
        if not self.preguntar_usuario:
            return brief
        preguntas = await llm.preguntar_json(
            "descubrimiento", prompts.DESCUBRIMIENTO, self.idea,
            lambda d: [str(p) for p in d["preguntas"]][:4],
        )
        if preguntas:
            respuestas = await self.preguntar_usuario(preguntas)
            brief += "\n" + "\n".join(f"- {p}\n  → {r or 'sin respuesta'}" for p, r in zip(preguntas, respuestas))
        return brief

    async def especificar(self, brief: str) -> Requisitos:
        self.avisar("📋 Requisitos: historias de usuario, criterios y casos de uso…")
        req = await llm.preguntar_json("requisitos", prompts.REQUISITOS, brief, Requisitos.desde_dict)
        self._guardar("requisitos", a_dict(req), req.a_markdown())
        return req

    async def disenar(self, brief: str, req: Requisitos) -> Diseno:
        self.avisar("🏗️  Diseño: arquitectura y contratos…")
        user = f"{brief}\n\n{req.a_markdown()}{skills.inject(self.idea)}"
        dis = await llm.preguntar_json("diseno", prompts.DISENO, user, Diseno.desde_dict)
        self._guardar("diseno", a_dict(dis), dis.a_markdown())
        try:  # las decisiones quedan en la memoria para futuras reparaciones del proyecto
            engram.init_db()
            for d in dis.decisiones:
                engram.save_signal(self.nombre, "diseno", "decision", f"{d.get('decision')}: {d.get('motivo')}")
        except Exception:
            pass
        return dis

    async def planificar(self, req: Requisitos, dis: Diseno) -> tuple[Plan, list[list[Tarea]]]:
        self.avisar("🧩 Tareas: porciones de funcionalidad y orden en paralelo…")
        criterios = "\n".join(f"- {c.id}: {c.texto}" for h in req.historias for c in h.criterios)
        historias = "\n".join(f"- {h.id}: {h.quiero}" for h in req.historias)
        user = f"Historias:\n{historias}\n\nCriterios:\n{criterios}\n\n{dis.a_markdown()}"
        plan = await llm.preguntar_json("tareas", prompts.TAREAS, user, lambda d: Plan.desde_dict(d, req))
        if plan.criterios_sin_cubrir:
            self.avisar(f"   Faltan criterios por cubrir ({', '.join(plan.criterios_sin_cubrir)}); se pide corregir el plan.")
            user += f"\n\nIMPORTANTE: tu plan anterior dejó sin cubrir {plan.criterios_sin_cubrir}. Cúbrelos."
            plan = await llm.preguntar_json("tareas", prompts.TAREAS, user, lambda d: Plan.desde_dict(d, req))
        ordenadas = planificador.olas(plan.tareas)
        ids_olas = [[t.id for t in ola] for ola in ordenadas]
        self._guardar("tareas", {**a_dict(plan), "olas": ids_olas}, plan.a_markdown(ids_olas))
        return plan, ordenadas

    def contexto_tarea(self, t: Tarea, req: Requisitos, dis: Diseno) -> str:
        """Lo mínimo que un agente necesita para su tarea (ahorro de tokens)."""
        historias = [h for h in req.historias if h.id in t.historias or any(c.id in t.criterios for c in h.criterios)]
        bloques = [
            f"# Proyecto\n{req.resumen}\nStack: {json.dumps(dis.stack, ensure_ascii=False)}",
            dis.contratos_markdown(),
            "# Estructura completa del proyecto (otras tareas escriben los demás archivos)\n"
            + "\n".join(f"- {r}" for r in dis.estructura),
            "# Historias y criterios que cubre tu tarea\n" + "\n".join(
                f"- {h.id}: como {h.como}, quiero {h.quiero}\n"
                + "\n".join(f"  - {c.id}: {c.texto}" for c in h.criterios if c.id in t.criterios or not t.criterios)
                for h in historias
            ),
        ]
        leidos = [(r, self.espacio.leer(r)) for r in t.lee]
        if any(c is not None for _, c in leidos):
            bloques.append("# Archivos de otras tareas que necesitas (solo lectura)\n" + "\n".join(
                f"--- {r} ---\n{c}" for r, c in leidos if c is not None
            ))
        bloques.append(
            f"# TU TAREA: {t.id} — {t.titulo}\n{t.objetivo}\n"
            f"Archivos que debes entregar (solo estos): {', '.join(t.archivos)}\n"
            "Lista cuando:\n" + "\n".join(f"- {x}" for x in t.listo_cuando)
        )
        return "\n\n".join(bloques)

    async def implementar_tarea(self, t: Tarea, req: Requisitos, dis: Diseno) -> ResultadoTarea:
        res = ResultadoTarea(t.id)
        user = self.contexto_tarea(t, req, dis)
        res.contexto_chars = len(user)
        try:
            archivos = {}
            for intento in range(2):
                texto = await llm.preguntar("implementacion", prompts.IMPLEMENTACION, user, max_tokens=16000)
                archivos = extraer_archivos(texto)
                if archivos:
                    break
                user += "\n\nTu respuesta no tenía bloques === FILE: ... ===. Entrega los archivos en ese formato."
        except Exception as e:  # una tarea fallida no detiene las demás
            res.error = str(e)
            return res
        for ruta, contenido in archivos.items():
            if ruta in t.archivos:
                self.espacio.escribir(ruta, contenido)
                res.escritos.append(ruta)
            else:
                res.rechazados.append(ruta)
        res.faltantes = [a for a in t.archivos if a not in archivos]
        return res

    async def implementar(self, olas_: list[list[Tarea]], req: Requisitos, dis: Diseno) -> dict[str, ResultadoTarea]:
        resultados: dict[str, ResultadoTarea] = {}
        limite = asyncio.Semaphore(self.paralelo)

        async def con_limite(t: Tarea) -> ResultadoTarea:
            async with limite:
                return await self.implementar_tarea(t, req, dis)

        for i, ola in enumerate(olas_, 1):
            self.avisar(f"💻 Ola {i}/{len(olas_)}: {', '.join(t.id for t in ola)} en paralelo…")
            for r in await asyncio.gather(*(con_limite(t) for t in ola)):
                resultados[r.id] = r
                estado = "✓" if r.ok else "⚠"
                detalle = r.error or (f"faltan {r.faltantes}" if r.faltantes else f"{len(r.escritos)} archivo(s)")
                self.avisar(f"   {estado} {r.id}: {detalle}")
        return resultados

    async def revisar(self, req: Requisitos, plan: Plan, tareas: dict[str, ResultadoTarea]) -> dict:
        self.avisar("🔬 Revisión final contra los criterios…")
        codigo = "\n\n".join(
            f"--- {r} ---\n{self.espacio.leer(r, max_chars=6000)}"
            for t in plan.tareas for r in tareas.get(t.id, ResultadoTarea(t.id)).escritos
        )[:60_000]
        user = f"{req.a_markdown()}\n\n# Código\n{codigo}"
        try:
            return await llm.preguntar_json("revision", prompts.REVISION, user, _validar_revision)
        except Exception as e:
            return {"veredicto": "sin_revision", "hallazgos": [], "criterios_dudosos": [], "error": str(e)}

    # ── proceso completo ────────────────────────────────────────────────────

    async def ejecutar(self, verificar: bool = False, reparar: bool = False) -> Informe:
        self.espacio.raiz.mkdir(parents=True, exist_ok=True)
        brief = await self.descubrir()
        req = await self.especificar(brief)
        dis = await self.disenar(brief, req)
        plan, olas_ = await self.planificar(req, dis)
        tareas = await self.implementar(olas_, req, dis)

        verificacion = None
        if verificar and dis.comandos.get("probar"):
            from .reparar import Reparador, preparar_git
            from .pruebas import correr

            preparar_git(self.espacio.raiz, "SpecForge: proyecto generado")
            comando = " && ".join(c for c in (dis.comandos.get("instalar"), dis.comandos["probar"]) if c)
            self.avisar(f"🧪 Verificando: {comando}")
            r = await correr(comando, self.espacio.raiz)
            verificacion = {"comando": comando, "ok": r.ok, "salida": r.salida[-3000:]}
            if not r.ok and reparar:
                self.avisar("🔧 Las pruebas fallan: pasando al modo reparar…")
                rep = await Reparador(self.espacio.raiz, comando, avisar=self.avisar).ejecutar()
                verificacion["reparacion"] = rep.resumen()

        revision = await self.revisar(req, plan, tareas)
        informe = Informe(self.espacio.raiz, req, dis, plan, [[t.id for t in o] for o in olas_], tareas, verificacion, revision)
        (self.espacio.raiz / "specs" / "informe.md").write_text(informe_markdown(informe), encoding="utf-8")
        return informe


def _validar_revision(d: dict) -> dict:
    if d.get("veredicto") not in ("aprobado", "con_observaciones", "rechazado"):
        raise ValueError("veredicto debe ser aprobado, con_observaciones o rechazado")
    d.setdefault("hallazgos", [])
    d.setdefault("criterios_dudosos", [])
    return d


def informe_markdown(inf: Informe) -> str:
    l = [f"# Informe — {inf.proyecto.name}", ""]
    l += ["## Trazabilidad", "", "| Criterio | Tarea | Archivos | Estado |", "|---|---|---|---|"]
    for h in inf.requisitos.historias:
        for c in h.criterios:
            tarea = next((t for t in inf.plan.tareas if c.id in t.criterios), None)
            if tarea is None:
                l.append(f"| {c.id} | — | — | ⚠️ sin tarea |")
                continue
            r = inf.tareas.get(tarea.id)
            estado = "✅" if r and r.ok else "⚠️"
            l.append(f"| {c.id} | {tarea.id} | {', '.join(r.escritos) if r else '—'} | {estado} |")
    l += ["", "## Tareas", ""]
    for t in inf.plan.tareas:
        r = inf.tareas.get(t.id)
        if r is None:
            continue
        extra = []
        if r.faltantes:
            extra.append(f"faltan {', '.join(r.faltantes)}")
        if r.rechazados:
            extra.append(f"intentó escribir archivos ajenos: {', '.join(r.rechazados)}")
        if r.error:
            extra.append(f"error: {r.error}")
        estado = ("ok" + (f" ({'; '.join(extra)})" if extra else "")) if r.ok else "; ".join(extra)
        l.append(f"- **{t.id}** {t.titulo} — {estado} · contexto enviado: {r.contexto_chars:,} caracteres")
    l += ["", f"Olas en paralelo: {' → '.join('[' + ', '.join(o) + ']' for o in inf.olas)}", ""]
    if inf.verificacion:
        v = inf.verificacion
        l += ["## Verificación", "", f"`{v['comando']}` → {'✅ pasan' if v['ok'] else '❌ fallan'}", ""]
        if v.get("reparacion"):
            l += ["### Reparación", "", v["reparacion"], ""]
    if inf.revision:
        rv = inf.revision
        l += ["## Revisión", "", f"Veredicto: **{rv.get('veredicto')}**", ""]
        l += [f"- [{x.get('severidad')}] `{x.get('archivo')}` — {x.get('problema')} → {x.get('sugerencia')}" for x in rv.get("hallazgos", [])]
        if rv.get("criterios_dudosos"):
            l += ["", "Criterios dudosos: " + "; ".join(map(str, rv["criterios_dudosos"]))]
    return "\n".join(l) + "\n"
