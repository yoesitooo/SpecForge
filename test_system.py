"""
test_system.py — Verifica que todo el stack está listo antes de arrancar.
Ejecutar: python test_system.py
"""

import asyncio
import sys

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    msg = f"{icon} {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append(ok)
    return ok


# ── 1. Packages ───────────────────────────────────────────────────────────────
print("\n=== DEPENDENCIAS ===")

def pkg(name):
    try:
        __import__(name.replace("-","_").split(">=")[0])
        return True
    except ImportError:
        return False

check("python-dotenv",    pkg("dotenv"))
check("httpx",            pkg("httpx"))
check("fastapi",          pkg("fastapi"))
check("uvicorn",          pkg("uvicorn"))
check("websockets",       pkg("websockets"))
check("aiogram",          pkg("aiogram"))
check("groq SDK",         pkg("groq"))
check("sounddevice",      pkg("sounddevice"))
check("numpy",            pkg("numpy"))
check("edge-tts",         pkg("edge_tts"))
check("pygame",           pkg("pygame"))
check("rich",             pkg("rich"))

# ── 2. Config ─────────────────────────────────────────────────────────────────
print("\n=== CONFIG ===")
try:
    from core.config import ENGRAM_DB_PATH, AGENT_MODELS, chain_for
    check("core.config", True)
    check("ENGRAM_DB_PATH", bool(ENGRAM_DB_PATH), ENGRAM_DB_PATH)
    check("Cadenas de proveedores", all(chain_for(c["tier"]) for c in AGENT_MODELS.values()))
except Exception as e:
    check("core.config", False, str(e))

# ── 3. Proveedores (sin llamadas reales) ──────────────────────────────────────
print("\n=== PROVEEDORES (basta con uno) ===")
try:
    from providers.router import PROVEEDORES, _get_provider
    disponibles = [p for p in PROVEEDORES if _get_provider(p).is_available()]
    for p in PROVEEDORES:
        estado = "listo" if p in disponibles else "sin configurar"
        print(f"  {PASS if p in disponibles else WARN} {p}: {estado}")
    check("Al menos un proveedor", bool(disponibles),
          ", ".join(disponibles) or "agrega GEMINI_API_KEY (gratis) a .env")
except Exception as e:
    check("Proveedores", False, str(e))

# ── 4. Memory layer ───────────────────────────────────────────────────────────
print("\n=== MEMORIA ===")
try:
    from memory.engram import init_db, save_signal, retrieve_context
    from memory.session_store import init_sessions, get, reset
    init_db(); init_sessions()
    reset("test_boot", "BootTest")
    save_signal("BootTest", "test", "decision", "Boot check OK")
    ctx = retrieve_context("BootTest", limit=1)
    check("Engram DB", "BootTest" in ctx, "SQLite FTS5 OK")
    state = get("test_boot")
    check("Session Store", state["project"] == "BootTest", "SQLite OK")
except Exception as e:
    check("Memory layer", False, str(e))

# ── 5. DAG ────────────────────────────────────────────────────────────────────
print("\n=== DAG ===")
try:
    from orchestrator.dag import AGENT_MAP, PHASE_ORDER, get_parallel_group, next_phase
    check("11 agentes cargados", len(AGENT_MAP) == 11, f"{len(AGENT_MAP)} agentes")
    check("Grupos paralelos",    get_parallel_group("frontend") == ["frontend","backend","db"])
    check("next_phase lógica",   next_phase("code_review") is None)
except Exception as e:
    check("DAG", False, str(e))

# ── 7. HTTP transport ─────────────────────────────────────────────────────────
print("\n=== HTTP TRANSPORT ===")
try:
    import ast, pathlib
    ast.parse(pathlib.Path("transports/http_transport.py").read_text(encoding="utf-8"))
    from transports.http_transport import app, broadcast_jarvis_state
    check("FastAPI app",        True, "/v1/chat/completions + /jarvis + /ws/jarvis")
    check("WebSocket broadcast", True, "broadcast_jarvis_state importado")
except Exception as e:
    check("HTTP transport", False, str(e))

# ── 8. Voice stack ────────────────────────────────────────────────────────────
print("\n=== VOICE STACK ===")
try:
    import ast, pathlib
    ast.parse(pathlib.Path("tools/voice_listener.py").read_text(encoding="utf-8"))
    ast.parse(pathlib.Path("tools/voice_speaker.py").read_text(encoding="utf-8"))
    ast.parse(pathlib.Path("transports/voice_transport.py").read_text(encoding="utf-8"))
    check("voice_listener.py syntax", True)
    check("voice_speaker.py syntax",  True)
    check("voice_transport.py syntax",True)
except Exception as e:
    check("Voice stack", False, str(e))

# Verificar mic disponible
try:
    import sounddevice as sd
    devs = sd.query_devices()
    inputs = [d for d in devs if d["max_input_channels"] > 0]
    check("Microfono detectado", len(inputs) > 0, f"{len(inputs)} dispositivo(s) de entrada")
except Exception as e:
    check("Microfono", False, str(e) + " — instalar sounddevice")

# ── 9. Jarvis HTML ────────────────────────────────────────────────────────────
print("\n=== JARVIS VISUAL ===")
import pathlib
html = pathlib.Path("static/jarvis.html")
check("static/jarvis.html existe", html.exists(), f"{html.stat().st_size} bytes" if html.exists() else "FALTA")

# ── Resumen ───────────────────────────────────────────────────────────────────
print()
total = len(results)
passed = sum(results)
failed = total - passed

print("="*45)
print(f"  {passed}/{total} checks pasaron")
if failed == 0:
    print("  SISTEMA LISTO — puede arrancar")
    print()
    print("  Telegram:  python main.py")
    print("  Jarvis:    set TRANSPORT_MODE=voice && set ENABLE_HTTP=true && python main.py")
    print("  CLI debug: set TRANSPORT_MODE=cli && python main.py")
else:
    print(f"  {failed} problema(s) — revisar arriba")
print("="*45)

sys.exit(0 if failed == 0 else 1)
