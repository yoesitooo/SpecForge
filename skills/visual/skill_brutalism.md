---
name: visual-brutalism
trigger_keywords: [brutalism, brutalismo, neo brutal, bold, raw, crudo, sombra plana, flat shadow]
description: >
  Estética digital cruda y directa. Bordes gruesos negros, sombras planas desplazadas,
  tipografía bold masiva, colores primarios puros o pasteles fuertes. Sin sutilezas
  ni glassmorphism. Popular en startups que quieren diferenciarse, portfolios de diseñadores,
  y productos que valoran la autenticidad sobre la "perfección" pulida.
---

# Brutalismo Digital / Neo-Brutalisme

## Concepto Visual
La anti-estética del glassmorphism. Todo lo que el diseño "sofisticado" evita:
bordes duros, colores chillones, sombras que parecen dibujadas a mano, asimetría intencional.
La "imperfección" ES el diseño.

## Paleta Neo-Brutal
```css
/* Fondos */
--brutal-bg:     #f5f0e8;  /* Crema de papel */
--brutal-bg-alt: #ffffff;
--brutal-black:  #0a0a0a;

/* Colores primarios puros */
--brutal-yellow:  #ffe500;
--brutal-red:     #ff3131;
--brutal-blue:    #3b5bdb;
--brutal-green:   #00cc88;
--brutal-pink:    #ff6ec7;
--brutal-orange:  #ff6b00;

/* La sombra siempre es negro sólido */
--brutal-shadow: #0a0a0a;
```

## Card Brutalista
```css
.brutal-card {
  background: #ffffff;
  border: 3px solid var(--brutal-black);
  border-radius: 0;                          /* SIN border-radius */
  padding: 24px;
  /* La sombra desplazada es la firma del brutalismo */
  box-shadow: 6px 6px 0 var(--brutal-black);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.brutal-card:hover {
  transform: translate(-3px, -3px);
  box-shadow: 9px 9px 0 var(--brutal-black);
}
.brutal-card:active {
  transform: translate(3px, 3px);
  box-shadow: 3px 3px 0 var(--brutal-black);
}
```

## Botón Neo-Brutal
```css
.brutal-btn {
  background: var(--brutal-yellow);
  color: var(--brutal-black);
  border: 3px solid var(--brutal-black);
  border-radius: 0;
  padding: 12px 28px;
  font-weight: 900;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 4px 4px 0 var(--brutal-black);
  cursor: pointer;
  transition: all 0.1s ease;
}
.brutal-btn:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 var(--brutal-black);
}
.brutal-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 var(--brutal-black);
}

/* Variantes de color */
.brutal-btn-red    { background: var(--brutal-red); color: white; }
.brutal-btn-blue   { background: var(--brutal-blue); color: white; }
.brutal-btn-outline {
  background: transparent;
  color: var(--brutal-black);
  box-shadow: 4px 4px 0 var(--brutal-black);
}
```

## Input Brutalista
```css
.brutal-input {
  background: white;
  border: 3px solid var(--brutal-black);
  border-radius: 0;
  padding: 12px 16px;
  font-weight: 600;
  width: 100%;
  outline: none;
  box-shadow: 4px 4px 0 var(--brutal-black);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.brutal-input:focus {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 var(--brutal-black);
}
```

## Badge / Tag
```css
.brutal-badge {
  display: inline-flex;
  background: var(--brutal-yellow);
  border: 2px solid var(--brutal-black);
  padding: 4px 12px;
  font-weight: 800;
  font-size: 0.75rem;
  text-transform: uppercase;
  box-shadow: 2px 2px 0 var(--brutal-black);
}
```

## Navbar Brutalista
```css
.brutal-nav {
  background: var(--brutal-yellow);
  border-bottom: 4px solid var(--brutal-black);
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brutal-nav-logo {
  font-size: 1.5rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}
```

## Tipografía
```css
/* Fuentes para brutalismo — grosor extremo */
font-family: 'Space Grotesk', 'DM Sans', 'Archivo Black', sans-serif;

/* Títulos: masivos y aplastados */
.brutal-title {
  font-size: clamp(3rem, 8vw, 8rem);
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -0.04em;
  text-transform: uppercase;
}
```

## Reglas de Uso
- CERO border-radius, CERO gradientes, CERO blur. Si hay alguno, ya no es brutalismo.
- La sombra desplazada SIEMPRE es negra sólida. La offset entre 4px y 8px.
- Colores: primarios puros o crema/blanco roto. Nada de pasteles lavados.
- El hover SIEMPRE mueve el elemento + extiende la sombra (o viceversa).
- Tipografía: la más bold disponible. Títulos deben ocupar espacio.
- Combina bien con ilustraciones flat, íconos outline gruesos y fotografía en B&N.
