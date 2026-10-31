---
name: saas-requirements-elicitation
description: >
  Genera preguntas de elicitación de requisitos profundas y personalizadas para un proyecto SaaS
  específico, basándose en el contexto que el usuario provee. Cubre requisitos funcionales,
  no funcionales, de roles/permisos, integraciones, seguridad, UX, cumplimiento y alcance MVP.
  Usar cuando el usuario diga cosas como "ayúdame a levantar requisitos", "necesito el PRD",
  "qué preguntas debo hacer antes de desarrollar", "cómo defino el alcance", "quiero escribir
  las historias de usuario", "qué entra en el MVP", o cuando comparta un proyecto SaaS y pida
  ayuda para definir QUÉ construir antes de ponerse a construirlo. Activar también si el usuario
  viene de la Fase 1 de Discovery y quiere avanzar. Disparar siempre que haya un proyecto de
  software y necesidad de definir, estructurar o documentar requisitos.
---

# SaaS Requirements Elicitation — Fase 2

## Propósito

A partir del contexto de un proyecto SaaS, generas preguntas de elicitación de requisitos que sean
**100% específicas al proyecto descrito** — sus actores reales, sus flujos reales, su sector real.
Nunca preguntas genéricas. Cada pregunta debe poder completarse con
"...en el caso de [nombre del producto]" y tener sentido inmediato.

---

## Paso 1 — Leer el contexto e inferir lo que importa

Antes de generar preguntas, analiza el contexto e identifica:

**Actores del sistema**
¿Quiénes interactúan con el sistema? Busca roles explícitos e implícitos.
Ejemplo: "SaaS para restaurantes" implica al menos: dueño, gerente, mesero, cocinero, cliente final.
Cada actor tiene flujos distintos. Cada flujo genera requisitos distintos.

**Entidades de datos principales**
¿Cuáles son los objetos de negocio que el sistema crea, lee, modifica o elimina?
Ejemplo: un SaaS de inventario tiene: producto, categoría, proveedor, movimiento, orden de compra.
Cada entidad tiene reglas de validación, estados, permisos y relaciones que elicitar.

**Flujos críticos**
¿Cuáles son los 3–5 flujos que, si no funcionan, el producto no tiene valor?
Ejemplo en un SaaS de firmas digitales: crear documento → enviar a firmar → firmar → descargar firmado.
Los flujos críticos generan el 80% de las preguntas funcionales.

**Señales de complejidad oculta**
Detecta features que parecen simples pero encierran alta complejidad técnica o de negocio:
- Notificaciones → ¿cuándo, a quién, por qué canal, qué pasa si falla el envío?
- Roles/permisos → ¿granularidad a nivel de campo? ¿roles dinámicos? ¿herencia?
- Pagos → ¿reembolsos, disputas, facturas, retención de impuestos?
- Reportes → ¿tiempo real o batch? ¿filtros complejos? ¿exportación? ¿scheduled?
- Búsqueda → ¿full-text? ¿filtros combinados? ¿resultados rankeados?
- Estados → ¿máquina de estados? ¿transiciones condicionales? ¿historial de estados?
- Multi-tenant → ¿aislamiento de datos? ¿configuración por tenant? ¿subdominios?
- Integraciones → ¿sync bidireccional? ¿webhooks? ¿manejo de errores y reintentos?
- IA/ML → ¿feedback loop? ¿datos de entrenamiento? ¿explicabilidad de resultados?

**Sector y regulación**
El sector determina restricciones no negociables. Ver `references/sector-constraints.md`
para los requisitos implícitos de cada sector (fintech, healthtech, edtech, marketplace, enterprise, HR, legal).

---

## Paso 2 — Generar preguntas contextuales por dimensión

Para cada dimensión, genera preguntas usando los **patrones de razonamiento** que siguen.
No copies preguntas genéricas: construye cada pregunta a partir del contexto leído.

### Dimensión 1 — Flujos funcionales

**Patrón de razonamiento:**
Para cada flujo crítico identificado en el Paso 1, pregunta por:
- El happy path completo paso a paso
- Los datos de entrada que el usuario provee
- Las validaciones que el sistema debe aplicar
- Los datos de salida o efectos que produce el flujo
- Los estados intermedios y finales del flujo
- Lo que pasa si se interrumpe o falla a mitad
- Los casos borde que el equipo normalmente no anticipa

**Ejemplo de transformación contexto → pregunta:**
Contexto: "SaaS para agendar citas médicas"
Pregunta genérica (mala): "¿Cuáles son los flujos del sistema?"
Pregunta contextual (buena): "Cuando un paciente agenda una cita, ¿qué pasa si el médico tiene ese horario disponible en el sistema pero está de vacaciones? ¿Quién bloquea esas horas y cómo?"

**Áreas que siempre cubrir en flujos:**
- Creación del recurso principal (el objeto de negocio central del SaaS)
- Edición y eliminación — ¿qué restricciones existen? ¿se puede eliminar si tiene dependencias?
- Flujos de aprobación si existen — ¿quién aprueba, qué niveles, qué pasa si rechaza?
- Flujos de cierre periódico si existen — cierre de mes, liquidación, renovación
- Flujos de estado si el recurso tiene lifecycle — borrador, activo, suspendido, archivado
- Acciones bulk — ¿se pueden hacer operaciones sobre múltiples registros?
- Flujos de importación/exportación si el usuario lo mencionó

### Dimensión 2 — Roles y permisos

**Patrón de razonamiento:**
Para cada actor identificado, pregunta por:
- Las acciones que puede hacer sobre cada entidad de datos
- Las acciones que explícitamente NO puede hacer y qué pasa si lo intenta
- Si los permisos son fijos o configurables por tenant
- Si hay visibilidad parcial de datos (solo ve sus propios registros, solo su equipo, etc.)
- Si hay campos que un rol ve pero otro no dentro del mismo formulario

**Ejemplo:**
Contexto: "plataforma de gestión de proyectos para agencias"
Pregunta contextual: "¿Un cliente externo invitado al proyecto puede ver los costos internos del equipo y las horas trabajadas, o solo los entregables y comentarios que le corresponden?"

### Dimensión 3 — Requisitos no funcionales

**Patrón de razonamiento:**
Los NFRs dependen del contexto del producto:
- Si es crítico para el negocio del cliente → preguntar por SLA y disponibilidad
- Si maneja datos sensibles → preguntar por cifrado, retención y auditoría
- Si tiene picos de uso predecibles → preguntar por escalabilidad y auto-scaling
- Si tiene usuarios en múltiples países → preguntar por latencia, regiones y regulación de datos
- Si procesa volumen alto → preguntar por rendimiento y tiempos de respuesta aceptables

**Áreas a cubrir según el proyecto:**
- Tiempo de respuesta aceptable para las operaciones más críticas
- Número de usuarios concurrentes en MVP y en 12 meses
- Disponibilidad requerida (SLA) y ventanas de mantenimiento aceptables
- Volumen de datos esperado y crecimiento proyectado
- Requisitos de backup, recuperación ante desastres y RPO/RTO

### Dimensión 4 — Seguridad y autenticación

**Patrón de razonamiento:**
Todo SaaS necesita responder:
- ¿Cómo se autentica el usuario? (email/password, SSO, OAuth, Magic Link, MFA)
- ¿Cómo se gestionan las sesiones? ¿Hay timeout? ¿Se puede tener sesión en múltiples dispositivos?
- ¿Cómo se protegen los datos en tránsito y en reposo?
- ¿Hay un log de auditoría de acciones sensibles?
- ¿Qué pasa con los datos cuando el cliente cancela?

Preguntar en profundidad solo si el contexto indica datos sensibles (salud, financiero, legal, RRHH).

### Dimensión 5 — Integraciones y datos externos

**Patrón de razonamiento:**
Identifica qué integraciones son probablemente necesarias según el sector y el contexto:
- ¿Con qué sistemas ya tiene el cliente para que el SaaS los reemplace o complemente?
- ¿Hay una integración sin la cual el producto no funciona (bloqueante) vs. las que son nice-to-have?
- Para cada integración: ¿es lectura, escritura o ambas? ¿Es en tiempo real o batch? ¿Qué pasa si falla?
- ¿El SaaS expone su propia API para que terceros lo consuman?

### Dimensión 6 — Notificaciones y comunicaciones

**Patrón de razonamiento:**
Las notificaciones son feature de alta complejidad oculta. Preguntar:
- ¿Qué eventos del sistema generan notificaciones? (creación, cambio de estado, vencimiento, error)
- ¿Por qué canales? (email, push, SMS, in-app, Slack, WhatsApp)
- ¿Son configurables por el usuario o son fijas?
- ¿Hay notificaciones recurrentes (recordatorios, resúmenes diarios)?
- ¿Qué pasa si el envío falla? ¿Hay reintentos?
- ¿Quién puede ver el historial de notificaciones enviadas?

### Dimensión 7 — Experiencia de usuario y onboarding

**Patrón de razonamiento:**
El onboarding define la tasa de activación. Preguntar:
- ¿Cuál es el "aha moment" y cuántos pasos separan el registro del primer valor real?
- ¿El onboarding es el mismo para todos los roles o personalizado?
- ¿Hay datos o configuraciones que el admin debe completar antes de que el equipo pueda usar el producto?
- ¿Hay un estado vacío (zero state) que el usuario ve antes de tener datos? ¿Cómo se maneja?
- ¿El usuario puede usar el producto en móvil? ¿Hay diferencias de funcionalidad?

### Dimensión 8 — Cumplimiento y regulación

**Patrón de razonamiento:**
Según el sector, inferir los requisitos de cumplimiento implícitos.
Ver `references/sector-constraints.md` para la lista detallada por sector.
Siempre preguntar como mínimo:
- ¿En qué países opera el producto? ¿Hay restricciones de residencia de datos?
- ¿El producto maneja datos personales que requieran consentimiento explícito?
- ¿Hay normativa sectorial específica que exija features de auditoría, retención o cifrado?
- ¿Se requiere accesibilidad WCAG?

### Dimensión 9 — Priorización y alcance del MVP

**Patrón de razonamiento:**
El MVP debe resolver exactamente UN problema para UN segmento de forma 10x mejor.
Preguntar para cada feature mencionada:
- ¿Es el MVP imposible de usar sin esta feature? → Must Have
- ¿Sin esta feature el MVP funciona pero tiene fricción alta? → Should Have
- ¿Esta feature está en el MVP por costumbre o porque realmente la necesita el usuario el día 1? → Cuestionar
- ¿Cuál es la feature que más tarda en construirse? ¿Vale ese esfuerzo para el MVP?

### Dimensión 10 — Criterios de aceptación y definición de "Done"

**Patrón de razonamiento:**
Para cada historia de usuario, los criterios deben ser verificables sin interpretación.
El formato Given/When/Then obliga a especificar el contexto, la acción y el resultado exacto.
Detectar y preguntar sobre:
- Flujos donde el criterio de éxito no es binario (ej: "funciona bien" no es un criterio)
- Features donde los estados de error son tan importantes como el happy path
- Historias que dependen de datos externos o integraciones (¿qué se simula en testing?)
- Features donde el criterio de "Done" incluye rendimiento o carga, no solo funcionalidad

---

## Paso 3 — Output estructurado

Siempre entrega el output en este orden:

### Parte A — Preguntas de elicitación
45–65 preguntas organizadas en las dimensiones relevantes para el proyecto.
Cada pregunta debe ser específica al contexto. Incluir sub-preguntas para temas complejos.

### Parte B — Esqueleto de PRD personalizado
Genera el PRD con las secciones ya nombradas según el proyecto:
- No "Módulo X" genérico, sino "Módulo de Gestión de [entidad real del proyecto]"
- No "Rol A", sino los nombres reales de los roles identificados
- Incluye una sección explícita de "Fuera de alcance del MVP" con al menos 3 items

### Parte C — Ejemplo de historia de usuario con Given/When/Then
Una historia de usuario completa para el flujo más crítico del proyecto, con:
- Al menos 3 criterios de aceptación (happy path + 2 casos de error)
- Prioridad MoSCoW
- Dependencias técnicas si las hay

### Parte D — Alertas de complejidad oculta
2–4 features que parecen simples pero tienen alta complejidad técnica o de negocio.
Para cada una: qué hace que sea compleja y qué decisiones de diseño debe tomar el equipo antes de codificar.

---

## Reglas de calidad

- Si el contexto es muy vago (menos de 2 oraciones), pide UNA aclaración: el flujo principal del sistema.
- Nunca escribas una pregunta que un equipo de cualquier SaaS podría recibir sin cambiarle una palabra.
- Las preguntas de permisos siempre incluyen el caso negativo: ¿qué pasa cuando el rol X intenta hacer Y?
- Las preguntas de flujos siempre incluyen al menos una sobre el estado de error o caso borde.
- El esqueleto de PRD debe usar los nombres reales del negocio del cliente, no placeholders genéricos.
- Si detectas que el usuario mencionó una feature con alta complejidad oculta, siempre desglosarla en sub-preguntas.

---

## Referencias

- `references/sector-constraints.md` — Requisitos implícitos por sector (leer cuando el proyecto pertenece a un sector específico)
- `references/user-story-templates.md` — Templates de historias de usuario por tipo de feature con ejemplos Given/When/Then
