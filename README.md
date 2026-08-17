# 📱 ScrcpyGUI v1.3.0 - IDE Edition 2026

> [!IMPORTANT]
> **Aviso Legal / Disclaimer**: ScrcpyGUI es una interfaz gráfica (GUI) independiente y no oficial diseñada para facilitar el uso de [scrcpy](https://github.com/Genymobile/scrcpy). Este proyecto es un **complemento** y no está afiliado, asociado ni respaldado por **Genymobile** ni por los desarrolladores originales de scrcpy. Todas las marcas comerciales y el motor de streaming pertenecen a sus respectivos dueños.

Una interfaz gráfica profesional, ultra-rápida y optimizada para la gestión de dispositivos Android mediante `scrcpy`. Diseñada con una arquitectura modular inspirada en los editores de código modernos (VS Code / JetBrains / Cursor), con escaneo automático de capacidades de hardware por dispositivo y soporte avanzado para pantallas virtuales.

---

## 🚀 Novedades de la Versión 1.3.0

### 💻 1. Nuevo Diseño Modular Estilo IDE
- **Top Navigation Bar**: Barra de estado superior con selector de dispositivos en vivo, accesos rápidos a consultas de hardware (`🎬 Encoders`, `📷 Cámaras`, `🖥️ Pantallas`, `⚡ Modo PC`), botón de actualización y botón de ejecución optimizado.
- **Activity Sidebar**: Barra lateral vertical con lista de presets clasificados por colores, badges descriptivos y tarjeta de estado de versión.
- **Center Workspace**: Ficha técnica interactiva con estadísticas en tiempo real (*Códec, Resolución, FPS, Bitrate*), características del modo y switches rápidos de sesión.
- **Terminal Console Dock**: Consola integrada en la parte inferior con formato monoespaciado verde estilo IDE para ver comandos CLI y registros en vivo con botones de `[ 📋 Copiar CLI ]` y `[ 🗑️ Limpiar ]`.

### 🧠 2. Escaneo Inteligente de Hardware
- Al conectar un dispositivo, la aplicación consulta automáticamente vía ADB y scrcpy sus **encoders de video compatibles** (H.264, H.265, AV1, VP9), **encoders de audio**, **cámaras físicas** y **pantallas activas**.
- Los menús y opciones se adaptan automáticamente para mostrar **únicamente lo compatible con tu teléfono**.

### 📱 3. Preset "App en Pantalla Virtual" & Selector Modal
- Abre cualquier aplicación instalada en tu móvil en una pantalla secundaria aislada con resolución de tablet y control por hardware UHID.
- **Modal de Búsqueda Instantánea**: Encuentra y selecciona apps en milisegundos con filtrado en tiempo real.

### 🔄 4. Soporte Pantalla Flex (scrcpy v4.0+)
- La pantalla virtual se redimensiona automáticamente al tamaño de la ventana en PC sin bordes negros ni deformaciones.

### 📦 5. Actualizador Integrado
- Detección, descarga e instalación automática de la última versión oficial de scrcpy directamente desde GitHub Releases.

---

## 📖 Guía de Uso Rápido

### 1. Iniciar con un Preset
- Selecciona uno de los perfiles en la barra lateral izquierda (ej. `🎮 Gaming Pro`, `🖥️ Modo Escritorio`, `🚀 App en Pantalla Virtual`).
- Revisa las métricas en el panel central y presiona **`▶ Iniciar Scrcpy`**.

### 2. Conexión Inalámbrica Wi-Fi
- **Con cable USB previo**: Haz clic en **`⚡ Auto-USB`** en la pestaña Wi-Fi para conectar automáticamente sin cables.
- **Sin cable (Android 11+)**: Empareja ingresando la IP y el código de 6 dígitos en la pestaña Wi-Fi.

### 3. Modo Personalizado
- Si necesitas una configuración a medida, selecciona **`⚙️ Personalizado`** para acceder a todas las opciones organizadas en pestañas (*Video, Audio, Pantalla, Controles, Wi-Fi, Perfiles*).

---

## 🛠️ Requisitos
- **Sistema Operativo**: Windows 10/11 (64-bit), Linux o macOS.
- **Android**: Android 5.0+ (Android 10+ para pantallas virtuales, Android 11+ para audio y Wi-Fi sin cables).
- **Python**: Python 3.10+ con dependencias de `requirements.txt`.

---

## 📜 Licencia
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

*Desarrollado por [zTheNea](https://github.com/zTheNea) — Agosto 2026*
