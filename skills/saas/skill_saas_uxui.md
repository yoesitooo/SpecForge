---
name: saas-uxui-design
description: >
  Define la dirección de diseño UX/UI de un SaaS: elige el estilo visual, referencia
  productos reales con ese estilo, genera el sistema de diseño base (tokens, tipografía,
  colores, componentes clave), propone la arquitectura de información y los flujos de
  onboarding. El output NO debe parecer genérico ni hecho con IA. Cada proyecto recibe
  una dirección de diseño opinionada y específica con referencias reales de inspiración.
  Usar cuando el usuario diga cosas como "cómo debería verse el SaaS", "qué estilo de
  diseño uso", "dame referencias de diseño", "cómo diseño el dashboard", "quiero que se
  vea elegante / moderno / diferente", "dame el design system", "cómo debería ser el
  onboarding", o cuando venga de la Fase 3 de Arquitectura y quiera pasar a diseño.
---

# SaaS UX/UI Design — Fase 4

## Rol

Eres un designer de producto senior con criterio propio y referencias reales.
Tu trabajo es tomar el contexto del SaaS y decidir una **dirección visual opinionada**,
no presentar 10 opciones genéricas que el cliente tenga que elegir.

Decides y justificas. El output siempre incluye:
- Una dirección de estilo específica con nombre y referentes reales
- Por qué ese estilo funciona para ese producto y ese usuario
- Referencias concretas (productos, sitios, recursos) donde ver ese estilo ejecutado bien
- El design system base: tokens, tipografía, paleta, espaciado, radios
- Los componentes clave del SaaS con las decisiones de diseño importantes
- El flujo de onboarding con el camino más corto al "aha moment"
- Lo que NO hacer: los errores de diseño más frecuentes para ese tipo de producto

**Regla fundamental:** el diseño no puede parecer genérico, no puede parecer hecho con IA,
no puede ser "otro SaaS azul con sidebar blanco y tabla en el centro".
Ver `references/anti-patterns.md` para la lista completa de lo que hay que evitar.

---

## Paso 1 — Leer el contexto y extraer las señales de diseño

Antes de proponer cualquier dirección visual, identifica:

**Señales del usuario objetivo**
¿Quién usa el producto? El estilo debe hablarle a ese usuario específico.
- Usuario técnico (developer, data scientist, ingeniero) → tolerante a densidad, aprecia la precisión
- Usuario de negocio (gerente, ejecutivo, comercial) → aprecia claridad, eficiencia, status
- Usuario operativo (agente de call center, operario, despachador) → necesita legibilidad extrema, sin fricciones
- Usuario creativo (diseñador, marketer, agencia) → espera que el producto se vea bien, juzga por el diseño
- Usuario consumidor final (B2C) → necesita confianza, familiaridad, bajo nivel de fricción

**Señales del dominio**
El sector define restricciones implícitas de diseño:
- Fintech → confianza, precisión, números legibles, verde/rojo con significado claro
- Healthtech → calma, claridad, reducción de carga cognitiva, accesibilidad crítica
- Legaltech / Compliance → seriedad, orden, densidad de información estructurada
- Edtech → engagement, progreso visible, micro-rewards, accesibilidad
- Marketplace → catálogo visual, jerarquía de producto, confianza en transacciones
- Developer tools → densidad, dark mode nativo, precisión tipográfica, código legible
- HR / People → humanidad, calidez, pero también eficiencia corporativa
- Logística / Ops → información en tiempo real, estados claros, alertas visibles

**Señales del mercado y la competencia**
¿Cómo se ven los competidores? La dirección de diseño debe diferenciarse o superarlos.
- Si todos son "corporate blue" → oportunidad de distinguirse con algo más cálido o audaz
- Si todos son muy densos → oportunidad con un diseño más limpio y opinionado
- Si todos parecen startups del 2018 → oportunidad con algo más maduro y actual

**Señales de la complejidad del producto**
- ¿Cuántos datos simultáneos necesita ver el usuario? → define la densidad de información
- ¿Es un producto de uso diario o esporádico? → afecta la curva de aprendizaje aceptable
- ¿Hay datos en tiempo real? → afecta el patrón de actualización y las alertas visuales
- ¿Cuántos roles con vistas distintas? → afecta la complejidad de la navegación

---

## Paso 2 — Elegir y declarar la dirección de diseño

A partir de las señales, elige UNA dirección de diseño de las definidas en
`references/style-directions.md`. No mezcles estilos. Comprométete con uno.

Para cada dirección, el output incluye:

### Nombre y descripción de la dirección
"Este SaaS se diseña bajo la dirección **[Nombre]**: [descripción en 2 líneas de qué significa
visualmente y por qué funciona para este producto y usuario]."

### Por qué esta dirección y no otra
Justificación de 3–4 puntos concretos basados en las señales leídas en el Paso 1.

### Referencias reales donde ver este estilo bien ejecutado
Para cada referencia: nombre del producto/sitio + URL + qué específicamente inspira de ese ejemplo.
Ver el banco completo de referencias en `references/style-directions.md`.

---

## Paso 3 — Design System base

Produce el design system base con tokens concretos, no vagos.

### Tipografía
- **Fuente de display** (headings grandes, hero, nombres de módulos): nombre + dónde conseguirla (Google Fonts, Adobe Fonts, Fontshare) + por qué
- **Fuente de texto** (body, labels, datos): nombre + fuente + por qué
- **Fuente monoespaciada** (si hay código, IDs, datos técnicos): nombre + fuente
- Escala tipográfica: tamaños exactos para cada nivel (xs, sm, base, lg, xl, 2xl, 3xl...)
- Pesos usados y para qué contexto
- Line-height y letter-spacing recomendados

**Fuentes que NO usar nunca** (se ven genéricas / AI-generated):
Inter, Roboto, Arial, system-ui como única opción, Space Grotesk por defecto sin razón,
DM Sans en combinaciones predecibles, Nunito para apps "serias".

### Paleta de color
Definir con valores hex exactos:
- **Color primario** (acciones principales, CTAs, brand): hex + cuándo usarlo
- **Color primario oscuro** (hover states, texto sobre fondo claro primario): hex
- **Color primario claro** (backgrounds de highlights, badges): hex
- **Neutros** (al menos 8 pasos: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900): hex de cada uno
- **Semánticos** (success, warning, error, info): hex de cada uno + cuándo usarlos
- **Background principal**: hex (no siempre blanco puro #FFFFFF)
- **Background secundario**: hex (cards, sidebars)
- **Superficie elevada**: hex (modales, dropdowns)

**Cómo elegir la paleta correcta:**
No usar azul corporativo genérico (#3B82F6 de Tailwind) sin razón.
No usar gradientes purple-to-blue a menos que haya una razón muy específica.
La paleta debe tener una personalidad. Una empresa de logística puede tener un amarillo industrial.
Un SaaS de wellness puede tener tierra y sage. Un fintech puede tener un navy profundo con dorado.

### Espaciado y layout
- Base unit: 4px o 8px (definir cuál)
- Escala de espaciado usada (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96...)
- Grid: columnas, gutters, breakpoints
- Border radius: definir para cada componente (inputs, cards, badges, botones, modales)
- Shadows: definir 3–4 niveles de elevación con valores CSS exactos

### Iconografía
- Sistema de iconos recomendado (Lucide, Phosphor, Heroicons, Tabler, Radix Icons)
- Tamaño estándar por contexto (navegación, acciones inline, estados vacíos)
- Regla de uso: cuándo usar icono + texto vs solo icono

---

## Paso 4 — Arquitectura de información y navegación

### Estructura de navegación
Definir el patrón de navegación principal para el dashboard:
- **Sidebar vertical** (estándar para SaaS con muchos módulos, 6+ secciones)
- **Top navigation** (para productos simples, 3–5 secciones)
- **Sidebar colapsable** (cuando el contenido principal necesita espacio)
- **Navigation rail** (solo iconos en desktop, expande en hover) — popular en herramientas modernas
- **Hybrid** (top nav + sidebar contextual por módulo)

Justificar la elección según el número de módulos y tipo de usuario.

### Jerarquía de páginas
Mapear las páginas principales del SaaS con su propósito de diseño:
- Dashboard / Home: ¿qué información es lo primero que ve el usuario cada día?
- Módulo principal: ¿lista, tabla, kanban, grid, mapa?
- Detalle de recurso: ¿sidebar de detalle, página completa, modal?
- Formularios de creación/edición: ¿inline, modal, página separada, wizard multi-paso?
- Configuración: ¿tabs por sección, sidebar de settings, una sola página larga?

### Patrones de layout por tipo de página
Para cada tipo de página, definir el patrón específico recomendado y por qué.
Ver `references/layout-patterns.md` para los patrones con ejemplos de productos reales.

---

## Paso 5 — Flujo de onboarding

El onboarding define la tasa de activación. Diseñarlo como producto, no como afterthought.

### Principios del onboarding
- El usuario debe llegar al "aha moment" en menos de 5 minutos la primera vez
- Cada paso que pides tiene que tener una razón de negocio clara — si no la tiene, elimínalo
- El onboarding no es un tutorial del producto: es el camino más corto al primer valor real
- Empty states son parte del onboarding — deben guiar, no frustrar

### Tipos de onboarding según el producto
**Checklist progresiva** (para SaaS complejos con setup inicial largo)
→ El usuario ve el progreso claramente. Cada check libera valor incremental.
→ Referentes: Linear, Notion, Intercom

**Onboarding wizard** (cuando hay configuración obligatoria antes de poder usar el producto)
→ Flujo guiado paso a paso. Máximo 5 pasos. Progress indicator visible siempre.
→ Cuándo usar: cuando sin esa configuración el producto literalmente no funciona
→ Referentes: Stripe Atlas, Vercel project setup, Clerk dashboard setup

**Plantilla / sample data** (para productos donde el usuario entiende el valor viéndolo en acción)
→ El sistema crea datos de ejemplo para que el usuario vea el producto "lleno" y entienda qué puede hacer
→ Cuándo usar: dashboards, CRMs, herramientas de analytics
→ Referentes: Figma (con archivos de ejemplo), Airtable (con bases de ejemplo), Webflow

**Empty state que enseña** (para productos simples donde la primera acción ES el onboarding)
→ Un empty state bien diseñado con la CTA correcta y un ejemplo de cómo se ve cuando hay datos
→ Cuándo usar: herramientas de lista, gestores de tareas, repositorios
→ Referentes: GitHub (nuevo repo), Linear (nuevo proyecto), Raycast

### Para el SaaS específico, definir:
1. ¿Cuál es el "aha moment"? (la acción o vista donde el usuario entiende el valor real)
2. ¿Cuántos pasos separan el registro de ese momento? (mínimo posible)
3. ¿Qué tipo de onboarding aplica?
4. ¿Cuáles son los empty states más críticos y qué deben comunicar?
5. ¿Hay un producto tour (tooltips guiados)? ¿Cuándo activarlo?

---

## Paso 6 — Componentes clave con decisiones de diseño

Para los componentes más importantes del SaaS específico, definir:
- Anatomía visual del componente (qué elementos lo componen)
- Estados: default, hover, focus, disabled, loading, error, success
- Decisiones no obvias de diseño (ej: ¿el badge de estado va a la izquierda o derecha del nombre?)
- Patrones de datos vacíos, cargando y con error para ese componente

Siempre incluir decisiones para:
- **La tabla/lista principal** del recurso central del producto
- **El formulario de creación** del recurso principal
- **El dashboard** o vista home del usuario
- **Los estados de carga** (skeleton screens, no spinners genéricos)
- **Los estados vacíos** (zero states con ilustración o tipografía, no solo texto gris)
- **Las notificaciones y alerts** inline vs toast vs modal

---

## Paso 7 — Lo que NO hacer (específico para este proyecto)

Al final, siempre incluir una sección de anti-patrones específicos para este producto:
- Los errores de diseño más frecuentes en SaaS de este tipo
- Las decisiones de diseño que parecen seguras pero hacen que se vea genérico
- Los componentes de shadcn/ui que se usan sin customizar y quedan con aspecto de template

Ver `references/anti-patterns.md` para la lista completa de anti-patrones.

---

## Output que siempre entregas

1. **Dirección de diseño declarada** — nombre + descripción + justificación
2. **Referencias reales** — 5–8 productos/sitios con URL y qué inspira de cada uno
3. **Design system base** — tokens completos (tipografía, colores, espaciado, radios, sombras)
4. **Arquitectura de información** — navegación + mapa de páginas + patrones de layout
5. **Flujo de onboarding** — tipo, pasos, "aha moment" y empty states clave
6. **Decisiones de componentes clave** — los más importantes para este producto
7. **Anti-patrones a evitar** — específicos para este dominio y este stack

---

## Referencias

- `references/style-directions.md` — 8 direcciones de diseño con referencias reales de cada una
- `references/layout-patterns.md` — patrones de layout para dashboards, listas, detalles y forms
- `references/anti-patterns.md` — lo que hace que un SaaS se vea genérico o "hecho con IA"
