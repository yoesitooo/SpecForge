---
name: visual-aurora-ui
trigger_keywords: [aurora, gradient fluid, organic gradient, borealis, difuminado, blob, mesh gradient]
description: >
  Fondos fluidos con degradados orgánicos tipo aurora boreal. Blobs de color
  difuminados que se mueven lentamente o están fijos como fondo. Combinación
  de 3-4 colores saturados difuminados sobre fondo oscuro. Ultra moderno en
  SaaS landing pages, portfolios creativos y apps de AI/tech.
---

# Aurora UI — Gradientes Orgánicos Fluidos

## Concepto Visual
Blobs de color (círculos con blur extremo) que se superponen para crear una
"aurora" o "mesh gradient" orgánico. El fondo vive, no es estático.

## Paleta Aurora Oscura (Recomendada)
```css
--aurora-bg:     #050508;
--aurora-1:      #3b1f8c;  /* Violeta profundo */
--aurora-2:      #1a3a6e;  /* Azul profundo */
--aurora-3:      #0f5f4f;  /* Verde esmeralda */
--aurora-4:      #6b1a4f;  /* Magenta oscuro */
--text-primary:  #e8e8f0;
--text-glow:     rgba(180, 160, 255, 0.9);
```

## Paleta Aurora Clara (para hero sections)
```css
--aurora-bg:     #f8f0ff;
--aurora-1:      rgba(167, 139, 250, 0.4);  /* Violeta suave */
--aurora-2:      rgba(96, 165, 250, 0.35);  /* Azul cielo */
--aurora-3:      rgba(52, 211, 153, 0.3);   /* Verde menta */
--aurora-4:      rgba(251, 113, 133, 0.25); /* Rosa */
```

## Fondo Aurora — CSS Puro
```css
.aurora-bg {
  position: relative;
  background: var(--aurora-bg);
  overflow: hidden;
}

.aurora-bg::before,
.aurora-bg::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: aurora-drift 15s ease-in-out infinite alternate;
}

.aurora-bg::before {
  width: 600px; height: 600px;
  top: -200px; left: -100px;
  background: radial-gradient(circle, var(--aurora-1) 0%, transparent 70%);
}

.aurora-bg::after {
  width: 500px; height: 500px;
  bottom: -150px; right: -50px;
  background: radial-gradient(circle, var(--aurora-3) 0%, transparent 70%);
  animation-delay: -7s;
}

@keyframes aurora-drift {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(40px, -30px) scale(1.1); }
}
```

## Múltiples Blobs (3-4 capas)
```css
/* Usando pseudo-elementos + divs adicionales */
.aurora-blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
  animation: blob-float 20s ease-in-out infinite;
}

.blob-1 {
  width: 700px; height: 700px;
  top: -300px; left: -200px;
  background: radial-gradient(circle, #3b1f8c 0%, transparent 65%);
  opacity: 0.5;
}
.blob-2 {
  width: 500px; height: 500px;
  top: 20%; right: -100px;
  background: radial-gradient(circle, #1a3a6e 0%, transparent 65%);
  opacity: 0.4;
  animation-delay: -5s;
}
.blob-3 {
  width: 400px; height: 400px;
  bottom: -100px; left: 30%;
  background: radial-gradient(circle, #0f5f4f 0%, transparent 65%);
  opacity: 0.35;
  animation-delay: -10s;
}

@keyframes blob-float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33%       { transform: translate(30px, -50px) rotate(120deg); }
  66%       { transform: translate(-20px, 20px) rotate(240deg); }
}
```

## React + Framer Motion (versión animada)
```tsx
import { motion } from 'framer-motion'

const AuroraBackground = () => (
  <div className="relative overflow-hidden bg-[#050508]">
    {[
      { color: '#3b1f8c', delay: 0, x: '-200px', y: '-200px' },
      { color: '#1a3a6e', delay: 5, x: '60%', y: '10%' },
      { color: '#0f5f4f', delay: 10, x: '20%', y: '70%' },
    ].map((blob, i) => (
      <motion.div
        key={i}
        className="absolute w-[500px] h-[500px] rounded-full"
        style={{
          background: `radial-gradient(circle, ${blob.color} 0%, transparent 65%)`,
          filter: 'blur(80px)',
          left: blob.x,
          top: blob.y,
          opacity: 0.5,
        }}
        animate={{
          x: [0, 40, -20, 0],
          y: [0, -30, 20, 0],
          scale: [1, 1.1, 0.95, 1],
        }}
        transition={{
          duration: 20,
          delay: blob.delay,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />
    ))}
    {/* Contenido encima de los blobs */}
    <div className="relative z-10">
      {/* ... */}
    </div>
  </div>
)
```

## Texto con efecto Aurora
```css
.text-aurora {
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

## Reglas de Uso
- Los blobs deben tener `blur` mínimo de 60px. Con menos, se ven como manchas.
- Máximo 4 blobs por sección — más se vuelve ruido visual.
- El contenido (texto, cards) SIEMPRE con `position: relative; z-index: 10`.
- Animar lentamente (15-20s) — movimiento rápido marea al usuario.
- Combinar con glassmorphism en las cards para coherencia estética.
