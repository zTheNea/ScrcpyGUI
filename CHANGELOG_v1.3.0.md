# 🚀 Registro de Cambios - ScrcpyGUI v1.3.0

**Fecha:** Agosto 2026  
**Versión:** `v1.3.0` "IDE Edition & Smart Hardware Intelligence"

---

## 📝 Resumen Ejecutivo

La versión **1.3.0** representa el mayor rediseño visual y técnico de ScrcpyGUI hasta la fecha. Se ha transformado la experiencia de usuario adoptando un diseño modular moderno inspirado en los editores de código contemporáneos (VS Code / JetBrains / Cursor), integrando un sistema de escaneo automático de capacidades de hardware por dispositivo y añadiendo herramientas de multitarea como pantallas virtuales interactivas con selector inteligente de aplicaciones y soporte dinámico de Pantalla Flex (scrcpy v4.0+).

---

## 🌟 Novedades Principales

### 💻 1. Nuevo Diseño Modular Estilo IDE
- **Barra de Navegación Superior Unificada (`Topbar`)**:
  - Logo compacto con acceso directo al selector de dispositivos en tiempo real.
  - Botones de diagnóstico de hardware en 1 clic (`🎬 Encoders`, `📷 Cámaras`, `🖥️ Pantallas`, `⚡ Modo PC`).
  - Botón de actualización de scrcpy y botón de ejecución estilizado (`▶ Iniciar Scrcpy` / `⏹ Detener`).
- **Barra Lateral de Actividades (`Sidebar`)**:
  - Explorador vertical de modos y presets con badges descriptivos y realce de color por categoría.
  - Tarjeta de versión integrada en el pie con verificación y descarga en segundo plano.
- **Espacio de Trabajo Central Adaptativo (`Center Workspace`)**:
  - **Ficha Técnica / Inspector de Preset**: Muestra métricas clave en 4 tarjetas de estadísticas (*Códec, Resolución, FPS, Bitrate*), resumen de características y panel de switches rápidos de sesión.
  - **Editor de Propiedades Avanzado**: Pestañas de configuración personalizada sin saltos ni desalineaciones (`anchor="nw"`).
- **Dock de Terminal Integrado (`Terminal Console Dock`)**:
  - Consola estilo terminal con tipografía monoespaciada verde *Consolas* para logs y comandos generados en tiempo real.
  - Botones rápidos de utilidad: `[ 📋 Copiar CLI ]` y `[ 🗑️ Limpiar ]`.

---

### 🧠 2. Escaneo Inteligente y Adaptación de Capacidades por Dispositivo
- **Análisis de Hardware Automático en Segundo Plano**:
  - Al conectar o seleccionar un dispositivo, ScrcpyGUI analiza de forma asíncrona sus capacidades reales mediante ADB y scrcpy:
    - **Códecs de Video Hardware**: Consulta los encoders disponibles (`--list-encoders`) y filtra el menú de códecs para mostrar **únicamente** los soportados por el chip del teléfono (H.264, H.265, AV1, VP8, VP9).
    - **Códecs de Audio**: Identifica compatibilidad con Opus, AAC, FLAC o RAW.
    - **Cámaras Físicas**: Lista IDs reales y orientaciones (Trasera, Frontal, Gran Angular).
    - **Pantallas**: Detecta resoluciones y pantallas adicionales activas.
    - **Versión de Android & SoC**: Identifica la versión de Android y nivel de API para validar compatibilidad con UHID, Audio forwarding y Modo Escritorio.
  - Sistema de caché por número de serie para respuestas instantáneas.

---

### 📱 3. Preset "App en Pantalla Virtual" & Selector Modal de Apps
- **Nuevo Preset Dedicado**: `🚀 App en Pantalla Virtual` para abrir apps aisladas en un monitor virtual secundario en resolución 1080p con DPI de tablet y control UHID.
- **Modal de Búsqueda Instantánea (`AppPickerModal`)**:
  - Sustituye los menús desplegables estáticos por un diálogo flotante interactivo con filtrado en tiempo real por nombre de app o paquete.
  - Tarjeta interactiva en el panel central con botón directo `[ 🔍 Seleccionar / Cambiar App... ]` y `[ ❌ ]`.

---

### 🔄 4. Integración de Pantalla Flex (scrcpy v4.0+)
- **Soporte `--flex-display`**:
  - Permite que la ventana de la pantalla virtual secundaria adapte automáticamente su resolución y relación de aspecto conforme el usuario redimensiona la ventana en Windows con el ratón.
  - Activada por defecto en el modo de aplicaciones virtuales y accesible desde los interruptores rápidos de sesión.

---

### 📦 5. Actualizador y Gestor de scrcpy Integrado
- **Detección y Descarga Directa**:
  - Consulta automática de las últimas versiones oficiales de scrcpy en GitHub Releases.
  - Descarga, extracción e instalación automática del binario oficial de 64 bits sin necesidad de configuración manual.

---

## 🐛 Correcciones y Optimizaciones Técnicas

- **Estabilidad de Pestañas**: Fijado el alineamiento de pestañas en `CTkTabview` con `anchor="nw"` y layouts balanceados en 2 columnas uniformes para evitar desplazamientos horizontales no deseados.
- **Debouncing de Interfaz**: Actualización de comandos optimizada con temporizador debounce para evitar llamadas redundantes de reconstrucción de CLI.
- **Manejo de Errores de Descarga**: Corregido el manejador de callbacks de descarga para evitar excepciones `AttributeError` en hilos secundarios.
- **Suite de Pruebas Automatizadas**: 27 pruebas unitarias completas pasando al 100% (`tests/test_command_builder.py`, `tests/test_config_manager.py`, `tests/test_scrcpy_manager.py`).

---

*Desarrollado por [zTheNea](https://github.com/zTheNea) — ScrcpyGUI v1.3.0*
