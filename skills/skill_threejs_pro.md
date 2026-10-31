# Skill: Three.js Pro — Experiencias 3D Inmersivas

---
name: threejs_pro
description: "Guía para integrar elementos 3D premium usando Three.js. Enfocada en performance, estética futurista y micro-interacciones."
---

### 🎨 Estética 3D Premium
- **Fondos de Partículas**: Usa `THREE.Points` para crear fondos de polvo estelar o redes neuronales interactivas.
- **Materiales Glassmorphism**: Implementa `MeshPhysicalMaterial` con `transmission`, `roughness: 0` y `thickness` para efectos de vidrio 3D.
- **Iluminación Cinematográfica**: Combina `AmbientLight` (baja intensidad) con `SpotLight` o `PointLight` de colores vibrantes (Cyan, Magenta, Gold) para crear profundidad.

### 🚀 Optimización y Rendimiento
- **Ciclo de Render**: Usa siempre `requestAnimationFrame`.
- **Limpieza de Memoria**: Si se destruye un componente, asegúrate de hacer `dispose()` de geometrías, materiales y texturas.
- **Geometrías Simples**: Prefiere `BufferGeometry` para alto rendimiento en partículas.

### 🛠️ Integración con React (Si aplica)
- Usa **React Three Fiber (R3F)** y **Drei** para una implementación declarativa y limpia.
- Implementa `Suspense` para estados de carga de modelos pesados (GLTF/GLB).

### 🛑 Reglas de Oro
- No satures la escena: "Menos es más". Un solo elemento 3D bien iluminado impacta más que diez mal hechos.
- Interactividad: El 3D debe reaccionar al mouse (parallax sutil) para sentirse vivo.
- Responsividad: Ajusta el `aspect ratio` de la cámara en el evento `resize`.

---
*Este manual convierte cualquier interfaz plana en una experiencia tridimensional de vanguardia.*
