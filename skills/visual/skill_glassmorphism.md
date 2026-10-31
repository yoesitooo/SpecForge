# Skill: Glassmorphism — Design System Premium
triggers: glassmorphism, glass, vidrio, frosted, blur card

## Variables CSS (Tailwind v4 — en globals.css)

```css
@theme {
  --color-glass-bg: rgba(255, 255, 255, 0.04);
  --color-glass-border: rgba(255, 255, 255, 0.08);
  --color-glass-border-hover: rgba(255, 255, 255, 0.16);
  --color-glow-primary: rgba(108, 99, 255, 0.35);
  --color-glow-accent: rgba(201, 168, 76, 0.35);
}
```

## Componentes React/Tailwind

### Glass Card base
```tsx
// CORRECTO para Tailwind v4
<div className="rounded-2xl bg-white/4 backdrop-blur-xl border border-white/8
                shadow-[0_8px_32px_rgba(0,0,0,0.4)]
                hover:border-white/16 hover:-translate-y-0.5
                transition-all duration-300">
  {children}
</div>
```

### Glass Card con glow de marca
```tsx
<div className="relative rounded-2xl bg-white/4 backdrop-blur-xl border border-white/8
                before:absolute before:inset-0 before:rounded-2xl
                before:bg-gradient-to-br before:from-brand/10 before:to-transparent before:opacity-0
                hover:before:opacity-100 before:transition-opacity before:duration-300">
```

### Glass Nav / Header
```tsx
<header className="sticky top-0 z-50 border-b border-white/8
                   bg-[#0A0A0F]/70 backdrop-blur-xl backdrop-saturate-150">
```

### Glass Modal / Dialog
```tsx
// overlay
<div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
// panel
<div className="rounded-3xl bg-[#13131A]/90 backdrop-blur-2xl border border-white/12
                shadow-[0_24px_64px_rgba(0,0,0,0.6)]">
```

## Glow Effects

```tsx
// Botón con glow pulsante
<button className="relative px-6 py-3 rounded-xl
                   bg-gradient-to-r from-violet-600 to-violet-500
                   shadow-[0_0_20px_rgba(108,99,255,0.4)]
                   hover:shadow-[0_0_35px_rgba(108,99,255,0.65)]
                   active:scale-95 transition-all duration-200">

// Card con glow en hover
<div className="hover:shadow-[0_0_40px_rgba(108,99,255,0.2)] transition-shadow duration-500">
```

## Tipografía Glassmorphism

```tsx
// Títulos — Outfit (fuerte, moderno)
// Cuerpo — Inter (legibilidad óptima en dark)
// Mono — JetBrains Mono

// En Next.js — next/font/google
import { Outfit, Inter } from 'next/font/google'
const outfit = Outfit({ subsets: ['latin'], variable: '--font-display' })
const inter = Inter({ subsets: ['latin'], variable: '--font-body' })
```

## Micro-animaciones

```tsx
// Con Framer Motion 11 (import de motion/react)
const cardVariants = {
  rest: { y: 0, boxShadow: "0 8px 32px rgba(0,0,0,0.4)" },
  hover: { y: -6, boxShadow: "0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(108,99,255,0.2)" }
}

<motion.div variants={cardVariants} initial="rest" whileHover="hover" transition={{ duration: 0.3, ease: "easeOut" }}>
```
