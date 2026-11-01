"""Proceso completo de GENERAR con una IA simulada y pruebas reales (pytest)."""

import asyncio
import json
import sys

from tests.test_artefactos import REQ

PY = f'"{sys.executable}"' if " " in sys.executable else sys.executable

DISENO = {
    "resumen": "Módulo Python con funciones puras.", "stack": {"lenguaje": "Python"},
    "componentes": [{"nombre": "citas", "responsabilidad": "crear y listar citas"}],
    "modelo_datos": [{"entidad": "Cita", "campos": ["dia: str", "hora: str"]}],
    "contratos": [{"nombre": "crear_cita", "tipo": "funcion", "firma": "crear_cita(agenda, dia, hora) -> dict | ValueError"},
                  {"nombre": "citas_del_dia", "tipo": "funcion", "firma": "citas_del_dia(agenda, dia) -> list"}],
    "estructura": ["app/__init__.py", "app/modelo.py", "app/citas.py", "app/agenda.py", "tests/test_app.py"],
    "comandos": {"probar": f"{PY} -m pytest -q -p no:cacheprovider"},
}

PLAN = {"tareas": [
    {"id": "T-1", "titulo": "Base", "objetivo": "Modelo compartido", "historias": [], "criterios": [],
     "archivos": ["app/__init__.py", "app/modelo.py"], "lee": [], "depende_de": [], "listo_cuando": ["importa"]},
    {"id": "T-2", "titulo": "Pedir cita", "objetivo": "Crear citas sin choques", "historias": ["HU-1"],
     "criterios": ["CA-1.1", "CA-1.2"], "archivos": ["app/citas.py"], "lee": ["app/modelo.py"],
     "depende_de": ["T-1"], "listo_cuando": ["pruebas pasan"]},
    {"id": "T-3", "titulo": "Agenda del día", "objetivo": "Listar citas", "historias": ["HU-2"],
     "criterios": ["CA-2.1"], "archivos": ["app/agenda.py"], "lee": [], "depende_de": ["T-1"],
     "listo_cuando": ["pruebas pasan"]},
    {"id": "T-4", "titulo": "Pruebas", "objetivo": "Probar los criterios", "historias": ["HU-1", "HU-2"],
     "criterios": [], "archivos": ["tests/test_app.py"], "lee": ["app/citas.py", "app/agenda.py"],
     "depende_de": ["T-2", "T-3"], "listo_cuando": ["pytest pasa"]},
]}

CODIGO = {
    "T-1": {"app/__init__.py": "", "app/modelo.py": "def nueva(dia, hora):\n    return {'dia': dia, 'hora': hora}\n"},
    "T-2": {"app/citas.py": (
        "from app.modelo import nueva\n\n\ndef crear_cita(agenda, dia, hora):\n"
        "    if any(c['dia'] == dia and c['hora'] == hora for c in agenda):\n"
        "        raise ValueError('hora ocupada')\n    c = nueva(dia, hora)\n    agenda.append(c)\n    return c\n"),
        # intenta además escribir un archivo de otra tarea: debe rechazarse
        "app/agenda.py": "ROTO = True\n"},
    "T-3": {"app/agenda.py": "def citas_del_dia(agenda, dia):\n    return [c for c in agenda if c['dia'] == dia]\n"},
    "T-4": {"tests/test_app.py": (
        "import pytest\nfrom app.citas import crear_cita\nfrom app.agenda import citas_del_dia\n\n\n"
        "def test_crea_y_lista():\n    a = []\n    crear_cita(a, 'lun', '9')\n    assert citas_del_dia(a, 'lun') == [{'dia': 'lun', 'hora': '9'}]\n\n\n"
        "def test_rechaza_choque():\n    a = []\n    crear_cita(a, 'lun', '9')\n    with pytest.raises(ValueError):\n        crear_cita(a, 'lun', '9')\n")},
}


def _bloques(archivos):
    return "".join(f"=== FILE: {r} ===\n{c}=== END FILE ===\n" for r, c in archivos.items())


def _responder(concurrencia):
    async def responder(etapa, user):
        if etapa == "descubrimiento":
            return json.dumps({"preguntas": ["¿Quién usa la app?"]})
        if etapa == "requisitos":
            return json.dumps(REQ)
        if etapa == "diseno":
            return "Propuesta:\n```json\n" + json.dumps(DISENO) + "\n```"
        if etapa == "tareas":
            return json.dumps(PLAN)
        if etapa == "implementacion":
            tarea = user.split("# TU TAREA: ")[1].split(" ")[0]
            concurrencia["ahora"] += 1
            concurrencia["max"] = max(concurrencia["max"], concurrencia["ahora"])
            await asyncio.sleep(0.05)
            concurrencia["ahora"] -= 1
            return _bloques(CODIGO[tarea])
        if etapa == "revision":
            return json.dumps({"veredicto": "aprobado", "hallazgos": [], "criterios_dudosos": []})
        raise AssertionError(etapa)
    return responder


def test_generar_de_punta_a_punta(ia_guionada, tmp_path):
    from specforge.generar import Generador

    concurrencia = {"ahora": 0, "max": 0}
    ia_guionada.responder = _responder(concurrencia)
    respuestas = []

    async def usuario(preguntas):
        respuestas.extend(preguntas)
        return ["la doctora y sus pacientes"]

    g = Generador("Agenda de citas", nombre="citas", carpeta=tmp_path, preguntar_usuario=usuario, avisar=lambda m: None)
    inf = asyncio.run(g.ejecutar(verificar=True))
    raiz = tmp_path / "citas"

    # Descubrimiento: la respuesta del usuario llega a los requisitos
    assert respuestas == ["¿Quién usa la app?"]
    req_user = next(u for e, u in ia_guionada.llamadas if e == "requisitos")
    assert "la doctora y sus pacientes" in req_user

    # Documentos guardados para personas y para máquinas
    for nombre in ("requisitos", "diseno", "tareas"):
        assert (raiz / "specs" / f"{nombre}.md").exists() and (raiz / "specs" / f"{nombre}.json").exists()

    # Olas: T-2 y T-3 en paralelo, T-4 al final
    assert inf.olas == [["T-1"], ["T-2", "T-3"], ["T-4"]]
    assert concurrencia["max"] == 2

    # Cada tarea solo escribe sus archivos: el intento de T-2 sobre agenda.py se rechaza
    assert inf.tareas["T-2"].rechazados == ["app/agenda.py"]
    assert "citas_del_dia" in (raiz / "app" / "agenda.py").read_text()

    # Contexto mínimo: T-3 no recibe criterios de HU-1 ni el código de citas.py
    t3 = next(u for e, u in ia_guionada.llamadas if e == "implementacion" and "TU TAREA: T-3" in u)
    assert "CA-2.1" in t3 and "CA-1.1" not in t3 and "crear_cita(agenda" not in t3.split("# Contratos")[0]
    # ...y T-4 sí recibe el código que declara leer
    t4 = next(u for e, u in ia_guionada.llamadas if e == "implementacion" and "TU TAREA: T-4" in u)
    assert "--- app/citas.py ---" in t4

    # Verificación real: las pruebas generadas pasan
    assert inf.verificacion["ok"], inf.verificacion["salida"]

    informe = (raiz / "specs" / "informe.md").read_text()
    assert "| CA-1.2 | T-2 | app/citas.py | ✅ |" in informe
    assert "intentó escribir archivos ajenos: app/agenda.py" in informe
    assert "Veredicto: **aprobado**" in informe


def test_pide_corregir_plan_con_criterios_sin_cubrir(ia_guionada, tmp_path):
    from specforge.generar import Generador

    incompleto = json.loads(json.dumps(PLAN))
    incompleto["tareas"][2]["criterios"] = []
    planes = iter([incompleto, PLAN])
    base = _responder({"ahora": 0, "max": 0})

    async def responder(etapa, user):
        return json.dumps(next(planes)) if etapa == "tareas" else await base(etapa, user)

    ia_guionada.responder = responder
    g = Generador("x", nombre="p", carpeta=tmp_path, avisar=lambda m: None)
    inf = asyncio.run(g.ejecutar())
    pedidos = [u for e, u in ia_guionada.llamadas if e == "tareas"]
    assert len(pedidos) == 2 and "['CA-2.1']" in pedidos[1]
    assert inf.plan.criterios_sin_cubrir == []


def test_tarea_que_falla_no_detiene_las_demas(ia_guionada, tmp_path):
    from specforge.generar import Generador

    base = _responder({"ahora": 0, "max": 0})

    async def responder(etapa, user):
        if etapa == "implementacion" and "TU TAREA: T-3" in user:
            raise ConnectionError("se cayó")
        return await base(etapa, user)

    ia_guionada.responder = responder
    g = Generador("x", nombre="p", carpeta=tmp_path, avisar=lambda m: None)
    inf = asyncio.run(g.ejecutar())
    assert "se cayó" in inf.tareas["T-3"].error
    assert inf.tareas["T-4"].ok
