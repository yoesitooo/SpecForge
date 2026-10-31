---
name: visual-cyberpunk
trigger_keywords: [cyberpunk, synthwave, neon, retro futurista, terminal, glitch, hacker, neon noir]
description: >
  Estética retro-futurista inspirada en Blade Runner, Tron y la cultura hacker.
  Neones brillantes (cyan, magenta, verde terminal) sobre negro profundo.
  Efectos de glitch, scanlines, text-shadow glow. Ideal para herramientas de dev,
  plataformas de gaming, ciberseguridad y productos tech-forward.
---

# Cyberpunk / Synthwave UI — Neón y Terminal

## Concepto Visual
Negro casi puro como base. Neones brillantes como acentos que "brillan" hacia afuera
con múltiples capas de text-shadow y box-shadow. Grid lines o scanlines sutiles en el fondo.

## Paleta Cyberpunk
```css
--cyber-bg:        #050508;
--cyber-surface:   #0d0d14;
--cyber-surface-2: #13131e;

/* Neones primarios */
--neon-cyan:    #00f5ff;
--neon-magenta: #ff00aa;
--neon-green:   #39ff14;
--neon-yellow:  #ffe600;
--neon-purple:  #bf00ff;

/* Glow colors (para box-shadow) */
--glow-cyan:    rgba(0, 245, 255, 0.4);
--glow-magenta: rgba(255, 0, 170, 0.4);
--glow-green:   rgba(57, 255, 20, 0.4);

--text-primary: #e0e0ff;
--text-code:    #00f5ff;
--border-cyber: rgba(0, 245, 255, 0.2);
```

## Texto Neon Glow
```css
.neon-text-cyan {
  color: var(--neon-cyan);
  text-shadow:
    0 0 7px var(--neon-cyan),
    0 0 14px var(--neon-cyan),
    0 0 30px rgba(0, 245, 255, 0.5),
    0 0 60px rgba(0, 245, 255, 0.2);
}

.neon-text-magenta {
  color: var(--neon-magenta);
  text-shadow:
    0 0 7px var(--neon-magenta),
    0 0 14px var(--neon-magenta),
    0 0 30px rgba(255, 0, 170, 0.5);
}

/* Efecto flicker (parpadeo de neón roto) */
.neon-flicker {
  animation: flicker 3s infinite alternate;
}
@keyframes flicker {
  0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
    text-shadow: 0 0 7px var(--neon-cyan), 0 0 20px var(--neon-cyan);
  }
  20%, 24%, 55% {
    text-shadow: none;
    opacity: 0.8;
  }
}
```

## Card Cyberpunk
```css
.cyber-card {
  background: var(--cyber-surface);
  border: 1px solid var(--border-cyber);
  border-radius: 4px;  /* Anguloso — no rounded en cyberpunk */
  position: relative;
  overflow: hidden;
  box-shadow:
    0 0 20px rgba(0, 245, 255, 0.1),
    inset 0 0 20px rgba(0, 245, 255, 0.02);
}

/* Línea superior de acento (el "HUD line") */
.cyber-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
}

/* Corner brackets en esquinas (estética HUD) */
.cyber-card::after {
  content: '';
  position: absolute;
  top: 6px; right: 6px;
  width: 12px; height: 12px;
  border-top: 2px solid var(--neon-cyan);
  border-right: 2px solid var(--neon-cyan);
}
```

## Botón Cyberpunk
```css
.cyber-btn {
  background: transparent;
  border: 1px solid var(--neon-cyan);
  color: var(--neon-cyan);
  padding: 10px 28px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  position: relative;
  clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px));
  transition: all 0.2s ease;
}
.cyber-btn:hover {
  background: rgba(0, 245, 255, 0.1);
  box-shadow: 0 0 20px var(--glow-cyan), inset 0 0 10px rgba(0,245,255,0.1);
  text-shadow: 0 0 8px var(--neon-cyan);
}
```

## Fondo con Grid Lines (CRT/Tron)
```css
.cyber-grid-bg {
  background-color: var(--cyber-bg);
  background-image:
    linear-gradient(rgba(0, 245, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 245, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* Scanlines overlay */
.cyber-scanlines::after {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
  pointer-events: none;
  z-index: 9999;
}
```

## Efecto Glitch en Texto
```css
.glitch {
  position: relative;
  color: var(--text-primary);
}
.glitch::before, .glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
}
.glitch::before {
  color: var(--neon-cyan);
  animation: glitch-1 2s infinite linear alternate;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
  transform: translateX(-2px);
}
.glitch::after {
  color: var(--neon-magenta);
  animation: glitch-2 2s infinite linear alternate;
  clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
  transform: translateX(2px);
}
@keyframes glitch-1 {
  0%, 90% { transform: translateX(-2px); opacity: 1; }
  95%      { transform: translateX(2px); opacity: 0.8; }
  100%     { transform: translateX(-2px); }
}
@keyframes glitch-2 {
  0%, 90% { transform: translateX(2px); opacity: 1; }
  95%      { transform: translateX(-3px); opacity: 0.8; }
  100%     { transform: translateX(2px); }
}
```

## Tipografía
```css
/* Monospace para datos y código */
font-family: 'JetBrains Mono', 'Fira Code', 'Share Tech Mono', monospace;
/* Display para títulos */
font-family: 'Orbitron', 'Rajdhani', 'Exo 2', sans-serif;
```

## Reglas de Uso
- Usar bordes angulosos (border-radius 0-4px) para el look HUD/terminal.
- `clip-path: polygon` con esquinas cortadas refuerza la estética futurista.
- Neon glow en texto: máximo 2-3 elementos por pantalla, o se fatiga la vista.
- Fuentes monospace para cualquier dato técnico, número o código.
- Usar con moderación en SaaS — es muy temático. Perfecto para cybersecurity, gaming, dev tools.
