# Skill: UI/UX Pro Max — Guía Completa 2025
triggers: [ui ux, design system, premium ui, components, layout, typography, accessibility]

## Jerarquía de Decisión Visual

Antes de elegir estilo, clasifica el producto:
- **SaaS B2B / Dev tool** → Dark Premium o Glassmorphism
- **Consumer app / bienestar** → Claymorphism o Aurora UI
- **Fintech / legal / salud** → Dark Premium (sobriedad = confianza)
- **Startup diferencial / agencia** → Neo-Brutalismo o Bento Grid
- **Portfolio creativo / AI product** → Aurora UI o Cyberpunk
- **IoT / control panel** → Neomorphism

## Sistema de Color Semántico (siempre así)

```css
@theme {
  /* Fondos */
  --color-bg-base: #0A0A0F;        /* fondo principal */
  --color-bg-surface: #13131A;     /* cards, panels */
  --color-bg-elevated: #1A1A24;    /* dropdowns, modals */

  /* Texto */
  --color-text-primary: #F0F0F5;
  --color-text-secondary: #A0A0B0;
  --color-text-muted: #5A5A70;

  /* Marca */
  --color-brand: #6C63FF;          /* ajusta al proyecto */
  --color-brand-hover: #8A82FF;
  --color-brand-muted: rgba(108,99,255,0.15);

  /* Estado */
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  --color-info: #3B82F6;

  /* Bordes */
  --color-border: rgba(255,255,255,0.08);
  --color-border-hover: rgba(255,255,255,0.16);
}
```

## Escala Tipográfica (8pt rhythm)

```css
/* Tailwind v4 — en globals.css */
@theme {
  --font-display: 'Outfit', sans-serif;   /* headings */
  --font-body: 'Inter', sans-serif;        /* body text */
  --font-mono: 'JetBrains Mono', monospace;

  --text-xs: 0.75rem;    /* 12px — labels, badges */
  --text-sm: 0.875rem;   /* 14px — body small */
  --text-base: 1rem;     /* 16px — body */
  --text-lg: 1.125rem;   /* 18px — body large */
  --text-xl: 1.25rem;    /* 20px — subheadings */
  --text-2xl: 1.5rem;    /* 24px — section titles */
  --text-3xl: 1.875rem;  /* 30px — page titles */
  --text-4xl: 2.25rem;   /* 36px — hero */
  --text-5xl: 3rem;      /* 48px — display */
}
```

## Componentes Base (con shadcn/ui + Tailwind v4)

### Card glassmorphism
```tsx
export function GlassCard({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn(
      "rounded-2xl border border-white/8 bg-white/4 backdrop-blur-xl",
      "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
      "transition-all duration-300 hover:border-white/16 hover:-translate-y-0.5",
      className
    )}>
      {children}
    </div>
  )
}
```

### Botón primario con gradient
```tsx
export function PrimaryButton({ children, ...props }: ButtonProps) {
  return (
    <Button
      className="bg-gradient-to-r from-brand to-brand-hover text-white
                 shadow-[0_0_20px_rgba(108,99,255,0.4)] hover:shadow-[0_0_30px_rgba(108,99,255,0.6)]
                 transition-all duration-300 active:scale-95"
      {...props}
    >
      {children}
    </Button>
  )
}
```

## Reglas UX Obligatorias

### Feedback visual (<100ms)
- Loading state en TODA acción async (Suspense, skeleton, spinner)
- Toast de éxito/error tras cada mutación (usar sonner)
- Disable de botón mientras se procesa (prevent double submit)

### Accesibilidad mínima no-negociable
- Contraste texto/fondo: mínimo 4.5:1 (AA), idealmente 7:1 (AAA)
- Targets táctiles: mínimo 44×44px
- Focus visible en todos los elementos interactivos (`:focus-visible`)
- alt descriptivo en todas las imágenes (no "imagen" o "foto")
- Formularios con `<label htmlFor>` — NUNCA solo placeholder como label

### Mobile-first breakpoints (Tailwind v4)
```
base  → 0px      (mobile portrait)
sm    → 640px    (mobile landscape / small tablet)
md    → 768px    (tablet)
lg    → 1024px   (laptop)
xl    → 1280px   (desktop)
2xl   → 1536px   (wide desktop)
```

## Animaciones con Framer Motion 11

```tsx
// Import correcto en 2025
import { motion, AnimatePresence } from "motion/react"  // NO "framer-motion"

// Fade + slide up (estándar para page transitions)
const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
}

// Stagger de lista
const container = {
  animate: { transition: { staggerChildren: 0.08 } }
}

// Exit animation con AnimatePresence
<AnimatePresence mode="wait">
  {isOpen && <motion.div key="modal" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />}
</AnimatePresence>
```

## Skeleton Loading (evita layout shift)

```tsx
// Con shadcn/ui Skeleton
import { Skeleton } from "@/components/ui/skeleton"

function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/8 p-6 space-y-3">
      <Skeleton className="h-4 w-3/4 bg-white/8" />
      <Skeleton className="h-4 w-1/2 bg-white/8" />
      <Skeleton className="h-20 w-full bg-white/8" />
    </div>
  )
}
```

## Responsive Layout Patterns

### Bento grid responsive
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-fr">
  <div className="col-span-1 lg:col-span-2 row-span-2">...</div>  {/* hero card */}
  <div className="col-span-1">...</div>
  <div className="col-span-1">...</div>
</div>
```

### Sidebar layout
```tsx
<div className="flex flex-col lg:flex-row min-h-screen">
  <aside className="w-full lg:w-64 lg:shrink-0 border-b lg:border-b-0 lg:border-r border-white/8" />
  <main className="flex-1 overflow-auto p-4 lg:p-8" />
</div>
```
