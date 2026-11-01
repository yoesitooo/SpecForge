import pytest

from specforge.__main__ import main, menu


def respuestas(*valores):
    it = iter(valores)
    return lambda _prompt: next(it)


def test_menu_generar_con_reparacion():
    assert menu(respuestas("1", "agenda de citas", "s")) == ["generar", "agenda de citas", "--reparar"]


def test_menu_telegram():
    assert menu(respuestas("4")) == ["telegram"]


def test_menu_reparar():
    assert menu(respuestas("2", "", "pytest -q")) == ["reparar", ".", "--prueba", "pytest -q"]


@pytest.mark.parametrize("valores", [("0",), ("1", ""), ("2", ".", ""), ("9",)])
def test_menu_salir_o_datos_vacios(valores):
    assert menu(respuestas(*valores)) == []


def test_reparar_desde_cli_explica_si_no_es_git(tmp_path, capsys):
    assert main(["reparar", str(tmp_path), "--prueba", "pytest -q"]) == 2
    assert "no es un repositorio git" in capsys.readouterr().out
