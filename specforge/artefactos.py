"""
Artefactos del proceso — el "contrato" entre etapas
===================================================
Cada etapa produce un documento estructurado que la siguiente consume:

  requisitos  →  historias de usuario (con criterios EARS) + casos de uso
  diseño      →  arquitectura, modelo de datos, CONTRATOS y comandos
  tareas      →  plan con dependencias y archivos que cada tarea es dueña

Se validan al recibirlos (IDs únicos, referencias que existen, sin ciclos) y
se guardan como JSON (para la máquina) y Markdown (para las personas).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import PurePosixPath


def _lista(d: dict, clave: str) -> list:
    valor = d.get(clave, [])
    if not isinstance(valor, list):
        raise ValueError(f"'{clave}' debe ser una lista")
    return valor


def _texto(d: dict, clave: str) -> str:
    valor = d.get(clave)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"falta el campo de texto '{clave}'")
    return valor.strip()


def ruta_segura(ruta: str) -> str:
    """Ruta relativa dentro del proyecto: sin absolutas, sin '..', sin .git."""
    p = PurePosixPath(ruta.replace("\\", "/").strip())
    if not p.parts or p.is_absolute() or ".." in p.parts or p.parts[0] in (".git", "specs"):
        raise ValueError(f"ruta no permitida: '{ruta}'")
    return str(p)


# ─── Requisitos ──────────────────────────────────────────────────────────────


@dataclass
class Criterio:
    id: str
    texto: str  # EARS: "CUANDO <evento> EL SISTEMA DEBE <respuesta>"


@dataclass
class Historia:
    id: str
    como: str
    quiero: str
    para: str
    prioridad: str
    criterios: list[Criterio]


@dataclass
class CasoUso:
    id: str
    nombre: str
    actor: str
    precondiciones: list[str]
    flujo_principal: list[str]
    flujos_alternos: list[dict]  # {"condicion": str, "pasos": [str]}
    postcondiciones: list[str]
    historias: list[str]


@dataclass
class Requisitos:
    resumen: str
    historias: list[Historia]
    casos_uso: list[CasoUso]
    no_funcionales: list[str] = field(default_factory=list)

    @property
    def ids_criterios(self) -> list[str]:
        return [c.id for h in self.historias for c in h.criterios]

    @classmethod
    def desde_dict(cls, d: dict) -> "Requisitos":
        historias = []
        for h in _lista(d, "historias"):
            criterios = [Criterio(_texto(c, "id"), _texto(c, "texto")) for c in _lista(h, "criterios")]
            if not criterios:
                raise ValueError(f"la historia {h.get('id')} no tiene criterios de aceptación")
            historias.append(
                Historia(
                    id=_texto(h, "id"),
                    como=_texto(h, "como"),
                    quiero=_texto(h, "quiero"),
                    para=_texto(h, "para"),
                    prioridad=str(h.get("prioridad", "media")).lower(),
                    criterios=criterios,
                )
            )
        if not historias:
            raise ValueError("no hay historias de usuario")

        ids_h = {h.id for h in historias}
        casos = []
        for c in _lista(d, "casos_uso"):
            refs = [str(x) for x in _lista(c, "historias")]
            desconocidas = set(refs) - ids_h
            if desconocidas:
                raise ValueError(f"el caso de uso {c.get('id')} cita historias que no existen: {sorted(desconocidas)}")
            casos.append(
                CasoUso(
                    id=_texto(c, "id"),
                    nombre=_texto(c, "nombre"),
                    actor=_texto(c, "actor"),
                    precondiciones=[str(x) for x in _lista(c, "precondiciones")],
                    flujo_principal=[str(x) for x in _lista(c, "flujo_principal")],
                    flujos_alternos=[
                        {"condicion": _texto(f, "condicion"), "pasos": [str(p) for p in _lista(f, "pasos")]}
                        for f in _lista(c, "flujos_alternos")
                    ],
                    postcondiciones=[str(x) for x in _lista(c, "postcondiciones")],
                    historias=refs,
                )
            )
        req = cls(_texto(d, "resumen"), historias, casos, [str(x) for x in _lista(d, "no_funcionales")])
        _sin_duplicados([h.id for h in historias] + req.ids_criterios + [c.id for c in casos])
        return req

    def a_markdown(self) -> str:
        l = ["# Requisitos", "", self.resumen, "", "## Historias de usuario", ""]
        for h in self.historias:
            l += [f"### {h.id} · prioridad {h.prioridad}", "",
                  f"**Como** {h.como}, **quiero** {h.quiero}, **para** {h.para}.", "",
                  "Criterios de aceptación:", ""]
            l += [f"- **{c.id}** {c.texto}" for c in h.criterios] + [""]
        l += ["## Casos de uso", ""]
        for c in self.casos_uso:
            l += [f"### {c.id} — {c.nombre}", "", f"- **Actor:** {c.actor}",
                  f"- **Historias:** {', '.join(c.historias) or '—'}",
                  f"- **Precondiciones:** {'; '.join(c.precondiciones) or '—'}", "",
                  "**Flujo principal**", ""]
            l += [f"{i}. {p}" for i, p in enumerate(c.flujo_principal, 1)] + [""]
            for f in c.flujos_alternos:
                l += [f"**Alterno — {f['condicion']}**", ""] + [f"{i}. {p}" for i, p in enumerate(f["pasos"], 1)] + [""]
            l += [f"- **Postcondiciones:** {'; '.join(c.postcondiciones) or '—'}", ""]
        if self.no_funcionales:
            l += ["## Requisitos no funcionales", ""] + [f"- {x}" for x in self.no_funcionales] + [""]
        return "\n".join(l)


# ─── Diseño ──────────────────────────────────────────────────────────────────


@dataclass
class Diseno:
    resumen: str
    stack: dict
    componentes: list[dict]      # {"nombre", "responsabilidad"}
    modelo_datos: list[dict]     # {"entidad", "campos": [str]}
    contratos: list[dict]        # {"nombre", "tipo", "firma", "descripcion"}
    estructura: list[str]        # rutas de archivos previstas
    comandos: dict               # {"instalar", "probar", "ejecutar"}
    decisiones: list[dict] = field(default_factory=list)  # {"decision", "motivo"}

    @classmethod
    def desde_dict(cls, d: dict) -> "Diseno":
        contratos = _lista(d, "contratos")
        for c in contratos:
            _texto(c, "nombre"), _texto(c, "firma")
        comandos = d.get("comandos") or {}
        if not isinstance(comandos, dict):
            raise ValueError("'comandos' debe ser un objeto")
        return cls(
            resumen=_texto(d, "resumen"),
            stack=d.get("stack") or {},
            componentes=_lista(d, "componentes"),
            modelo_datos=_lista(d, "modelo_datos"),
            contratos=contratos,
            estructura=[ruta_segura(str(r)) for r in _lista(d, "estructura")],
            comandos={k: str(v) for k, v in comandos.items() if v},
            decisiones=_lista(d, "decisiones"),
        )

    def contratos_markdown(self) -> str:
        """Lo que TODAS las tareas deben respetar: se envía a cada agente."""
        l = ["## Contratos (respétalos exactamente)", ""]
        l += [f"- **{c['nombre']}** ({c.get('tipo', 'api')}): `{c['firma']}` — {c.get('descripcion', '')}" for c in self.contratos]
        if self.modelo_datos:
            l += ["", "## Modelo de datos", ""]
            l += [f"- **{e.get('entidad')}**: {', '.join(map(str, e.get('campos', [])))}" for e in self.modelo_datos]
        return "\n".join(l)

    def a_markdown(self) -> str:
        l = ["# Diseño", "", self.resumen, "", "## Stack", ""]
        l += [f"- **{k}:** {v if isinstance(v, str) else ', '.join(map(str, v))}" for k, v in self.stack.items()]
        l += ["", "## Componentes", ""] + [f"- **{c.get('nombre')}** — {c.get('responsabilidad')}" for c in self.componentes]
        l += ["", self.contratos_markdown(), "", "## Estructura de archivos", "", "```"] + self.estructura + ["```"]
        if self.comandos:
            l += ["", "## Comandos", ""] + [f"- **{k}:** `{v}`" for k, v in self.comandos.items()]
        if self.decisiones:
            l += ["", "## Decisiones", ""] + [f"- **{x.get('decision')}** — {x.get('motivo')}" for x in self.decisiones]
        return "\n".join(l) + "\n"


# ─── Tareas ──────────────────────────────────────────────────────────────────


@dataclass
class Tarea:
    id: str
    titulo: str
    objetivo: str
    historias: list[str]
    criterios: list[str]
    archivos: list[str]       # archivos que ESTA tarea crea o modifica (es su dueña)
    lee: list[str]            # archivos de otras tareas que necesita leer
    depende_de: list[str]
    listo_cuando: list[str]   # condiciones verificables


@dataclass
class Plan:
    tareas: list[Tarea]
    criterios_sin_cubrir: list[str] = field(default_factory=list)

    @classmethod
    def desde_dict(cls, d: dict, requisitos: Requisitos) -> "Plan":
        crudas = d.get("tareas") if isinstance(d, dict) else d
        if not isinstance(crudas, list) or not crudas:
            raise ValueError("no hay tareas")
        tareas = []
        for t in crudas:
            archivos = [ruta_segura(str(a)) for a in _lista(t, "archivos")]
            if not archivos:
                raise ValueError(f"la tarea {t.get('id')} no declara archivos")
            tareas.append(
                Tarea(
                    id=_texto(t, "id"),
                    titulo=_texto(t, "titulo"),
                    objetivo=_texto(t, "objetivo"),
                    historias=[str(x) for x in _lista(t, "historias")],
                    criterios=[str(x) for x in _lista(t, "criterios")],
                    archivos=archivos,
                    lee=[ruta_segura(str(a)) for a in _lista(t, "lee")],
                    depende_de=[str(x) for x in _lista(t, "depende_de")],
                    listo_cuando=[str(x) for x in _lista(t, "listo_cuando")],
                )
            )
        ids = [t.id for t in tareas]
        _sin_duplicados(ids)
        for t in tareas:
            faltan = set(t.depende_de) - set(ids)
            if faltan:
                raise ValueError(f"la tarea {t.id} depende de tareas que no existen: {sorted(faltan)}")
            ajenos = set(t.criterios) - set(requisitos.ids_criterios)
            if ajenos:
                raise ValueError(f"la tarea {t.id} cita criterios que no existen: {sorted(ajenos)}")
        duenos: dict[str, str] = {}
        for t in tareas:
            for a in t.archivos:
                if a in duenos:
                    raise ValueError(f"el archivo {a} lo reclaman {duenos[a]} y {t.id}; cada archivo tiene un solo dueño")
                duenos[a] = t.id
        _sin_ciclos(tareas)
        cubiertos = {c for t in tareas for c in t.criterios}
        return cls(tareas, [c for c in requisitos.ids_criterios if c not in cubiertos])

    def dueno_de(self, archivo: str) -> str | None:
        return next((t.id for t in self.tareas if archivo in t.archivos), None)

    def a_markdown(self, olas: list[list[str]] | None = None) -> str:
        l = ["# Plan de tareas", ""]
        if olas:
            l += ["## Orden de ejecución", ""]
            l += [f"- **Ola {i}** (en paralelo): {', '.join(ola)}" for i, ola in enumerate(olas, 1)] + [""]
        for t in self.tareas:
            l += [f"## {t.id} — {t.titulo}", "", t.objetivo, "",
                  f"- **Cubre:** {', '.join(t.historias + t.criterios) or '—'}",
                  f"- **Archivos (dueña):** {', '.join(f'`{a}`' for a in t.archivos)}",
                  f"- **Lee:** {', '.join(f'`{a}`' for a in t.lee) or '—'}",
                  f"- **Depende de:** {', '.join(t.depende_de) or '—'}",
                  "- **Lista cuando:**"] + [f"  - {x}" for x in t.listo_cuando] + [""]
        if self.criterios_sin_cubrir:
            l += ["## ⚠️ Criterios sin tarea", "", ", ".join(self.criterios_sin_cubrir), ""]
        return "\n".join(l)


def _sin_duplicados(ids: list[str]) -> None:
    vistos, repetidos = set(), set()
    for i in ids:
        (repetidos if i in vistos else vistos).add(i)
    if repetidos:
        raise ValueError(f"IDs repetidos: {sorted(repetidos)}")


def _sin_ciclos(tareas: list[Tarea]) -> None:
    deps = {t.id: set(t.depende_de) for t in tareas}
    visitando, hecho = set(), set()

    def visitar(n: str, camino: list[str]) -> None:
        if n in hecho:
            return
        if n in visitando:
            raise ValueError(f"dependencias circulares: {' → '.join(camino + [n])}")
        visitando.add(n)
        for m in deps[n]:
            visitar(m, camino + [n])
        visitando.discard(n)
        hecho.add(n)

    for t in tareas:
        visitar(t.id, [])


def a_dict(obj) -> dict:
    return asdict(obj)
