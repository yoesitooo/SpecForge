"""El DAG es datos puros: estas pruebas no llaman a ningún modelo."""

import pytest

dag = pytest.importorskip("orchestrator.dag")
from core.config import AGENT_MODELS  # noqa: E402


def test_once_fases_y_cada_una_con_agente():
    assert len(dag.PHASE_ORDER) == 11
    assert set(dag.PHASE_ORDER) == set(dag.AGENT_MAP) == set(dag.PHASE_LABELS)


def test_cada_fase_tiene_nivel_de_modelo():
    assert set(dag.PHASE_ORDER) == set(AGENT_MODELS)


def test_grupos_paralelos_son_contiguos_en_el_orden():
    for grupo in dag.PARALLEL_GROUPS:
        indices = [dag.PHASE_ORDER.index(f) for f in grupo]
        assert indices == list(range(indices[0], indices[0] + len(grupo))), grupo


def test_grupo_paralelo_y_siguiente_fase():
    assert dag.get_parallel_group("backend") == ["frontend", "backend", "db"]
    assert dag.get_parallel_group("discovery") is None
    assert dag.next_phase("code_review") is None
    assert dag.next_phase("discovery") == "requirements"


def test_cada_agente_declara_su_fase():
    for fase, agente in dag.AGENT_MAP.items():
        assert agente.phase == fase
