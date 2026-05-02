# ScrcpyGUI 🚀

**ScrcpyGUI** es una interfaz gráfica nativa para Windows diseñada para potenciar el uso de [scrcpy](https://github.com/Genymobile/scrcpy). Permite controlar dispositivos Android con configuraciones optimizadas, gestión de latencia ultra baja y actualización automática del motor.

![ScrcpyGUI Badge](https://img.shields.io/badge/Version-v1.0.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.14+-yellow?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-orange?style=for-the-badge)

## ✨ Características Principales

- **📦 Auto-Updater**: Descarga y actualiza automáticamente la última versión de `scrcpy` directamente desde GitHub.
- **🎨 Presets Optimizados**:
  - **🎬 Cinema**: Máxima fidelidad visual (4K/HEVC) para consumo de contenido.
  - **🎮 Pro Gaming**: Latencia mínima con soporte para entrada HID física (Teclado/Ratón/Gamepad).
  - **⚖️ Balanced**: Perfil estándar para uso diario y aplicaciones.
  - **🚀 Ultra (AV1)**: Preparado para el futuro con soporte de códec AV1 y altas tasas de refresco (144Hz+).
- **🎛️ Panel Personalizado**: Control total sobre códecs (H264, H265, AV1), bitrates, FPS, buffers y más.
- **📱 Quick Settings**: Toggles rápidos para apagar la pantalla del dispositivo o mantenerlo despierto sin cambiar de perfil.
- **💻 Terminal Integrada**: Visualización en tiempo real de los logs de `scrcpy` para depuración.

## 🛠️ Herramientas y Tecnologías

- **Lenguaje**: Python 3.14+
- **GUI**: CustomTkinter (Modern Dark Theme)
- **Motor**: scrcpy (Genymobile)
- **Compilación**: PyInstaller
- **Detección de Hardware**: ADB (Android Debug Bridge)

## 🚀 Instalación y Uso

1. Descarga el ejecutable desde la carpeta `dist/` o los Releases de GitHub.
2. Asegúrate de tener **Depuración USB** activada en tu dispositivo Android.
3. Conecta el móvil por USB o Wi-Fi.
4. Selecciona un modo y pulsa **Iniciar Scrcpy**.

## 🏗️ Estructura del Proyecto

- `scrcpy_gui.py`: Lógica principal de la interfaz y gestión de procesos.
- `scrcpy_manager.py`: Módulo de descarga, verificación de versiones y gestión de archivos.
- `ScrcpyGUI.spec`: Configuración para empaquetado del ejecutable.
- `.gitignore`: Configuración de exclusión para Git.

## 📝 Especificaciones Técnicas

| Característica | Detalle |
| :--- | :--- |
| **Códecs Soportados** | H.264, H.265 (HEVC), AV1 |
| **Input** | HID (Teclado, Ratón, Gamepad), AOA, UHID |
| **Audio** | Forwarding nativo de scrcpy |
| **Resolución** | Hasta 4K / Nativa |
| **Tasa de Refresco** | Hasta 144Hz |

---
Desarrollado para mejorar la experiencia de productividad y gaming entre Android y PC.
