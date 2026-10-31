---
name: visual-claymorphism
trigger_keywords: [claymorphism, clay, arcilla, inflable, 3d, bubbly, cartoon 3d, friendly]
description: >
  Objetos que parecen hechos de arcilla suave o inflables 3D. Bordes muy redondeados,
  colores vibrantes, sombras coloreadas en lugar de grises, y efecto de profundidad
  sin perspectiva dura. Tendencia en apps de productividad, onboarding, educación
  y cualquier producto que quiera sentirse accesible y moderno.
---

# Claymorphism — Arcilla Digital

## Concepto Visual
La clave es la sombra coloreada (misma tonalidad del objeto pero más oscura/saturada)
y el `border-radius` muy generoso (24px+). Los elementos parecen "inflados" hacia el usuario.

## Paleta Base
```css
/* Fondo limpio para que el clay destaque */
--clay-bg:       #f0f4ff;
--clay-bg-dark:  #1a1a2e;

/* Objetos clay — colores vibrantes y pasteles */
--clay-purple:   #7c6af7;
--clay-pink:     #f472b6;
--clay-blue:     #38bdf8;
--clay-green:    #34d399;
--clay-orange:   #fb923c;
--clay-yellow:   #fbbf24;

/* Sombras clay (misma tonalidad, oscurecida) */
--shadow-purple: rgba(124, 106, 247, 0.5);
--shadow-pink:   rgba(244, 114, 182, 0.5);
--shadow-blue:   rgba(56, 189, 248, 0.5);
```

## Card Clay Base
```css
.clay-card {
  background: #ffffff;
  border-radius: 28px;
  padding: 28px;
  box-shadow:
    0 8px 0 rgba(0, 0, 0, 0.12),          /* sombra inferior "aplastada" */
    0 20px 40px rgba(0, 0, 0, 0.08);       /* sombra de profundidad */
  border: 2px solid rgba(255, 255, 255, 0.8);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.clay-card:hover {
  transform: translateY(-4px);
  box-shadow:
    0 12px 0 rgba(0, 0, 0, 0.12),
    0 28px 48px rgba(0, 0, 0, 0.1);
}
```

## Botón Clay Coloreado
```css
.clay-btn {
  background: var(--clay-purple);
  border-radius: 16px;
  padding: 14px 32px;
  color: white;
  font-weight: 700;
  border: none;
  /* La sombra "abajo" del mismo color = efecto 3D inflado */
  box-shadow:
    0 6px 0 rgba(100, 80, 200, 0.7),
    0 12px 20px rgba(124, 106, 247, 0.35);
  transition: all 0.15s ease;
  cursor: pointer;
}
.clay-btn:active {
  transform: translateY(4px);
  box-shadow:
    0 2px 0 rgba(100, 80, 200, 0.7),
    0 6px 10px rgba(124, 106, 247, 0.3);
}
```

## Ícono Clay (elemento flotante)
```css
.clay-icon-wrap {
  width: 64px; height: 64px;
  border-radius: 20px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(145deg, var(--clay-blue), #0ea5e9);
  box-shadow:
    0 6px 0 var(--shadow-blue),
    0 12px 24px rgba(56, 189, 248, 0.3),
    inset 0 1px 2px rgba(255, 255, 255, 0.5);
}
```

## Avatar Clay
```css
.clay-avatar {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #a78bfa, #7c6af7);
  box-shadow:
    0 5px 0 rgba(100, 80, 200, 0.6),
    0 10px 20px rgba(124, 106, 247, 0.3);
  border: 3px solid rgba(255,255,255,0.9);
}
```

## Modo Oscuro Clay
```css
/* En dark mode, el clay usa tonos más vibrantes y sombras más profundas */
.dark .clay-card {
  background: #2d2d44;
  box-shadow:
    0 8px 0 rgba(0, 0, 0, 0.4),
    0 20px 40px rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.06);
}
```

## Reglas de Uso
- SIEMPRE usar sombra coloreada (del mismo tono del elemento), nunca gris puro.
- `border-radius` mínimo: 20px en cards, 14px en botones. Más = más clay.
- Combinar con iconos 3D (Spline, Three.js, o emojis grandes) para máximo impacto.
- Ideal en fondo blanco o muy claro. Sobre oscuro, usar versión vibrant-dark.
- Evitar en interfaces corporativas serias — mejor para B2C, educación, wellness.
