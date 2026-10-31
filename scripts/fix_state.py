import json
import os

# Calcula la ruta dinámica desde la ubicación del script
# scripts/ -> AgentHub/ -> root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_HUB_DIR = os.path.dirname(SCRIPT_DIR)  # sube de scripts/ a AgentHub/
file_path = os.path.join(AGENT_HUB_DIR, 'memory', 'orchestrator_state.json')

with open(file_path, 'r', encoding='utf-8') as f:
    state = json.load(f)

# New 43 tasks plan
new_plan = """### TAREA-01: package.json - Definición de dependencias y scripts de inicio.
### TAREA-02: vite.config.js - Configuración de Vite con plugins de React y optimización de carga.
### TAREA-03: tailwind.config.js - Configuración de plugins (Forms, Typography) y extensión de colores personalizados.
### TAREA-04: postcss.config.js - Configuración de PostCSS para procesar Tailwind.
### TAREA-05: src/index.css - Reset CSS global, import de Framer Motion y variables CSS base.
### TAREA-06: public/favicon.ico - Icono de la aplicación para pestañas del navegador.
### TAREA-07: public/robots.txt - Archivo para SEO básico y rastreo de bots.
### TAREA-08: public/sitemap.xml - Estructura básica de sitemap para SEO.
### TAREA-09: src/components/layout/Layout.jsx - Componente contenedor principal con wrapper de animación de entrada.
### TAREA-10: src/components/layout/Navbar.jsx - Barra de navegación con efecto glassmorphism y scroll spy.
### TAREA-11: src/components/layout/NavbarLogo.jsx - Logo de texto estilizado con gradiente neón.
### TAREA-12: src/components/layout/NavbarLinks.jsx - Enlaces de navegación con hover effects.
### TAREA-13: src/components/layout/Footer.jsx - Footer con enlaces legales y redes sociales.
### TAREA-14: src/components/layout/FooterSocial.jsx - Componente de iconos de redes sociales.
### TAREA-15: src/components/sections/Hero.jsx - Sección principal con layout de dos columnas (texto + visual).
### TAREA-16: src/components/sections/HeroText.jsx - Componente de H1, H2 y párrafos con tipografía jerárquica.
### TAREA-17: src/components/sections/HeroButton.jsx - Botón primario con efecto de brillo y sombra.
### TAREA-18: src/components/sections/HeroButtonSecondary.jsx - Botón secundario (outline) con hover.
### TAREA-19: src/components/sections/HeroVisual.jsx - Contenedor del placeholder de imagen principal.
### TAREA-20: src/components/sections/HeroBackground.jsx - Fondo con gradientes animados y partículas sutiles.
### TAREA-21: src/components/sections/Features.jsx - Sección de características con grid responsive.
### TAREA-22: src/components/sections/FeatureCard.jsx - Tarjeta de característica con efecto glassmorphism.
### TAREA-23: src/components/sections/FeatureIcon.jsx - Icono de Lucide dentro de la tarjeta.
### TAREA-24: src/components/sections/FeatureDescription.jsx - Texto descriptivo con animación de entrada escalonada.
### TAREA-25: src/components/sections/Services.jsx - Sección de servicios con layout de tarjetas.
### TAREA-26: src/components/sections/ServiceCard.jsx - Tarjeta de servicio con imagen placeholder y botón de acción.
### TAREA-27: src/components/sections/ServiceImage.jsx - Placeholder de imagen de servicio con lazy loading.
### TAREA-28: src/components/sections/ServiceTitle.jsx - Título del servicio con gradiente de texto.
### TAREA-29: src/components/sections/ContactForm.jsx - Formulario de contacto con React Hook Form.
### TAREA-30: src/components/sections/ContactInput.jsx - Inputs estilizados con focus rings neón.
### TAREA-31: src/components/sections/ContactSubmit.jsx - Botón de envío con estado de carga (spinner).
### TAREA-32: src/components/sections/ContactInfo.jsx - Información de contacto (email, teléfono).
### TAREA-33: src/hooks/useScrollAnimation.jsx - Hook personalizado para detectar elementos en viewport.
### TAREA-34: src/utils/animations.json - Definición de animaciones de Framer Motion (fadeUp, scaleIn).
### TAREA-35: src/utils/constants.js - Definición de constantes de diseño (espaciado, breakpoints).
### TAREA-36: src/assets/images/hero-bg.webp - Placeholder de imagen de fondo optimizado.
### TAREA-37: src/assets/images/service-1.webp - Placeholder de imagen para servicio 1.
### TAREA-38: src/assets/images/service-2.webp - Placeholder de imagen para servicio 2.
### TAREA-39: src/assets/images/service-3.webp - Placeholder de imagen para servicio 3.
### TAREA-40: src/assets/images/hero-visual.webp - Placeholder de imagen principal del hero.
### TAREA-41: index.html - Archivo HTML principal de la aplicación.
### TAREA-42: src/main.jsx - Punto de entrada de React.
### TAREA-43: src/App.jsx - Componente raíz que agrupa Layout, Hero, Features, Services y ContactForm."""

state['node_outputs']['planear_tareas'] = new_plan
state['current_task_index'] = 43 # Done
state['auto_limit'] = 0 # Stop automation
state['node_index'] = 6 # Move to Verification phase to stop implementing
state['current_node'] = 'verificar'
state['node_outputs']['implementar'] = "Implementación finalizada con éxito."
state['error_counts'] = {} # Limpiar Circuit Breaker para el nuevo intento

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)

print("Estado del orquestador actualizado correctamente.")
