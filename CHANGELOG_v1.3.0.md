# 📋 Informe de Mejoras y Cambios — ScrcpyGUI v1.3.0
**Fecha:** 17 de Agosto, 2026  
**Versión:** 1.3.0 *"IDE Layout, Smart Hardware Detection & Virtual App Display"*

---

## 📝 Resumen Ejecutivo

La versión **1.3.0** representa una de las mayores evoluciones de **ScrcpyGUI**, transformando la aplicación en un entorno de trabajo profesional con estética inspirada en editores de código modernos (VS Code / JetBrains / Cursor). Introduce detección y adaptación inteligente de hardware por dispositivo, soporte para pantallas virtuales multi-ventana con auto-lanzador de apps y Pantalla Flex, un buscador modal de aplicaciones con filtrado en tiempo real, y una suite completa de pruebas unitarias automatizadas.

---

## 🌟 Principales Novedades y Características

### 1. 🎨 Rediseño Integral de Interfaz (Estilo IDE Profesional)
- **Barra de Navegación Superior Compacta**: Integra el logotipo, selector de dispositivos con auto-detección, accesos directos a herramientas de inspección (`🎬 Encoders`, `📷 Cámaras`, `🖥️ Pantallas`, `⚡ Modo PC`), botón de actualización rápida y botón principal de ejecución (`▶ Iniciar Scrcpy` / `⏹ Detener`).
- **Barra Lateral de Actividades (Explorer)**: Lista vertical estilizada de todos los perfiles de conexión (`🖥️ Modo Escritorio`, `🚀 App en Pantalla Virtual`, `🎮 Gaming Pro`, `🎬 Cine 2K`, `⚖️ Balanceado`, `📺 Streamer`, etc.) + `⚙️ Personalizado` + Tarjeta de versión instalada con buscador de actualizaciones.
- **Espacio de Trabajo Central Dinámico**:
  - **Ficha Técnica de Presets**: Muestra 4 tarjetas de métricas en tiempo real (*Códec, Resolución, FPS, Bitrate*), lista de características activas y panel de *Interruptores Rápidos de Sesión* (*Mantener despierto, Apagar pantalla móvil, Pantalla completa, Siempre visible, Pantalla Flex*).
  - **Editor de Propiedades Avanzadas**: Pestañas con distribución simétrica en 2 columnas sin saltos de posición (`anchor="nw"`).
- **Dock de Terminal Integrada**: Consola inferior estilo terminal de desarrollo con texto verde Consolas, botón para copiar el comando CLI exacto generado (`📋 Copiar CLI`) y limpiador de registro (`🗑️ Limpiar`).
- **Barra de Estado Inferior**: Muestra la versión de scrcpy activa, estado del dispositivo conectado, codificación y versión de ScrcpyGUI.

---

### 2. 📱 Detección y Adaptación Inteligente de Hardware
- **Escaneo Automático Asíncrono**: Al conectar o seleccionar un dispositivo, ScrcpyGUI analiza en segundo plano sus encoders de hardware, cámaras, pantallas y versión de Android / capa de personalización (HyperOS, Samsung OneUI, Pixel, etc.).
- **Filtrado Dinámico de Opciones**:
  - El selector de **Códec de Video** se actualiza automáticamente para mostrar **únicamente** los códecs soportados por el chip del móvil (`H264`, `H265`, `AV1`, `VP9`, `VP8`).
  - El selector de **Códec de Audio** filtra formatos compatibles (`Opus`, `AAC`, `FLAC`, `RAW`).
- **Auto-adaptación de Presets**: Si se selecciona un perfil con un códec no soportado por el hardware conectado, la app lo auto-adapta al mejor códec disponible sin interrumpir el flujo ni generar errores.
- **Caché por Serial**: Almacenamiento en memoria de las capacidades para cambios instantáneos entre dispositivos sin re-escanear.
- **Reporte Técnico Inmediato**: Imprime en la consola el desglose de hardware y muestra el modelo y versión de Android en la barra de estado.

---

### 3. 🚀 Preset 'App en Pantalla Virtual' & Pantalla Flex (scrcpy v4.0+)
- **Nuevo Modo Preconfigurado**: Abre aplicaciones del móvil en una pantalla virtual secundaria independiente tipo monitor secundario.
- **Prompt Automático de Selección**: Al activar el modo, se abre de forma automática el selector de aplicaciones para elegir qué app ejecutar.
- **Tarjeta Interactiva en el Inspector**: Permite visualizar la aplicación vinculada y cambiarla o desvincularla con un solo clic.
- **Soporte de Pantalla Flex (`--flex-display`)**: Permite que la ventana en Windows adapte su resolución y contenido fluidamente conforme se redimensiona en la PC.

---

### 4. 🔍 Modal de Búsqueda Rápida de Aplicaciones (`AppPickerModal`)
- Reemplazo de los menús desplegables estáticos por un diálogo modal interactivo.
- **Filtrado en tiempo real** por nombre comercial o identificador de paquete (`package name`).
- Tarjetas oscuras con resaltado al pasar el ratón (*hover*), selección en 1 clic y botón de cierre rápido.

---

## 🧪 Pruebas y Calidad de Código
- **27 Pruebas Unitarias Automatizadas (100% PASS)** en `unittest`.
- Módulos probados:
  - Construcción determinista de comandos CLI (`command_builder.py`).
  - Persistencia, guardado y copias de seguridad de perfiles (`config_manager.py`).
  - Parseo de encoders, cámaras, pantallas y extracción de IPs (`scrcpy_manager.py`).
- Compatibilidad validada con scrcpy v4.1 en Windows 10 / 11.
