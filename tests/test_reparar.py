"""Modo REPARAR sobre un repositorio git real con pruebas reales."""

import asyncio
import json
import subprocess
import sys

import pytest

from specforge.reparar import ErrorReparacion, Reparador

PRUEBA = f"{sys.executable} -m pytest -q -p no:cacheprovider"

CALC_MALO = "def sumar(a, b):\n    return a - b\n"
TEST = "from calc import sumar\n\n\ndef test_sumar():\n    assert sumar(2, 3) == 5\n"


def git(raiz, *args):
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "calc.py").write_text(CALC_MALO)
    (tmp_path / "test_calc.py").write_text(TEST)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "inicio")
    return tmp_path


def guion(parches):
    parches = iter(parches)

    async def responder(etapa, user):
        if etapa == "localizar":
            assert "assert -1 == 5" in user or "AssertionError" in user
            return json.dumps({"archivos": ["calc.py", "no_existe.py"], "hipotesis": "resta en vez de sumar"})
        if etapa == "parche":
            return next(parches)
        raise AssertionError(etapa)
    return responder


ARREGLO = ("La función resta.\n=== EDIT: calc.py ===\n<<<<<<< SEARCH\n    return a - b\n=======\n"
           "    return a + b\n>>>>>>> REPLACE\n")
MAL_PARCHE = ("Cambio equivocado.\n=== EDIT: calc.py ===\n<<<<<<< SEARCH\n    return a - b\n=======\n"
              "    return a * b\n>>>>>>> REPLACE\n")


def test_arregla_en_una_rama_aparte(repo, ia_guionada):
    ia_guionada.responder = guion([ARREGLO])
    r = asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())

    assert r.estado == "arreglado" and len(r.intentos) == 1
    assert r.intentos[0].sospechosos[0] == "calc.py"           # elegido por el modelo, solo rutas reales
    assert "no_existe.py" not in r.intentos[0].sospechosos
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == r.rama
    assert "return a + b" in (repo / "calc.py").read_text()
    assert git(repo, "show", "main:calc.py") + "\n" == CALC_MALO  # main no se tocó
    assert "SpecForge: arreglo validado" in git(repo, "log", "-1", "--format=%s")
    assert git(repo, "status", "--porcelain", "--untracked-files=no") == ""


def test_si_no_lo_logra_deja_todo_como_estaba(repo, ia_guionada):
    ia_guionada.responder = guion([MAL_PARCHE, "sin ediciones"])
    r = asyncio.run(Reparador(repo, PRUEBA, max_intentos=2, avisar=lambda m: None).ejecutar())

    assert r.estado == "sin_arreglo" and len(r.intentos) == 2
    assert r.intentos[1].errores_edicion  # el segundo intento no trajo ediciones válidas
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert (repo / "calc.py").read_text() == CALC_MALO
    assert r.rama not in git(repo, "branch", "--list")


def test_el_segundo_intento_conoce_el_anterior(repo, ia_guionada):
    # el primer parche cambia la línea; el segundo parte del texto nuevo
    segundo = ARREGLO.replace("return a - b", "return a * b")
    ia_guionada.responder = guion([MAL_PARCHE, segundo])
    r = asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())
    assert r.estado == "arreglado" and len(r.intentos) == 2
    ultimo_parche = [u for e, u in ia_guionada.llamadas if e == "parche"][-1]
    assert "Intento 1: editó ['calc.py']" in ultimo_parche


def test_ya_pasaba(repo, ia_guionada):
    (repo / "calc.py").write_text("def sumar(a, b):\n    return a + b\n")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "ok")
    r = asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())
    assert r.estado == "ya_pasaba" and ia_guionada.llamadas == []


def test_exige_git_y_cambios_guardados(repo, tmp_path_factory, ia_guionada):
    sin_git = tmp_path_factory.mktemp("sin_git")
    with pytest.raises(ErrorReparacion, match="no es un repositorio git"):
        asyncio.run(Reparador(sin_git, PRUEBA, avisar=lambda m: None).ejecutar())
    (repo / "calc.py").write_text("# cambio sin guardar\n")
    with pytest.raises(ErrorReparacion, match="cambios sin guardar"):
        asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())


def test_recuerda_arreglos_anteriores(repo, ia_guionada):
    from specforge.reparar import firma_error

    ia_guionada.responder = guion([ARREGLO])
    asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())

    # El mismo error vuelve a aparecer en main: la localización recibe el arreglo anterior
    git(repo, "switch", "-q", "main")
    ia_guionada.llamadas.clear()
    ia_guionada.responder = guion([ARREGLO])
    asyncio.run(Reparador(repo, PRUEBA, avisar=lambda m: None).ejecutar())
    localizar = next(u for e, u in ia_guionada.llamadas if e == "localizar")
    assert "# Arreglos anteriores parecidos" in localizar and "calc.py" in localizar
    assert "assert" in firma_error("E   assert -1 == 5\nFAILED test_calc.py::test_sumar")
