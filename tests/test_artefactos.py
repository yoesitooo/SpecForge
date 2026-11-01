import copy

import pytest

from specforge.artefactos import Diseno, Plan, Requisitos, ruta_segura

REQ = {
    "resumen": "Agenda de citas para un consultorio.",
    "historias": [
        {"id": "HU-1", "como": "paciente", "quiero": "pedir una cita", "para": "ser atendido",
         "prioridad": "alta", "criterios": [
             {"id": "CA-1.1", "texto": "CUANDO el paciente envía fecha y hora libres EL SISTEMA DEBE crear la cita"},
             {"id": "CA-1.2", "texto": "SI la hora está ocupada EL SISTEMA DEBE rechazarla con un error"}]},
        {"id": "HU-2", "como": "doctora", "quiero": "ver las citas del día", "para": "organizarme",
         "criterios": [{"id": "CA-2.1", "texto": "CUANDO la doctora consulta un día EL SISTEMA DEBE listar sus citas"}]},
    ],
    "casos_uso": [
        {"id": "CU-1", "nombre": "Pedir cita", "actor": "paciente", "historias": ["HU-1"],
         "precondiciones": ["hay horarios"], "flujo_principal": ["elige hora", "confirma"],
         "flujos_alternos": [{"condicion": "si la hora está ocupada", "pasos": ["ve el error"]}],
         "postcondiciones": ["cita creada"]}],
    "no_funcionales": ["respuesta < 1 s"],
}

PLAN = {"tareas": [
    {"id": "T-1", "titulo": "Modelo", "objetivo": "Modelo de cita compartido", "historias": [], "criterios": [],
     "archivos": ["app/modelo.py"], "lee": [], "depende_de": [], "listo_cuando": ["importa sin errores"]},
    {"id": "T-2", "titulo": "Pedir cita", "objetivo": "Crear citas", "historias": ["HU-1"],
     "criterios": ["CA-1.1", "CA-1.2"], "archivos": ["app/citas.py", "tests/test_citas.py"],
     "lee": ["app/modelo.py"], "depende_de": ["T-1"], "listo_cuando": ["pytest pasa"]},
    {"id": "T-3", "titulo": "Agenda", "objetivo": "Listar citas", "historias": ["HU-2"], "criterios": ["CA-2.1"],
     "archivos": ["app/agenda.py"], "lee": [], "depende_de": ["T-1"], "listo_cuando": ["pytest pasa"]},
]}


def test_requisitos_validos_y_markdown():
    req = Requisitos.desde_dict(REQ)
    assert req.ids_criterios == ["CA-1.1", "CA-1.2", "CA-2.1"]
    md = req.a_markdown()
    assert "**Como** paciente, **quiero** pedir una cita" in md
    assert "**Alterno — si la hora está ocupada**" in md and "CU-1 — Pedir cita" in md


@pytest.mark.parametrize("romper,mensaje", [
    (lambda d: d["historias"][0].update(criterios=[]), "no tiene criterios"),
    (lambda d: d["casos_uso"][0].update(historias=["HU-9"]), "historias que no existen"),
    (lambda d: d["historias"][1].update(id="HU-1"), "IDs repetidos"),
    (lambda d: d.update(historias=[]), "no hay historias"),
])
def test_requisitos_invalidos(romper, mensaje):
    d = copy.deepcopy(REQ)
    romper(d)
    with pytest.raises(ValueError, match=mensaje):
        Requisitos.desde_dict(d)


def test_plan_valido_y_cobertura():
    plan = Plan.desde_dict(PLAN, Requisitos.desde_dict(REQ))
    assert [t.id for t in plan.tareas] == ["T-1", "T-2", "T-3"]
    assert plan.criterios_sin_cubrir == []
    assert plan.dueno_de("app/agenda.py") == "T-3"


def test_plan_reporta_criterios_sin_cubrir():
    d = copy.deepcopy(PLAN)
    d["tareas"][2]["criterios"] = []
    assert Plan.desde_dict(d, Requisitos.desde_dict(REQ)).criterios_sin_cubrir == ["CA-2.1"]


@pytest.mark.parametrize("romper,mensaje", [
    (lambda d: d["tareas"][2].update(archivos=["app/citas.py"]), "un solo dueño"),
    (lambda d: d["tareas"][1].update(depende_de=["T-9"]), "no existen"),
    (lambda d: d["tareas"][0].update(depende_de=["T-2"]), "circulares"),
    (lambda d: d["tareas"][1].update(criterios=["CA-7.7"]), "criterios que no existen"),
    (lambda d: d["tareas"][0].update(archivos=["../fuera.py"]), "no permitida"),
    (lambda d: d["tareas"][0].update(archivos=[]), "no declara archivos"),
])
def test_plan_invalido(romper, mensaje):
    d = copy.deepcopy(PLAN)
    romper(d)
    with pytest.raises(ValueError, match=mensaje):
        Plan.desde_dict(d, Requisitos.desde_dict(REQ))


@pytest.mark.parametrize("ruta", ["/etc/passwd", "../x", "a/../../x", ".git/config", "specs/requisitos.md", ""])
def test_rutas_peligrosas(ruta):
    with pytest.raises(ValueError):
        ruta_segura(ruta)


def test_ruta_normaliza_barras_de_windows():
    assert ruta_segura("app\\citas.py") == "app/citas.py"


def test_diseno_contratos_para_los_agentes():
    dis = Diseno.desde_dict({
        "resumen": "API REST", "stack": {"lenguaje": "Python"}, "componentes": [],
        "modelo_datos": [{"entidad": "Cita", "campos": ["fecha: date"]}],
        "contratos": [{"nombre": "crear_cita", "tipo": "funcion", "firma": "crear_cita(fecha, hora) -> Cita"}],
        "estructura": ["app/citas.py"], "comandos": {"probar": "pytest -q"},
    })
    md = dis.contratos_markdown()
    assert "`crear_cita(fecha, hora) -> Cita`" in md and "**Cita**: fecha: date" in md
