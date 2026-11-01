"""
SpecForge — línea de comandos
=============================
  python -m specforge generar "app de citas para un consultorio" [--nombre citas] [--sin-preguntas] [--verificar] [--reparar]
  python -m specforge reparar RUTA --prueba "pytest -q" [--intentos 3]
  python -m specforge diagnostico
"""

from __future__ import annotations

import argparse
import asyncio
import sys


async def _preguntar_en_terminal(preguntas: list[str]) -> list[str]:
    print("\nAntes de empezar, unas preguntas (Enter para saltar):")
    respuestas = []
    for p in preguntas:
        respuestas.append(input(f"  • {p}\n    → ").strip())
    return respuestas


def _generar(a: argparse.Namespace) -> int:
    from .generar import Generador

    g = Generador(
        a.idea,
        nombre=a.nombre,
        carpeta=a.carpeta,
        preguntar_usuario=None if a.sin_preguntas else _preguntar_en_terminal,
        paralelo=a.paralelo or 3,
    )
    inf = asyncio.run(g.ejecutar(verificar=a.verificar or a.reparar, reparar=a.reparar))
    malas = [t for t, r in inf.tareas.items() if not r.ok]
    print(f"\n📁 Proyecto: {inf.proyecto}")
    print(f"📄 Especificaciones e informe: {inf.proyecto / 'specs'}")
    if malas:
        print(f"⚠️  Tareas con problemas: {', '.join(malas)} (ver specs/informe.md)")
    if inf.verificacion:
        print("🧪 Pruebas:", "pasan ✅" if inf.verificacion["ok"] else "fallan ❌")
    return 0 if not malas else 1


def _reparar(a: argparse.Namespace) -> int:
    from .reparar import ErrorReparacion, Reparador

    try:
        r = asyncio.run(Reparador(a.ruta, a.prueba, max_intentos=a.intentos).ejecutar())
    except ErrorReparacion as e:
        print(f"❌ {e}")
        return 2
    print("\n" + r.resumen())
    return 0 if r.estado in ("arreglado", "ya_pasaba") else 1


def _diagnostico(_: argparse.Namespace) -> int:
    from providers.diagnostico import main

    return asyncio.run(main())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="specforge", description="De la idea al código con especificaciones primero, y reparación validada con pruebas.")
    sub = p.add_subparsers(dest="comando", required=True)

    g = sub.add_parser("generar", help="crear un proyecto desde una idea")
    g.add_argument("idea")
    g.add_argument("--nombre", help="nombre de la carpeta del proyecto")
    g.add_argument("--carpeta", help="dónde crear el proyecto (por defecto ./workspaces)")
    g.add_argument("--sin-preguntas", action="store_true", help="no hacer preguntas de descubrimiento")
    g.add_argument("--verificar", action="store_true", help="instalar y correr las pruebas al terminar")
    g.add_argument("--reparar", action="store_true", help="si las pruebas fallan, intentar arreglarlas (implica --verificar)")
    g.add_argument("--paralelo", type=int, help="agentes a la vez (por defecto 3)")
    g.set_defaults(func=_generar)

    r = sub.add_parser("reparar", help="arreglar un proyecto cuyas pruebas fallan")
    r.add_argument("ruta", help="carpeta del repositorio (git)")
    r.add_argument("--prueba", required=True, help='comando de pruebas, p. ej. "pytest -q" o "npm test"')
    r.add_argument("--intentos", type=int, default=3)
    r.set_defaults(func=_reparar)

    d = sub.add_parser("diagnostico", help="probar qué proveedores de IA responden")
    d.set_defaults(func=_diagnostico)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
