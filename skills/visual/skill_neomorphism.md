---
name: visual-neomorphism
trigger_keywords: [neomorphism, neumorphism, relieve, extruded, soft ui, 3d suave]
description: >
  Efecto de relieve suave tridimensional. Los elementos parecen empujados hacia adentro
  (pressed/inset) o hacia afuera (raised) del fondo. Requiere fondo de un solo color
  neutro. Popular en apps de música, fintech y wellness. Combinar con glassmorphism
  para interfaces híbridas modernas.
---

# Neomorphism / Neumorphism — Relieve Esculpido

## Concepto Visual
El truco: dos box-shadows opuestos — uno claro (arriba-izquierda) y uno oscuro (abajo-derecha)
sobre un fondo del MISMO COLOR que el elemento. Crea la ilusión de relieve sin gradiente.

## Paleta Base (Modo Oscuro)
```css
--neo-bg:        #1e1e2e;
--neo-shadow-dark:  rgba(0, 0, 0, 0.5);
--neo-shadow-light: rgba(255, 255, 255, 0.05);
--neo-accent:    #7c85f5;
--text-primary:  #cdd6f4;
--text-muted:    #6c7086;
```

## Paleta Base (Modo Claro)
```css
--neo-bg:        #e8ecf0;
--neo-shadow-dark:  rgba(163, 177, 198, 0.8);
--neo-shadow-light: rgba(255, 255, 255, 0.9);
--neo-accent:    #5e81f4;
--text-primary:  #2d3561;
```

## Elemento Raised (sobresale)
```css
.neo-raised {
  background: var(--neo-bg);
  border-radius: 16px;
  box-shadow:
    6px 6px 14px var(--neo-shadow-dark),
    -6px -6px 14px var(--neo-shadow-light);
}
```

## Elemento Pressed (hundido — estado activo)
```css
.neo-pressed {
  background: var(--neo-bg);
  border-radius: 16px;
  box-shadow:
    inset 4px 4px 10px var(--neo-shadow-dark),
    inset -4px -4px 10px var(--neo-shadow-light);
}
```

## Botón Toggle Neomórfico
```css
.neo-toggle {
  width: 56px; height: 28px;
  background: var(--neo-bg);
  border-radius: 14px;
  box-shadow:
    inset 3px 3px 8px var(--neo-shadow-dark),
    inset -3px -3px 8px var(--neo-shadow-light);
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}
.neo-toggle.active {
  box-shadow:
    inset 3px 3px 8px var(--neo-shadow-dark),
    inset -3px -3px 8px var(--neo-shadow-light),
    0 0 12px var(--neo-accent);
}
.neo-toggle::after {
  content: '';
  position: absolute;
  top: 4px; left: 4px;
  width: 20px; height: 20px;
  background: var(--neo-bg);
  border-radius: 50%;
  box-shadow: 2px 2px 5px var(--neo-shadow-dark), -2px -2px 5px var(--neo-shadow-light);
  transition: transform 0.3s ease;
}
.neo-toggle.active::after {
  transform: translateX(28px);
  background: var(--neo-accent);
}
```

## Input Neomórfico
```css
.neo-input {
  background: var(--neo-bg);
  border: none;
  border-radius: 12px;
  padding: 14px 20px;
  color: var(--text-primary);
  box-shadow:
    inset 3px 3px 8px var(--neo-shadow-dark),
    inset -3px -3px 8px var(--neo-shadow-light);
  outline: none;
  transition: box-shadow 0.2s ease;
}
.neo-input:focus {
  box-shadow:
    inset 3px 3px 8px var(--neo-shadow-dark),
    inset -3px -3px 8px var(--neo-shadow-light),
    0 0 0 2px var(--neo-accent);
}
```

## Reglas de Uso
- El fondo del elemento y del contenedor DEBEN ser el mismo color. Si difieren, el efecto se rompe.
- No usar sombras muy agresivas (>20px offset): se ve artificial.
- Ideal para controles interactivos: botones, sliders, toggles, knobs.
- Evitar en texto largo o contenido de lectura — dificulta la legibilidad.
- Siempre agregar estado `:active` con la versión `inset` para feedback táctil.
