import asyncio
import sys

from specforge.pruebas import archivos_en_traza, correr


def test_archivos_en_traza_python_y_node(tmp_path):
    for r in ["app/citas.py", "src/api.ts"]:
        (tmp_path / r).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / r).write_text("x")
    salida = (
        f'  File "{tmp_path}/app/citas.py", line 4, in crear\n'
        '  File "/usr/lib/python3/site-packages/lib.py", line 1\n'
        "    at handler (src/api.ts:12:5)\n"
        "    at x (node_modules/pkg/index.js:1:1)\n"
    )
    assert set(archivos_en_traza(salida, tmp_path)) == {"app/citas.py", "src/api.ts"}


def test_correr_encadena_y_se_detiene_en_el_primer_fallo(tmp_path):
    py = sys.executable
    r = asyncio.run(correr(f'{py} -c "print(1)" && {py} -c "import sys; sys.exit(3)" && {py} -c "print(99)"', tmp_path))
    assert not r.ok and r.codigo == 3 and "99" not in r.salida


def test_correr_programa_inexistente(tmp_path):
    r = asyncio.run(correr("programa-que-no-existe-xyz", tmp_path))
    assert r.codigo == 127 and not r.ok
