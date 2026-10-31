"""
Executor — Motor de ejecución del DAG.
Maneja ejecución secuencial Y paralela, rollback, circuit breaker,
y la lógica de loop para fases de implementación (6a/6b/6c).
"""

import asyncio
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

from agents.base import AgentContext, AgentOutput
from orchestrator.dag import AGENT_MAP, PHASE_ORDER, PHASE_LABELS, get_parallel_group, next_phase
from memory import session_store as store
from memory import engram
from core.config import WORKSPACES_PATH


MAX_RETRIES = 3  # Circuit breaker por fase


def _notify(message: str):
    """Push no-bloqueante al bus de notificaciones de voz."""
    try:
        from core.notifications import push_sync
        push_sync(message)
    except Exception:
        pass


async def run_phase(phase: str, ctx: AgentContext) -> AgentOutput:
    """Ejecuta un agente simple."""
    agent = AGENT_MAP[phase]
    return await agent.run(ctx)


async def run_parallel_group(group: list[str], ctx: AgentContext) -> dict[str, AgentOutput]:
    """Ejecuta varias fases en paralelo y retorna dict {phase: output}."""
    tasks = [run_phase(phase, ctx) for phase in group]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    outputs = {}
    for phase, result in zip(group, results):
        if isinstance(result, Exception):
            outputs[phase] = AgentOutput(
                phase=phase,
                content=f"❌ Error en {phase}: {result}",
                completed=False,
            )
        else:
            outputs[phase] = result
    return outputs


def _make_ctx(state: dict) -> AgentContext:
    return AgentContext(
        project=state["project"],
        chat_id=state["chat_id"],
        phase_outputs=state.get("outputs", {}),
        initial_prompt=state.get("initial_prompt", ""),
    )


def _save_output(project: str, phase: str, content: str):
    """Guarda el output de un agente en el workspace del proyecto."""
    clean = re.sub(r"[^\w\s-]", "", project).strip().replace(" ", "_")
    path = Path(WORKSPACES_PATH) / clean / f"{phase}_output.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    # Extraer y guardar archivos de código si el agente los generó
    pattern = r"FILE:\s*([^\n]+)\s*\n```[a-zA-Z]*\n(.*?)```"
    for match in re.finditer(pattern, content, re.DOTALL):
        filepath = match.group(1).strip()
        code = match.group(2).strip()
        if len(filepath) > 2 and "\n" not in filepath:
            full = Path(WORKSPACES_PATH) / clean / filepath
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(code, encoding="utf-8")


async def advance(chat_id: str) -> str:
    """
    Avanza el DAG un paso. Retorna el mensaje de respuesta para Telegram.
    Maneja: fases secuenciales, grupos paralelos, loop de implementación.
    """
    state = store.get(str(chat_id))
    phase = state["phase"]
    project = state["project"]

    label = PHASE_LABELS.get(phase, phase.upper())
    ctx = _make_ctx(state)

    # ── Verificar circuit breaker ─────────────────────────────────────────
    errors = state.get("error_counts", {})
    if errors.get(phase, 0) >= MAX_RETRIES:
        return (
            f"🛑 *Circuit Breaker activado en {label}*\n"
            f"El agente falló {MAX_RETRIES} veces. Revisa el workspace y usa "
            f"`/rollback {phase}` para reintentar desde cero."
        )

    # ── Decidir si es paralelo o secuencial ───────────────────────────────
    group = get_parallel_group(phase)

    if group and phase == group[0]:
        # Primer elemento del grupo — ejecutar todo el grupo en paralelo
        group_results = await run_parallel_group(group, ctx)

        all_ok = all(r.completed for r in group_results.values())
        for p, output in group_results.items():
            _save_output(project, p, output.content)
            state["outputs"][p] = output.content[:2000]
            engram.save_signal(project, p, "summary" if output.completed else "error",
                               output.content[-300:])

        store.save(str(chat_id), state)

        if not all_ok:
            failed = [p for p, r in group_results.items() if not r.completed]
            return (
                f"⚠️ *{label} — Grupo paralelo con problemas*\n"
                f"Fases incompletas: {', '.join(failed)}\n"
                f"Escribe `/go` para reintentar o `/rollback <fase>` para ajustar."
            )

        # Avanzar al siguiente nodo tras el grupo
        next_p = next_phase(phase)
        if next_p:
            state["phase"] = next_p
            state["phase_index"] = PHASE_ORDER.index(next_p)
            store.save(str(chat_id), state)

        phases_done = " + ".join(PHASE_LABELS.get(p, p) for p in group)
        previews = "\n".join(
            f"**{PHASE_LABELS.get(p,p)}:** {r.content[:200]}..."
            for p, r in group_results.items()
        )
        return (
            f"✅ *Grupo paralelo completado:*\n{phases_done}\n\n"
            f"{previews}\n\n"
            f"➡️ Siguiente: *{PHASE_LABELS.get(next_p, 'Proyecto completo')}*\n"
            f"Escribe `/go` para continuar."
        )

    elif group and phase != group[0]:
        # Miembro no-primero de un grupo — ya fue ejecutado como parte del primero
        # Avanzar al siguiente
        next_p = next_phase(phase)
        if next_p:
            state["phase"] = next_p
            state["phase_index"] = PHASE_ORDER.index(next_p)
            store.save(str(chat_id), state)
        return f"Ya completado en grupo paralelo. Siguiente: {PHASE_LABELS.get(next_p,'fin')}"

    else:
        # Fase secuencial normal
        output = await run_phase(phase, ctx)
        _save_output(project, phase, output.content)

        if not output.completed:
            errors[phase] = errors.get(phase, 0) + 1
            state["error_counts"] = errors
            store.save(str(chat_id), state)
            return (
                f"⏳ *{label} — En progreso*\n\n"
                f"{output.content[:800]}\n\n"
                f"⚠️ Fase incompleta (intento {errors[phase]}/{MAX_RETRIES}). "
                f"Escribe `/go` para continuar o responde con más contexto."
            )

        # Guardar output y avanzar
        state["outputs"][phase] = output.content[:2000]
        state["error_counts"].pop(phase, None)

        next_p = next_phase(phase)
        if next_p:
            state["phase"] = next_p
            state["phase_index"] = PHASE_ORDER.index(next_p)
            store.save(str(chat_id), state)
            next_label = PHASE_LABELS.get(next_p, next_p)
            _notify(f"Terminé {label}. Siguiente es {next_label}. Di go cuando quieras continuar.")
            return (
                f"✅ *{label} completada*\n\n"
                f"{output.content[:1000]}\n\n"
                f"➡️ Siguiente: *{next_label}*\n"
                f"Escribe `/go` para continuar."
            )
        else:
            store.save(str(chat_id), state)
            engram.engram_sync()
            _notify(f"Proyecto {project} completado. Todo el código está listo.")
            return (
                f"🎉 *¡Proyecto '{project}' COMPLETADO!*\n\n"
                f"Todos los agentes ejecutados. El código está en:\n"
                f"`workspaces/{project}/`\n\n"
                f"Usa `/new [nombre]` para iniciar otro proyecto."
            )


async def process_message_with_prompt(chat_id: str, project_name: str, initial_prompt: str) -> str:
    """
    Llamado desde smart_discovery cuando tiene el brief completo.
    Crea el proyecto e inyecta el prompt rico como initial_prompt.
    """
    store.reset(str(chat_id), project_name)
    state = store.get(str(chat_id))
    state["initial_prompt"] = initial_prompt
    store.save(str(chat_id), state)
    # Arrancar discovery automáticamente con el brief
    return await advance(str(chat_id))


async def run_autopilot(chat_id: str) -> None:
    """
    Ejecuta todas las fases pendientes del DAG en background.
    Notifica por voz después de cada fase.
    """
    import asyncio
    cid = str(chat_id)
    MAX_PHASES = 15  # Límite de seguridad

    for _ in range(MAX_PHASES):
        state = store.get(cid)
        phase = state["phase"]

        # Chequear si ya terminamos
        if not next_phase(phase) and state["outputs"].get(phase):
            break

        try:
            await advance(cid)
            # La notificación ya se manda dentro de advance()
        except Exception as e:
            _notify(f"Error en {phase}: {str(e)[:60]}. Revisando...")
            break

        # Pequeña pausa entre fases para no saturar el rate limit
        await asyncio.sleep(3)

    _notify("Autopilot completado. Revisa el resultado.")


def _is_assistant_mode(state: dict) -> bool:
    """True cuando no hay proyecto real activo — Jarvis responde como asistente libre.
    Solo sale de modo asistente cuando el usuario inició un proyecto con /new <nombre>."""
    return state["project"] == "nuevo_proyecto"


async def process_message(chat_id: str, text: str) -> str:
    """Punto de entrada del orquestador. Recibe cualquier mensaje de Telegram/Voz."""
    text = text.strip()
    state = store.get(str(chat_id))

    # ── Smart Discovery activo — enrutar respuestas al Q&A ───────────────
    if not text.startswith("/"):
        from agents.smart_discovery import is_active as disc_active, answer as disc_answer
        if disc_active(str(chat_id)):
            return await disc_answer(str(chat_id), text)

    # ── Modo asistente libre (sin proyecto activo) ────────────────────────
    if not text.startswith("/") and _is_assistant_mode(state):
        from agents.jarvis_assistant import run as assistant_run
        return await assistant_run(text, chat_id=str(chat_id))

    # ── Comandos ──────────────────────────────────────────────────────────

    if text.startswith("/new"):
        parts = text.split(" ", 1)
        project = parts[1].strip() if len(parts) > 1 else "nuevo_proyecto"
        store.reset(str(chat_id), project)
        # Limpiar historial del asistente al iniciar proyecto
        try:
            from agents.jarvis_assistant import clear_history
            clear_history(str(chat_id))
        except Exception:
            pass
        # Scaffold base del proyecto en workspaces/
        scaffold_msg = ""
        try:
            from tools.scaffold import scaffold_project
            from agents.project_templates import detect_type
            from memory import session_store as _s
            _st = _s.get(str(chat_id))
            ptype = _st.get("project_type", "web_saas")
            result = scaffold_project(WORKSPACES_PATH, project, ptype)
            scaffold_msg = f"\n\n📁 _{result.splitlines()[0]}_"
            log.info(f"[SCAFFOLD] {result}")
        except Exception as e:
            log.warning(f"[SCAFFOLD] Falló (no crítico): {e}")
        return (
            f"🚀 *Nuevo proyecto iniciado: {project}*{scaffold_msg}\n\n"
            f"Estoy listo para el *Discovery*.\n"
            f"Cuéntame: ¿qué problema quieres resolver y para quién?\n\n"
            f"_(O escribe `/go` para que yo haga las preguntas)_"
        )

    if text == "/go":
        return await advance(chat_id)

    if text == "/status":
        phase = state["phase"]
        idx = PHASE_ORDER.index(phase) + 1
        return (
            f"📊 *Estado del proyecto*\n"
            f"Proyecto: *{state['project']}*\n"
            f"Fase actual: *{PHASE_LABELS.get(phase, phase)}*\n"
            f"Progreso: {idx}/{len(PHASE_ORDER)}\n\n"
            f"Escribe `/go` para continuar."
        )

    if text.startswith("/rollback"):
        parts = text.split(" ", 1)
        if len(parts) < 2 or parts[1].strip() not in PHASE_ORDER:
            return f"Uso: `/rollback <fase>`\nFases: {', '.join(PHASE_ORDER)}"
        target = parts[1].strip()
        state["phase"] = target
        state["phase_index"] = PHASE_ORDER.index(target)
        state["error_counts"] = {}
        # Limpiar outputs posteriores al rollback
        idx = PHASE_ORDER.index(target)
        for p in PHASE_ORDER[idx:]:
            state["outputs"].pop(p, None)
        store.save(str(chat_id), state)
        return (
            f"⏪ *Rollback a {PHASE_LABELS.get(target, target)}*\n"
            f"Escribe `/go` para re-ejecutar desde aquí."
        )

    if text.startswith("/auto"):
        parts = text.split(" ")
        n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
        state["auto_limit"] = n
        store.save(str(chat_id), state)
        return f"🤖 *Modo automático: {n} pasos*\nEjecutando..."

    if text == "/stop":
        state["auto_limit"] = 0
        store.save(str(chat_id), state)
        return "🛑 Modo automático detenido."

    if text == "/spec":
        outputs = state.get("outputs", {})
        spec = outputs.get("tech_spec") or outputs.get("requirements") or "No hay spec generado aún."
        return f"📋 *Spec actual:*\n```\n{spec[:1500]}\n```"

    # ── Conversación en fase discovery de un proyecto REAL ───────────────
    # Solo llega aquí si hay un proyecto real activo (no "nuevo_proyecto")
    phase = state["phase"]
    if phase == "discovery" and state["project"] != "nuevo_proyecto":
        prev = state.get("initial_prompt", "")
        state["initial_prompt"] = (prev + "\n" + text).strip()
        store.save(str(chat_id), state)
        engram.save_signal(state["project"], "user", "decision", f"Input usuario: {text[:150]}")
        return await advance(chat_id)

    # Cualquier otro mensaje en otras fases
    return (
        f"💬 Recibido. Proyecto: *{state['project']}* | Fase: *{PHASE_LABELS.get(phase, phase)}*\n"
        f"Escribe `/go` para continuar, `/status` para ver el estado."
    )
