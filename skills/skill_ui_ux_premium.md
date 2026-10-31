# Skill: Estándar de Oro UI/UX Premium — SDD

Este documento es el estándar innegociable para cualquier interfaz generada por el ecosistema SDD. Se enfoca en Landings de alto impacto y estética "Elite Digital". 

> [!IMPORTANT]
> **Complemento Supremo**: Para decisiones avanzadas de color, tipografía y UX, consulta obligatoriamente `skill_ui_ux_pro_max.md`.

## 💎 1. Estética "Dark Luxury" & "Glassmorphism"
- **Fondo Primario**: `#050505` con un gradiente radial sutil hacia `#121212`.
- **Contenedores Glass**: 
  - `background: rgba(255, 255, 255, 0.03)`
  - `backdrop-filter: blur(12px)`
  - `border: 1px solid rgba(255, 255, 255, 0.08)`
- **Acentos**:
  - **Dorado Elite**: `#d4af37` (Solo para detalles críticos como iconos de confianza o bordes de botones primarios).
  - **Blanco Sedoso**: `#f5f5f7` (Para el texto principal).
  - **Gris Muted**: `#86868b` (Para descripciones secundarias).

## 📐 2. Layouts Modernos (Bento Grid)
- Utilizar estructuras de rejilla irregular (Bento) para secciones de "Características" o "Testimonios".
- **Espaciado**: Margenes generosos (`padding: 4rem` o más en secciones de escritorio). El "aire" es lo que da elegancia.
- **Bordes**: `border-radius: 24px` o `32px` para un look moderno y suave.

## ✍️ 3. Tipografía de Élite
- **Títulos**: Usar `Inter` o `Outfit` con `font-weight: 800` y `letter-spacing: -0.04em`.
- **Cuerpo**: `Inter` con `font-weight: 400` y `line-height: 1.6`.
- **Efectos**: Títulos con gradientes lineales (ej: de `#ffffff` a `#a1a1a1`).

## 🪄 4. Micro-Interacciones (GSAP / CSS)
- **Hover**: Los botones deben escalar sutilmente (`scale: 1.02`) y aumentar el brillo del borde dorado.
- **Scroll**: Las secciones deben aparecer con un "Fade In" suave mientras el usuario baja por la página.
- **CTAs**: Sombras difusas (`drop-shadow`) que coincidan con el color del acento.

## 🚀 5. Libertad Creativa (¡No seas cuadrado!)
- **Innovación Visual**: Tienes TOTAL LIBERTAD para proponer y codificar asimetrías, elementos superpuestos y layouts fluidos. Rompe con los bloques "cuadrados".
- **Inspiración Directa**: Basate en los estándares de sitios como *Figcomponents.com*, *Dark.design*, *Unicornicons.com*, *Dribbble.com* y *Awwwards.com*.
- **Código vs Imágenes**: Si en tu investigación encuentras código libre o plantillas completas de estos sitios, ¡ÚSALAS como base! Si solo encuentras imágenes, extrae la esencia (colores, sombras, layout) y codifica ideas similares desde cero.
- **Decisión Autónoma**: Eres el maestro del diseño. Mientras respetes la idea central del negocio, puedes tomar las decisiones creativas que consideres "lo mejor" visualmente para impresionar al usuario.

## ⚖️ 6. Enfoque Landing Page
- **Hero Section**: Debe ser monumental. Un título potente, un subtítulo corto y un CTA (Botón) que brille sutilmente.
- **Social Proof**: Logos en escala de grises con opacidad al 50%, que se iluminen al pasar el mouse.
- **Fricción Cero**: Formularios minimalistas con inputs tipo "Glass".

**ESTÁNDAR TÉCNICO**: El uso de **Tailwind CSS** es obligatorio para todo el estilizado. Se permite el uso de librerías modernas como `shadcn/ui`, `Framer Motion` y `GSAP`.

**PROHIBICIÓN ABSOLUTA**: 
- Prohibido usar **Bootstrap**. Se considera tecnología obsoleta para este ecosistema.
- Prohibido usar componentes nativos aburridos. Todo debe sentirse fluido, moderno y digno de ser exhibido en *Dark.design*.
