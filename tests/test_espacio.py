import pytest

from specforge.espacio import Edicion, Espacio, extraer_archivos, extraer_ediciones


def test_extraer_archivos():
    texto = "Aquí va:\n=== FILE: app/a.py ===\nx = 1\n=== END FILE ===\n=== FILE: app\\b.py ===\ny = 2\n=== END FILE ===\n"
    assert extraer_archivos(texto) == {"app/a.py": "x = 1\n", "app/b.py": "y = 2\n"}


def test_extraer_archivos_rechaza_rutas_peligrosas():
    with pytest.raises(ValueError):
        extraer_archivos("=== FILE: ../../etc/x ===\nmal\n=== END FILE ===\n")


def test_extraer_ediciones():
    texto = ("Causa: suma mal.\n=== EDIT: app/a.py ===\n<<<<<<< SEARCH\nreturn a - b\n=======\n"
             "return a + b\n>>>>>>> REPLACE\n")
    assert extraer_ediciones(texto) == [Edicion("app/a.py", "return a - b\n", "return a + b\n")]


def test_aplicar_exige_coincidencia_unica(tmp_path):
    e = Espacio(tmp_path)
    e.escribir("a.py", "x = 1\nx = 1\ny = 2\n")
    e.aplicar(Edicion("a.py", "y = 2\n", "y = 3\n"))
    assert e.leer("a.py").endswith("y = 3\n")
    with pytest.raises(ValueError, match="2 veces"):
        e.aplicar(Edicion("a.py", "x = 1\n", "x = 9\n"))
    with pytest.raises(ValueError, match="0 veces"):
        e.aplicar(Edicion("a.py", "no existe", ""))
    with pytest.raises(ValueError, match="no existe"):
        e.aplicar(Edicion("otro.py", "a", "b"))


def test_listar_ignora_dependencias_y_specs(tmp_path):
    e = Espacio(tmp_path)
    for r in ["src/a.py", "node_modules/x/i.js", ".git/HEAD", "README.md"]:
        (tmp_path / r).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / r).write_text("x")
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "r.md").write_text("x")
    assert e.listar() == ["README.md", "src/a.py"]


def test_leer_recorta_archivos_grandes(tmp_path):
    e = Espacio(tmp_path)
    e.escribir("g.txt", "a" * 100)
    assert "recortado: 90" in e.leer("g.txt", max_chars=10)


def test_escribir_borra_bytecode_viejo(tmp_path):
    # Regresión: con el mismo tamaño y segundo, Python reusaba el .pyc viejo y un arreglo correcto "fallaba"
    e = Espacio(tmp_path)
    e.escribir("calc.py", "x = 1\n")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "calc.cpython-312.pyc").write_bytes(b"viejo")
    (cache / "otro.cpython-312.pyc").write_bytes(b"ajeno")
    e.escribir("calc.py", "x = 2\n")
    assert not (cache / "calc.cpython-312.pyc").exists()
    assert (cache / "otro.cpython-312.pyc").exists()
