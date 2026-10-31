"""
Smart Discovery — Jarvis hace las preguntas, arma el brief, lanza el proyecto
=============================================================================
Flujo:
  1. start(chat_id, description)  → detecta tipo, genera preguntas, retorna Q1
  2. answer(chat_id, text)        → guarda respuesta, retorna siguiente Q o "listo"
  3. Cuando termina → build_brief() + dispara /new automáticamente

Estados por chat_id:
  - type: tipo de proyecto detectado
  - description: descripción original
  - questions: lista de preguntas pendientes
  - answers: respuestas acumuladas
  - current_q: índice de pregunta actual
  - done: si ya se completó el discovery
"""

import logging
import re

from core.config import GROQ_API_KEY
from agents.project_templates import detect_type, get_template, TYPE_LABELS

log = logging.getLogger(__name__)

_sessions: dict[str, dict] = {}

MAX_QUESTIONS = 4  # Máximo de preguntas antes de generar el brief igual


def is_active(chat_id: str) -> bool:
    s = _sessions.get(str(chat_id))
    return s is not None and not s.get("done", False)


def clear(chat_id: str):
    _sessions.pop(str(chat_id), None)


async def start(chat_id: str, description: str) -> str:
    """
    Inicia discovery. Retorna la primera pregunta para el usuario.
    """
    cid = str(chat_id)

    # Detectar tipo de proyecto
    project_type = detect_type(description)
    template = get_template(project_type)
    label = TYPE_LABELS.get(project_type, project_type)

    # Refinar preguntas con LLM basándose en la descripción concreta
    questions = await _generate_questions(description, template)

    _sessions[cid] = {
        "type":        project_type,
        "label":       label,
        "description": description,
        "questions":   questions,
        "answers":     [],
        "current_q":   0,
        "done":        False,
    }

    log.info(f"[DISCOVERY] Iniciado: {label} | {len(questions)} preguntas")

    first_q = questions[0] if questions else None
    if not first_q:
        # No hay preguntas → lanzar directo
        return await _finalize(cid)

    intro = f"Entendido, vamos a construir {label}. Tengo {len(questions)} pregunta{'s' if len(questions) > 1 else ''}. "
    return intro + first_q


async def answer(chat_id: str, text: str) -> str:
    """
    Recibe una respuesta. Retorna la siguiente pregunta o el brief final.
    """
    cid = str(chat_id)
    s = _sessions.get(cid)
    if not s:
        return "No hay discovery activo."

    # Guardar respuesta
    q_idx = s["current_q"]
    if q_idx < len(s["questions"]):
        s["answers"].append({
            "question": s["questions"][q_idx],
            "answer":   text.strip(),
        })
    s["current_q"] += 1

    # ¿Hay más preguntas?
    if s["current_q"] < len(s["questions"]):
        next_q = s["questions"][s["current_q"]]
        log.info(f"[DISCOVERY] Q{s['current_q']+1}/{len(s['questions'])}")
        return next_q

    # Terminamos — generar brief y lanzar proyecto
    return await _finalize(cid)


async def _finalize(chat_id: str) -> str:
    """Construye el brief y dispara /new en el orchestrator."""
    s = _sessions[chat_id]
    s["done"] = True

    brief = await _build_brief(
        description=s["description"],
        project_type=s["type"],
        answers=s["answers"],
    )

    # Generar nombre del proyecto
    name = await _generate_name(s["description"], s["type"])

    # Disparar /new con el brief como initial_prompt
    try:
        from orchestrator.executor import process_message_with_prompt
        await process_message_with_prompt(chat_id, name, brief)
        log.info(f"[DISCOVERY] Proyecto lanzado: {name}")
        return (
            f"Perfecto, tengo todo lo que necesito. "
            f"Arranqué el proyecto '{name}'. "
            f"Voy al discovery con los agentes ahora."
        )
    except Exception as e:
        log.error(f"[DISCOVERY] Error lanzando proyecto: {e}")
        # Fallback: retornar el brief para que el usuario lo use
        return f"Listo el brief para '{name}'. Usa /new {name} para arrancarlo.\n\n{brief[:300]}..."


async def _generate_questions(description: str, template: dict) -> list[str]:
    """
    Usa Groq para generar preguntas específicas basadas en la descripción.
    Si falla, usa las preguntas del template.
    """
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)

        prompt = f"""El usuario quiere construir esto: "{description}"
Tipo detectado: {template['label']}
Stack sugerido: {template['tech_stack']}

Genera exactamente 3 preguntas cortas y directas para clarificar lo que falta.
Las preguntas deben ser específicas para ESTA descripción, no genéricas.
Cada pregunta en una línea. Solo las preguntas, sin numeración ni explicaciones.
No preguntes cosas que ya se mencionaron en la descripción."""

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )

        raw = response.choices[0].message.content or ""
        questions = [
            q.strip().lstrip("0123456789.-) ")
            for q in raw.strip().splitlines()
            if q.strip() and "?" in q
        ][:MAX_QUESTIONS]

        return questions if questions else template["questions"][:3]

    except Exception as e:
        log.warning(f"[DISCOVERY] LLM falló, usando template: {e}")
        return template["questions"][:3]


async def _build_brief(description: str, project_type: str, answers: list[dict]) -> str:
    """Construye el brief técnico completo con toda la info recopilada."""
    template = get_template(project_type)

    qa_text = "\n".join(
        f"- {a['question']}\n  → {a['answer']}"
        for a in answers
    )

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)

        prompt = f"""Construye un brief técnico completo para el siguiente proyecto.

Descripción: {description}
Tipo: {template['label']}
Stack recomendado: {template['tech_stack']}

Respuestas del usuario:
{qa_text if qa_text else "Sin respuestas adicionales."}

El brief debe incluir (en texto plano, sin markdown excesivo):
1. Objetivo del proyecto (1-2 líneas)
2. Usuarios objetivo
3. Funcionalidades principales (listadas)
4. Stack tecnológico confirmado
5. Consideraciones técnicas importantes
6. Lo que NO debe hacer (scope limits)

Sé específico y técnico. Este brief lo usan agentes de IA para generar el código."""

        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )

        return response.choices[0].message.content or _fallback_brief(description, template, answers)

    except Exception as e:
        log.warning(f"[DISCOVERY] Error generando brief: {e}")
        return _fallback_brief(description, template, answers)


def _fallback_brief(description: str, template: dict, answers: list[dict]) -> str:
    lines = [f"Proyecto: {description}", f"Tipo: {template['label']}", f"Stack: {template['tech_stack']}"]
    for a in answers:
        lines.append(f"{a['question']}: {a['answer']}")
    lines.append(template["agent_hints"])
    return "\n".join(lines)


async def _generate_name(description: str, project_type: str = "") -> str:
    """Genera un nombre corto para el proyecto."""
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)

        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"Genera un nombre corto (1-3 palabras, sin espacios, PascalCase) para este proyecto tipo {project_type or 'web'}: {description}. Solo el nombre, nada más."
            }],
            max_tokens=20,
            temperature=0.5,
        )
        raw = response.choices[0].message.content or ""
        name = re.sub(r"[^a-zA-Z0-9]", "", raw.strip().split()[0]) if raw.strip() else "MiProyecto"
        return name or "MiProyecto"
    except Exception:
        return "MiProyecto"
