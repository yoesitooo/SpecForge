import pytest

main = pytest.importorskip("main")


@pytest.mark.parametrize("valor,esperado", [
    ("cli", {"cli"}),
    ("http", {"http"}),
    (" Voice , telegram ", {"voice", "telegram"}),
])
def test_transportes_validos(valor, esperado):
    assert main.parse_transportes(valor) == esperado


@pytest.mark.parametrize("valor", ["", "web", "cli,fax"])
def test_transportes_invalidos_terminan_el_programa(valor):
    with pytest.raises(SystemExit):
        main.parse_transportes(valor)
