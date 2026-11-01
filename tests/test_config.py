from core import config
from providers import router


def test_parse_chain():
    assert config.parse_chain(" gemini:gemini-3.8-flash , antigravity:,groq:openai/gpt-oss-20b ") == [
        ("gemini", "gemini-3.8-flash"),
        ("antigravity", ""),
        ("groq", "openai/gpt-oss-20b"),
    ]


def test_cada_agente_tiene_cadena_valida():
    for fase, cfg in config.AGENT_MODELS.items():
        cadena = config.chain_for(cfg["tier"])
        assert cadena, fase
        for proveedor, _ in cadena:
            assert proveedor in router.PROVEEDORES, (fase, proveedor)


def test_cadena_se_puede_reemplazar_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("SDD_CHAIN_FAST", "cerebras:gpt-oss-120b")
    assert config.chain_for("fast") == [("cerebras", "gpt-oss-120b")]


def test_hay_respaldo_gratis_en_cada_nivel():
    gratis = {"gemini", "groq", "cerebras", "openrouter", "github", "nvidia"}
    for nivel in config.DEFAULT_CHAINS:
        assert any(p in gratis for p, _ in config.chain_for(nivel)), nivel


def test_modo_auto_pone_las_cuentas_primero():
    proveedores = [p for p, _ in config.chain_for("smart")]
    assert proveedores[:2] == ["claude", "antigravity"]
    assert "gemini" in proveedores


def test_modo_gratis_ignora_las_cuentas(monkeypatch):
    monkeypatch.setenv("SPECFORGE_MODO", "gratis")
    for nivel in config.DEFAULT_CHAINS:
        assert not {p for p, _ in config.chain_for(nivel)} & config.PROVEEDORES_CUENTA


def test_modo_cuentas_solo_usa_cuentas(monkeypatch):
    monkeypatch.setenv("SPECFORGE_MODO", "cuentas")
    for nivel in config.DEFAULT_CHAINS:
        cadena = config.chain_for(nivel)
        assert cadena and {p for p, _ in cadena} <= config.PROVEEDORES_CUENTA, nivel


def test_modo_invalido(monkeypatch):
    import pytest
    monkeypatch.setenv("SPECFORGE_MODO", "pagado")
    with pytest.raises(EnvironmentError):
        config.chain_for("smart")
