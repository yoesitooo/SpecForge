---
name: saas-discovery-elicitation
description: >
  Generates a deep, personalized set of Discovery & Problem Framing questions (Phase 1 of SaaS construction)
  tailored to whatever project context the user provides. Use this skill whenever a user shares context
  about a SaaS idea, startup, or product they want to build and asks for discovery questions, elicitation
  questions, validation questions, or anything related to understanding the problem space before building.
  Also trigger when the user says things like "ayúdame a validar mi idea", "qué preguntas debo hacerme",
  "hazme las preguntas de discovery", "quiero explorar mi idea de SaaS", or similar.
  This skill should trigger even if the user only gives a brief description of their project.
---

# SaaS Discovery Elicitation — Fase 1

## Objetivo

Dado un contexto de proyecto (puede ser una frase corta, un párrafo o una descripción detallada),
generas un set completo y PERSONALIZADO de preguntas de elicitación para la Fase 1: Discovery & Problem Framing.

Las preguntas deben ayudar al fundador/equipo a:
1. Validar que el problema es real y doloroso
2. Definir con precisión el usuario objetivo
3. Entender el mercado y la competencia
4. Dimensionar la oportunidad económica
5. Detectar riesgos tempranos antes de escribir código

---

## Proceso

### Paso 1 — Extraer el contexto del proyecto

Lee lo que el usuario compartió e identifica los siguientes elementos (pueden estar implícitos o explícitos):

- **Dominio**: ¿En qué industria o sector opera el SaaS? (finanzas, salud, educación, logística, etc.)
- **Problema base**: ¿Qué problema intenta resolver?
- **Usuario objetivo**: ¿Para quién es? (B2B, B2C, B2B2C, enterprise, SMB, consumidor final)
- **Solución propuesta**: ¿Qué planea construir?
- **Estadio actual**: ¿Tiene código? ¿Solo la idea? ¿Ya tiene clientes?
- **Lagunas de información**: ¿Qué aspectos críticos NO mencionó y son riesgosos?

### Paso 2 — Generar preguntas personalizadas

Genera preguntas organizadas en 6 bloques. Cada pregunta debe:
- Estar **directamente conectada al contexto específico** del proyecto (no ser genérica)
- Señalar **por qué importa** esa pregunta para ESTE proyecto en particular
- Incluir **sub-preguntas de profundización** cuando el tema lo amerite
- Usar el idioma del usuario (si escribe en español, responde en español; si en inglés, en inglés)

**Bloques obligatorios** (ver detalles en `references/question-blocks.md`):
1. Problema & Dolor — ¿Es real? ¿Es urgente? ¿Cuánto duele?
2. Usuario & Segmento — ¿Quién exactamente? ¿Cuál es su contexto?
3. Mercado & Competencia — ¿Qué existe hoy? ¿Hay espacio?
4. Modelo de negocio & Monetización — ¿Pagarán? ¿Cuánto?
5. Riesgos & Suposiciones — ¿Qué puede matar este negocio?
6. Próximos pasos concretos — ¿Cómo validar antes de construir?

### Paso 3 — Señalar alertas rojas

Al final, incluye una sección **"⚠ Alertas de este proyecto"** donde señalas:
- Las 2–3 suposiciones más peligrosas que el usuario está haciendo
- Los puntos ciegos más frecuentes en proyectos de este tipo
- Una recomendación concreta de qué validar PRIMERO

---

## Formato de salida

```
## Contexto que entendí
[Resumen en 3–5 líneas de lo que captaste del proyecto, incluyendo lo que está implícito]

---

## 🔍 Preguntas de Discovery — [Nombre del proyecto o descripción corta]

### 1. Problema & Dolor
[5–8 preguntas personalizadas con contexto de por qué importan]

### 2. Usuario & Segmento objetivo
[5–7 preguntas personalizadas]

### 3. Mercado & Competencia
[4–6 preguntas personalizadas]

### 4. Modelo de negocio & Monetización
[4–6 preguntas personalizadas]

### 5. Riesgos & Suposiciones críticas
[4–5 preguntas personalizadas]

### 6. Próximos pasos para validar
[3–5 acciones concretas priorizadas, no solo preguntas]

---

## ⚠ Alertas de este proyecto
[2–3 alertas específicas al contexto dado]
```

---

## Reglas de calidad

- **Nunca** generes preguntas genéricas que apliquen a cualquier SaaS. Cada pregunta debe poder completarse con "...en el caso de [nombre del proyecto]".
- Si el contexto es muy vago (ej. "quiero hacer un SaaS de finanzas"), pide UNA aclaración clave antes de generar — solo una, la más bloqueante.
- Prioriza preguntas que el fundador **no se haría solo** — las incómodas, las que cuestionan la premisa.
- Las preguntas de monetización deben incluir rangos de precio específicos del sector si los conoces.
- En los próximos pasos, sugiere métodos de validación concretos: entrevistas de problema, landing page + waitlist, wizard of oz, etc.

---

## Referencia complementaria

Lee `references/question-blocks.md` si necesitas ampliar el banco de preguntas por bloque
o adaptar para sectores específicos (healthtech, fintech, edtech, B2B enterprise, marketplace, etc.)
