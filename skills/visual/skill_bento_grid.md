---
name: visual-bento-grid
trigger_keywords: [bento, bento grid, widget, dashboard, mosaic, apple grid, card grid, modular layout]
description: >
  Organización modular en celdas rectangulares de distintos tamaños, inspirada en
  las cajas bento japonesas y los widgets de Apple. Cada celda tiene un rol único
  y puede contener texto, imagen, animación o dato. Ideal para features sections,
  dashboards, portfolios y landing pages de SaaS que quieren comunicar mucho
  sin abrumar.
---

# Bento Grid UI — Layout Modular

## Concepto Visual
Una cuadrícula donde las cards tienen tamaños diferentes (1x1, 2x1, 1x2, 2x2)
que juntas forman una composición visual equilibrada. Cada card comunica una
feature o dato con jerarquía clara.

## Grid Base (CSS Grid)
```css
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: auto;
  gap: 16px;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

/* Tamaños de celdas */
.bento-sm   { grid-column: span 1; grid-row: span 1; }
.bento-md   { grid-column: span 2; grid-row: span 1; }
.bento-tall { grid-column: span 1; grid-row: span 2; }
.bento-wide { grid-column: span 3; grid-row: span 1; }
.bento-lg   { grid-column: span 2; grid-row: span 2; }
.bento-hero { grid-column: span 4; grid-row: span 1; }

/* Responsive: colapsa a 2 columnas en tablet */
@media (max-width: 768px) {
  .bento-grid { grid-template-columns: repeat(2, 1fr); }
  .bento-wide, .bento-hero { grid-column: span 2; }
  .bento-lg { grid-column: span 2; }
}
/* Mobile: 1 columna */
@media (max-width: 480px) {
  .bento-grid { grid-template-columns: 1fr; }
  [class*="bento-"] { grid-column: span 1; grid-row: span 1; }
}
```

## Card Base Bento (Dark Premium)
```css
.bento-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 24px;
  overflow: hidden;
  position: relative;
  transition: transform 0.3s ease, border-color 0.3s ease;
  min-height: 160px;
}
.bento-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.16);
}

/* Gradiente de acento en el hover */
.bento-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(600px circle at var(--mouse-x) var(--mouse-y),
    rgba(79, 142, 247, 0.06) 0%, transparent 40%);
  opacity: 0;
  transition: opacity 0.3s;
}
.bento-card:hover::before { opacity: 1; }
```

## Tailwind — Clases de Bento
```jsx
// Grid container
<div className="grid grid-cols-4 gap-4 p-6 max-w-6xl mx-auto">

  {/* Card hero — ocupa 2 columnas, 2 filas */}
  <div className="col-span-2 row-span-2 rounded-2xl bg-white/4 border border-white/8 p-6">
    {/* Contenido principal */}
  </div>

  {/* Card stat — 1x1 */}
  <div className="col-span-1 row-span-1 rounded-2xl bg-white/4 border border-white/8 p-4">
    <p className="text-4xl font-black">98%</p>
    <p className="text-sm text-gray-400">Satisfacción</p>
  </div>

  {/* Card wide — 3 columnas */}
  <div className="col-span-3 rounded-2xl bg-white/4 border border-white/8 p-6">
    {/* Feature destacada */}
  </div>

</div>
```

## Patterns Internos de Cards

### Card de Estadística
```css
.bento-stat-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.bento-stat-number {
  font-size: 3rem;
  font-weight: 900;
  letter-spacing: -0.04em;
  line-height: 1;
  background: linear-gradient(135deg, #fff 0%, #888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Card con Imagen de Fondo
```css
.bento-img-card {
  background-image: url('...');
  background-size: cover;
  background-position: center;
  position: relative;
}
.bento-img-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 60%);
  border-radius: inherit;
}
```

### Card con Animación (code preview, demo)
```css
.bento-demo-card {
  overflow: hidden;
  cursor: pointer;
}
.bento-demo-card .demo-content {
  transform: scale(0.85);
  transform-origin: top left;
  pointer-events: none;
  transition: transform 0.4s ease;
}
.bento-demo-card:hover .demo-content {
  transform: scale(0.82) translateY(-4px);
}
```

## Composición Recomendada para Features Section
```
┌──────────────┬───────┬───────┐
│              │  SM   │  SM   │
│  LG (2x2)   ├───────┴───────┤
│  (Demo/Hero) │  WIDE (2x1)  │
├──────┬───────┴───────────────┤
│  SM  │       WIDE (3x1)     │
└──────┴───────────────────────┘
```

## Reglas de Uso
- Máximo 4 columnas en desktop, 2 en tablet, 1 en mobile.
- Cada card debe tener UN propósito visual claro (dato, feature, demo, CTA).
- Variar los tamaños: una cuadrícula de todos 1x1 se vuelve aburrida.
- La card más grande (2x2 o hero) debe tener el contenido más importante.
- Gap uniforme: 12px mínimo, 20px máximo. El espacio en blanco es parte del diseño.
- Agregar hover con traslación sutil (-2px) para dar profundidad al conjunto.
