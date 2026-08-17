# 📱 ScrcpyGUI v1.3.0 - IDE Edition

> [!IMPORTANT]
> **Aviso Legal / Disclaimer**: ScrcpyGUI es una interfaz gráfica (GUI) independiente y de código abierto diseñada para facilitar el uso y la configuración de [scrcpy](https://github.com/Genymobile/scrcpy). Este proyecto es un **complemento** y no está afiliado, asociado ni respaldado por **Genymobile** ni por los desarrolladores originales de scrcpy.

Una interfaz gráfica profesional, ultra-rápida y optimizada con **diseño estilo IDE (VS Code / JetBrains)** para la gestión y control avanzado de dispositivos Android mediante `scrcpy`.

---

## 🚀 Principales Novedades de la Versión 1.3.0

### 🎨 1. Nueva Interfaz de Usuario Estilo IDE
- **Navegación Superior Compacta**: Selector de dispositivos con auto-escaneo, accesos directos a herramientas de hardware (`🎬 Encoders`, `📷 Cámaras`, `🖥️ Pantallas`, `⚡ Modo PC`) y botón de ejecución rápido.
- **Barra Lateral de Explorador de Presets**: Menú visual con badges de rendimiento y tarjeta de versión scrcpy con comprobación de actualizaciones.
- **Ficha Técnica Central de Presets**: Panel interactivo con 4 tarjetas de métricas en tiempo real (*Códec, Resolución, FPS, Bitrate*), lista de características y switches de sesión.
- **Dock de Terminal Integrado**: Consola inferior de desarrollo con colores verde Consolas, botón `📋 Copiar CLI` y limpiador de logs.

### 📱 2. Detección y Adaptación Inteligente de Hardware
- **Escaneo Asíncrono Automático**: Al conectar tu dispositivo, ScrcpyGUI analiza en segundo plano sus encoders de video/audio, cámaras y pantallas.
- **Menús Dinámicos**: Los selectores de **Códec de Video** y **Códec de Audio** solo muestran los códecs soportados por el chip del teléfono (`H.264`, `H.265`, `AV1`, `VP9`, `Opus`, `AAC`, `FLAC`).
- **Auto-adaptación de Perfiles**: Si un preset utiliza un códec no soportado por tu móvil, se auto-adapta inmediatamente para evitar fallos de lanzamiento.

### 🚀 3. Modo 'App en Pantalla Virtual' & Pantalla Flex
- **Multi-Ventana Aislada**: Abre apps específicas de tu teléfono en una pantalla virtual secundaria tipo monitor independiente.
- **Buscador Modal de Aplicaciones (`AppPickerModal`)**: Popup interactivo con filtrado en tiempo real por nombre o paquete (`package name`).
- **Pantalla Flex (`--flex-display`)**: Adapta la resolución dinámicamente conforme cambias el tamaño de la ventana en PC.

---

## 📖 Guía de Uso Rápido

### 1. Conexión Rápida
1. Conecta tu móvil por cable USB (o vía Wi-Fi desde la pestaña **📶 Wi-Fi**).
2. ScrcpyGUI detectará automáticamente tu modelo y configurará los códecs compatibles.

### 2. Selección de Perfiles
* **🖥️ Modo Escritorio (DeX)**: Pantalla virtual 1080p con DPI de tablet y control por teclado/ratón UHID.
* **🚀 App en Pantalla Virtual**: Te pedirá qué app deseas abrir y la ejecutará en una ventana secundaria redimensionable con Pantalla Flex.
* **🎮 Gaming Pro (120fps/HID)**: Latencia cero, tasa de cuadros de 120 FPS y control por hardware UHID.
* **🎬 Cine 2K (H.265)**: Máxima fidelidad de imagen a 1440p con bajo consumo de ancho de banda.
* **⚙️ Personalizado**: Acceso al editor avanzado de propiedades por pestañas.

---

## 🛠️ Requisitos
- **Sistema Operativo**: Windows 10 / 11 (64-bit).
- **Android**: Android 5.0+ (Android 10+ para pantallas virtuales, Android 11+ para audio y Wi-Fi pairing).
- **scrcpy**: Compatible con scrcpy v2.x hasta v4.1+ (se puede descargar automáticamente desde el botón de actualización en la app).

---

## 📜 Licencia
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

*Desarrollado por [zTheNea](https://github.com/zTheNea)*
