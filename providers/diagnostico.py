"""
Diagnóstico real de proveedores — ¿cuáles responden con TU configuración?
=========================================================================
Uso:
    python -m providers.diagnostico

Para cada proveedor configurado (clave en .env o CLI con sesión iniciada)
hace UNA llamada mínima y muestra si respondió, con qué modelo y en cuánto
tiempo. Así compruebas que funcionan tanto las APIs gratis como tus cuentas
(Claude Pro con `claude`, Google AI Pro con `agy`).

Gasta una consulta por proveedor; no se ejecuta en las pruebas automáticas.
"""

from __future__ import annotations

import asyncio
import sys
import time

from core.config import DEFAULT_CHAINS, PROVEEDORES_CUENTA, modo, parse_chain
from providers.router import PROVEEDORES, _get_provider

PROMPT = "Responde solo con la palabra: listo"


def _modelo_de_prueba(proveedor: str) -> str:
    """Primer modelo que las cadenas por defecto usan para ese proveedor."""
    for spec in DEFAULT_CHAINS.values():
        for p, m in parse_chain(spec):
            if p == proveedor:
                return m
    return ""


async def probar(proveedor: str) -> tuple[str, str]:
    p = _get_provider(proveedor)
    tipo = "cuenta" if proveedor in PROVEEDORES_CUENTA else "API"
    if not p.is_available():
        motivo = "CLI no instalado" if tipo == "cuenta" else "sin clave en .env"
        return "—", f"{proveedor} ({tipo}): {motivo}"
    modelo = _modelo_de_prueba(proveedor)
    inicio = time.monotonic()
    try:
        r = await p.complete(system="", user=PROMPT, model=modelo, temperature=0, max_tokens=20)
    except Exception as e:  # diagnóstico: mostrar cualquier fallo
        return "✗", f"{proveedor} ({tipo}): {str(e).splitlines()[0][:160]}"
    segundos = time.monotonic() - inicio
    return "✓", f"{proveedor} ({tipo}, {modelo or 'modelo por defecto'}): «{r.content.strip()[:30]}» en {segundos:.1f} s"


async def main() -> int:
    print(f"Modo actual: SPECFORGE_MODO={modo()}\n")
    resultados = await asyncio.gather(*(probar(p) for p in PROVEEDORES))
    for icono, texto in resultados:
        print(f"  {icono} {texto}")
    ok = sum(1 for icono, _ in resultados if icono == "✓")
    print(f"\n{ok} proveedor(es) respondieron.")
    if ok == 0:
        print("Agrega una clave gratis (GEMINI_API_KEY) o inicia sesión con `agy` o `claude`.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
