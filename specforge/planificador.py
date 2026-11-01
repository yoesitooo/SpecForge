"""
Planificador — qué tareas pueden trabajar al mismo tiempo
=========================================================
Agrupa las tareas en "olas": todas las de una ola corren en paralelo y la
siguiente ola espera a que termine la anterior. Una tarea entra en una ola
cuando sus dependencias ya terminaron.

Para que dos agentes en paralelo no se pisen:
  - cada archivo tiene una sola tarea dueña (lo valida artefactos.Plan), y
  - una tarea no corre a la vez que otra que escribe un archivo que ella LEE
    (se mueve a la ola siguiente).
"""

from __future__ import annotations

from .artefactos import Tarea


def olas(tareas: list[Tarea]) -> list[list[Tarea]]:
    pendientes = {t.id: t for t in tareas}
    hechas: set[str] = set()
    resultado: list[list[Tarea]] = []

    while pendientes:
        listas = [t for t in pendientes.values() if set(t.depende_de) <= hechas]
        if not listas:  # no debería pasar: Plan valida que no haya ciclos
            raise ValueError(f"no se pueden ordenar: {sorted(pendientes)}")

        ola: list[Tarea] = []
        escritos: set[str] = set()
        for t in sorted(listas, key=lambda x: _orden_original(tareas, x)):
            if set(t.lee) & escritos or set(t.archivos) & {l for o in ola for l in o.lee}:
                continue  # conflicto de lectura/escritura: a la próxima ola
            ola.append(t)
            escritos |= set(t.archivos)

        resultado.append(ola)
        for t in ola:
            hechas.add(t.id)
            del pendientes[t.id]
    return resultado


def _orden_original(tareas: list[Tarea], t: Tarea) -> int:
    return next(i for i, x in enumerate(tareas) if x.id == t.id)
