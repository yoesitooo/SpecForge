# Skill: Page Optimizer & Performance Tuning
triggers: [optimizar, performance, lag, fps, svg pesado, lighthouse, rendimiento, fast]

## Propósito
Esta skill enseña al agente a optimizar el rendimiento de las páginas web (especialmente React/Next.js/Vite) para lograr 60 FPS consistentes y un tiempo de carga (LCP) menor a 1.5s, resolviendo problemas comunes como los vistos previamente con activos pesados.

## 1. Reglas de Optimización de Activos (Assets)
- **SVGs**: Nunca cargues SVGs gigantes (>100kb) directamente en el DOM o como componentes React. Usa etiquetas `<img>` con `loading="lazy"` o conviértelos en imágenes `.webp`.
- **Videos**: 
  - Usa formato `.webm` o `.mp4` altamente comprimido.
  - Atributos obligatorios: `<video autoPlay loop muted playsInline preload="none" poster="miniatura.webp">`
  - NUNCA cargues videos HD en móvil. Usa `srcSet` o media queries para cargar versiones ligeras.

## 2. Prevención de Layout Shifts (CLS)
- Todas las imágenes y videos DEBEN tener un `width` y `height` explícito, o un `aspect-ratio` definido en CSS para evitar saltos en la pantalla mientras cargan.
- Proporciona un `skeleton loader` o `min-height` para contenedores que cargarán contenido dinámico.

## 3. Optimización de React / JavaScript
- Usa `React.lazy()` y `<Suspense>` para dividir el código (Code Splitting). Los componentes que no son visibles al inicio (below the fold) no deben cargar inmediatamente.
- Evita re-renders innecesarios: usa `useMemo` y `useCallback` en componentes pesados o listas grandes.
- Elimina cualquier dependencia muerta o redundante.

## 4. Animaciones y Framerate
- NUNCA animes propiedades como `width`, `height`, `top`, `left`, o `margin` ya que fuerzan el re-cálculo del layout (Reflow) y causan lag.
- Anima ÚNICAMENTE `transform` (translate, scale, rotate) y `opacity`.
- Usa `will-change: transform` para promover elementos a su propia capa de GPU si tienen animaciones complejas, pero úsalo con moderación para no saturar la memoria.

## Checklist de Salida
Antes de entregar, verifica:
- [ ] No hay SVGs gigantes en línea.
- [ ] Las imágenes usan `lazy loading` y formatos modernos (WebP).
- [ ] Las animaciones usan `transform` y no afectan el layout.
- [ ] Los videos no bloquean el renderizado inicial y están silenciados/comprimidos.
