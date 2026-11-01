from specforge.artefactos import Tarea
from specforge.planificador import olas


def t(id, archivos, depende_de=(), lee=()):
    return Tarea(id, id, "obj", [], [], list(archivos), list(lee), list(depende_de), [])


def ids(resultado):
    return [[x.id for x in ola] for ola in resultado]


def test_independientes_van_juntas():
    assert ids(olas([t("A", ["a"]), t("B", ["b"]), t("C", ["c"])])) == [["A", "B", "C"]]


def test_dependencias_crean_olas():
    tareas = [t("BASE", ["m"]), t("X", ["x"], ["BASE"]), t("Y", ["y"], ["BASE"]), t("FIN", ["f"], ["X", "Y"])]
    assert ids(olas(tareas)) == [["BASE"], ["X", "Y"], ["FIN"]]


def test_no_lee_lo_que_otra_escribe_al_mismo_tiempo():
    # B lee el archivo de A sin declararlo como dependencia: no deben correr juntas
    assert ids(olas([t("A", ["a"]), t("B", ["b"], lee=["a"])])) == [["A"], ["B"]]
