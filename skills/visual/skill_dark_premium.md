---
name: visual-dark-premium
trigger_keywords: [dark premium, dark luxury, dark mode, minimalismo oscuro, dark saas, premium dark, elite dark]
description: >
  El estándar oro de interfaces oscuras modernas. Negro profundo con contrastes
  sutiles de gris, líneas finas de luz, tipografía jerarquizada y acentos de
  color contenidos. Ningún elemento compite por atención — la jerarquía lo es todo.
  Estilo dominante en SaaS premium, herramientas dev, fintech y cualquier producto
  B2B que quiera proyectar autoridad y confianza.
---

# Minimalismo Oscuro / Dark Mode Premium

## Concepto Visual
"Todo lo que pueda eliminarse, se elimina." Los colores son herramientas de
jerarquía, no decoración. El espacio en blanco (negro, aquí) es protagonista.
Cada píxel de color tiene un motivo.

## Sistema de Color Completo
```css
:root {
  /* Fondos — de más oscuro a menos oscuro */
  --bg-base:       #050507;   /* El negro base */
  --bg-surface:    #0c0c10;   /* Superficie elevada */
  --bg-elevated:   #121218;   /* Cards, modales */
  --bg-subtle:     #18181f;   /* Hover states, sidebars */
  --bg-overlay:    #1e1e28;   /* Dropdowns, tooltips */

  /* Bordes — siempre sutiles */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-base:   rgba(255, 255, 255, 0.10);
  --border-strong: rgba(255, 255, 255, 0.18);

  /* Texto — escala de 5 niveles */
  --text-primary:   #f2f2f7;  /* Títulos, texto principal */
  --text-secondary: #aeaebb;  /* Subtítulos, labels */
  --text-tertiary:  #72728a;  /* Placeholders, hints */
  --text-disabled:  #44445a;  /* Elementos deshabilitados */
  --text-inverse:   #050507;  /* Texto sobre fondo claro */

  /* Acentos — usar con moderación */
  --accent-primary: #6366f1;      /* Indigo — acciones primarias */
  --accent-hover:   #818cf8;      /* Hover del accent */
  --accent-subtle:  rgba(99, 102, 241, 0.12); /* Backgrounds de accent */
  --accent-border:  rgba(99, 102, 241, 0.3);  /* Bordes de accent */

  /* Estados semánticos */
  --success:   #34d399;
  --warning:   #fbbf24;
  --error:     #f87171;
  --info:      #60a5fa;
  --success-bg: rgba(52, 211, 153, 0.08);
  --error-bg:   rgba(248, 113, 113, 0.08);
}
```

## Tipografía — La Jerarquía lo es Todo
```css
/* Display — impacto máximo */
.text-display {
  font-size: clamp(2.5rem, 5vw, 4.5rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}

/* Heading 1 */
.text-h1 {
  font-size: clamp(1.8rem, 3vw, 2.75rem);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

/* Subtítulos y descripciones */
.text-body-lg {
  font-size: 1.125rem;
  font-weight: 400;
  line-height: 1.7;
  color: var(--text-secondary);
}

/* Labels y metadata */
.text-caption {
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}
```

## Card Premium
```css
.card-premium {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 28px;
  transition: border-color 0.2s ease, background 0.2s ease;
}
.card-premium:hover {
  border-color: var(--border-base);
  background: var(--bg-subtle);
}

/* Card con highlight superior (muy sutil) */
.card-premium-glow {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  position: relative;
}
.card-premium-glow::before {
  content: '';
  position: absolute;
  top: 0; left: 20%; right: 20%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  opacity: 0.6;
}
```

## Botón Primario Dark Premium
```css
.btn-primary {
  background: var(--accent-primary);
  color: white;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 10px 24px;
  font-weight: 600;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  box-shadow: 0 0 0 0 rgba(99, 102, 241, 0);
}
.btn-primary:hover {
  background: var(--accent-hover);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--accent-subtle);
  color: var(--accent-hover);
  border: 1px solid var(--accent-border);
  border-radius: 10px;
  padding: 10px 24px;
  font-weight: 600;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-base);
  border-radius: 10px;
  padding: 10px 24px;
}
.btn-ghost:hover {
  color: var(--text-primary);
  border-color: var(--border-strong);
  background: var(--bg-subtle);
}
```

## Navbar Dark Premium
```css
.navbar-dark {
  position: sticky;
  top: 0;
  background: rgba(5, 5, 7, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 32px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 100;
}
```

## Input Dark Premium
```css
.input-dark {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 10px 14px;
  color: var(--text-primary);
  font-size: 0.9rem;
  width: 100%;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-dark::placeholder {
  color: var(--text-disabled);
}
.input-dark:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}
.input-dark:hover:not(:focus) {
  border-color: var(--border-base);
}
```

## Sidebar Dark
```css
.sidebar-dark {
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  width: 240px;
  height: 100vh;
  padding: 20px 12px;
}
.sidebar-item {
  padding: 8px 12px;
  border-radius: 8px;
  color: var(--text-secondary);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.sidebar-item:hover {
  background: var(--bg-subtle);
  color: var(--text-primary);
}
.sidebar-item.active {
  background: var(--accent-subtle);
  color: var(--accent-hover);
}
```

## Reglas de Uso
- NUNCA usar negro puro (#000000) — usar #050507 o similar. El negro puro fatiga.
- El accent color (indigo, azul, etc.) en máximo 5% de la superficie total.
- Escala de grises: mínimo 5 niveles. Sin escala → interfaz plana sin depth.
- Separadores: usar `border` 1px con baja opacidad, nunca `<hr>` visible.
- Hover states: siempre incrementar levemente el brillo del fondo (+05 de opacidad).
- Iconos: color `var(--text-tertiary)` en estado normal, `var(--text-primary)` en activo.
