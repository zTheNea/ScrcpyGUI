# 📱 ScrcpyGUI v1.3.0 — IDE Edition 2026

> [!IMPORTANT]
> **Aviso Legal / Disclaimer**: ScrcpyGUI es una interfaz gráfica (GUI) independiente y no oficial diseñada para facilitar el uso de [scrcpy](https://github.com/Genymobile/scrcpy). Este proyecto es un **complemento** y no está afiliado, asociado ni respaldado por **Genymobile** ni por los desarrolladores originales de scrcpy. Todas las marcas comerciales y el motor de streaming pertenecen a sus respectivos dueños.

Una interfaz gráfica profesional, ultra-rápida y optimizada para la gestión de dispositivos Android mediante `scrcpy`. Diseñada con una arquitectura modular inspirada en los editores de código modernos (VS Code / JetBrains / Cursor), con escaneo automático de capacidades de hardware por dispositivo y soporte avanzado para pantallas virtuales.

---

## 🛠️ Requisitos Previos

Antes de usar ScrcpyGUI, asegúrate de cumplir con los siguientes requisitos en tu **PC** y en tu **teléfono Android**.

### 💻 En tu PC (Windows / Linux / macOS)

| Requisito | Detalle |
|---|---|
| **Sistema Operativo** | Windows 10/11 (64-bit), Linux o macOS |
| **Python** | Python 3.10 o superior ([python.org](https://www.python.org/downloads/)) |
| **pip** | Viene incluido con Python. Se usa para instalar las dependencias |
| **scrcpy** | Se descarga automáticamente desde la app, o puedes instalarlo manualmente desde [github.com/Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) |
| **ADB (Android Debug Bridge)** | Incluido automáticamente con scrcpy en Windows. En Linux/macOS, instálalo con tu gestor de paquetes (`sudo apt install adb` / `brew install android-platform-tools`) |
| **Cable USB** | Necesario para la conexión inicial. Después puedes conectar por Wi-Fi |

> [!TIP]
> **¿No tienes scrcpy?** No te preocupes. ScrcpyGUI detecta si scrcpy no está instalado y te ofrece un botón de **descarga automática** directamente desde GitHub Releases. Solo necesitas conexión a internet.

### 📱 En tu Teléfono Android

| Requisito | Detalle |
|---|---|
| **Versión de Android** | Android 5.0 (Lollipop) como mínimo |
| **Depuración USB** | **Obligatorio.** Debe estar activada en *Opciones de Desarrollador* |
| **Cable USB** | Para la conexión inicial entre el teléfono y el PC |

#### Cómo activar la Depuración USB:
1. Ve a **Ajustes → Acerca del teléfono**.
2. Toca **"Número de compilación"** 7 veces seguidas hasta que diga *"Eres un desarrollador"*.
3. Vuelve a **Ajustes → Opciones de desarrollador** (o *Ajustes → Sistema → Opciones de desarrollador*).
4. Activa **"Depuración USB"**.
5. Conecta el cable USB al PC y acepta el mensaje de **"¿Permitir depuración USB?"** en tu teléfono.

> [!NOTE]
> La ubicación exacta del menú varía según la marca del teléfono (Samsung, Xiaomi, Motorola, etc.), pero el proceso siempre es el mismo.

### 📶 Requisitos Adicionales por Función

No todas las funciones están disponibles en todas las versiones de Android. Aquí tienes una tabla de compatibilidad:

| Función | Versión mínima de Android | Notas |
|---|---|---|
| Espejado de pantalla básico | Android 5.0+ | Funciona en prácticamente cualquier teléfono |
| Transmisión de Audio al PC | Android 11+ (API 30) | El audio del teléfono se escucha en tu PC |
| Conexión Wi-Fi sin cable USB | Android 11+ (API 30) | Requiere emparejamiento previo con código de 6 dígitos |
| Pantallas Virtuales (Modo Escritorio/DeX) | Android 10+ (API 29) | Crea una segunda pantalla independiente en tu teléfono |
| Pantalla Flex (redimensionable) | Android 10+ + scrcpy v4.0+ | La pantalla virtual se adapta al tamaño de la ventana en PC |
| Control por Hardware UHID (Teclado/Ratón) | Android 13+ (API 33) | El teclado y ratón del PC funcionan como periféricos nativos del teléfono |
| Modo OTG (Hardware puro) | Android 5.0+ | El teléfono usa el teclado/ratón del PC como si fueran USB reales |
| Cámara como Webcam | Android 12+ (API 31) + scrcpy v2.7+ | Usa la cámara del teléfono como webcam en tu PC |

---

## 🚀 Instalación

### Opción A: Ejecutar desde el código fuente (Recomendado para desarrollo)

```bash
# 1. Clonar el repositorio
git clone https://github.com/zTheNea/ScrcpyGUI.git
cd ScrcpyGUI

# 2. Instalar las dependencias de Python
pip install -r requirements.txt

# 3. Ejecutar la aplicación
python scrcpy_gui.py
```

### Opción B: Ejecutable portable (.exe) para Windows

Descarga el archivo `ScrcpyGUI.exe` desde la sección de [Releases](https://github.com/zTheNea/ScrcpyGUI/releases) y ejecútalo directamente. No requiere Python instalado.

### Opción C: Compilar tu propio .exe con PyInstaller

```bash
pip install pyinstaller
pyinstaller ScrcpyGUI.spec
```
El ejecutable se generará en la carpeta `dist/`.

---

## 🌟 Novedades de la Versión 1.3.0

### 💻 1. Nuevo Diseño Modular Estilo IDE
- **Top Navigation Bar**: Barra de estado superior con selector de dispositivos en vivo, accesos rápidos a consultas de hardware (`🎬 Encoders`, `📷 Cámaras`, `🖥️ Pantallas`, `⚡ Modo PC`), botón de actualización y botón de ejecución optimizado.
- **Activity Sidebar**: Barra lateral vertical con lista de presets clasificados por colores, badges descriptivos y tarjeta de estado de versión.
- **Center Workspace**: Ficha técnica interactiva con estadísticas en tiempo real (*Códec, Resolución, FPS, Bitrate*), características del modo y switches rápidos de sesión.
- **Terminal Console Dock**: Consola integrada en la parte inferior con formato monoespaciado verde estilo IDE para ver comandos CLI y registros en vivo con botones de `[ 📋 Copiar CLI ]` y `[ 🗑️ Limpiar ]`.

### 🧠 2. Escaneo Inteligente de Hardware
- Al conectar un dispositivo, la aplicación consulta automáticamente vía ADB y scrcpy sus **encoders de video compatibles** (H.264, H.265, AV1, VP9), **encoders de audio**, **cámaras físicas** y **pantallas activas**.
- Los menús y opciones se adaptan automáticamente para mostrar **únicamente lo compatible con tu teléfono**.

### 📱 3. Selector Integrado de Aplicaciones
- Abre cualquier aplicación instalada en tu móvil en una pantalla secundaria aislada con resolución de tablet y control por hardware UHID.
- **Selector inline con búsqueda en tiempo real**: Encuentra y selecciona apps sin ventanas flotantes, directamente integrado en la interfaz.

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

## ❓ Preguntas Frecuentes (FAQ)

<details>
<summary><b>¿Necesito rootear mi teléfono?</b></summary>

**No.** ScrcpyGUI y scrcpy funcionan completamente sin root. Solo necesitas activar la Depuración USB en las Opciones de Desarrollador.
</details>

<details>
<summary><b>¿Mi teléfono deja de funcionar mientras uso scrcpy?</b></summary>

**No.** Tu teléfono sigue funcionando normalmente. scrcpy solo lee la pantalla y envía eventos de entrada. Puedes usar el teléfono al mismo tiempo.
</details>

<details>
<summary><b>¿Funciona con cualquier marca de teléfono?</b></summary>

**Sí**, funciona con Samsung, Xiaomi, Motorola, OnePlus, Google Pixel, Huawei, Oppo, Realme, Nothing y cualquier teléfono que ejecute Android 5.0 o superior y tenga Depuración USB.
</details>

<details>
<summary><b>¿Se consume la batería del teléfono?</b></summary>

Si estás conectado por USB, el teléfono se carga al mismo tiempo. Por Wi-Fi, el consumo es similar al de una videollamada.
</details>

<details>
<summary><b>¿Puedo usar el teclado y ratón de mi PC para controlar el teléfono?</b></summary>

**Sí.** ScrcpyGUI soporta múltiples modos de control: inyección de teclado/ratón vía ADB, modo UHID (hardware nativo en Android 13+) y modo OTG (hardware puro USB). El modo se configura desde el preset o la pestaña Controles.
</details>

<details>
<summary><b>¿Puedo jugar juegos móviles con teclado y ratón?</b></summary>

**Sí.** El modo `🎮 Gaming Pro` está optimizado para esto, con baja latencia (120fps), inyección por hardware UHID y sin audio para reducir el delay al mínimo.
</details>

---

## 🏗️ Arquitectura del Proyecto

```
ScrcpyGUI/
├── scrcpy_gui.py          # Interfaz gráfica principal (CustomTkinter)
├── scrcpy_manager.py      # Lógica de ADB, red, descargas y hardware
├── command_builder.py      # Generador de argumentos CLI de scrcpy
├── config_manager.py       # Persistencia de configuración y perfiles
├── presets.py              # Presets y paleta de colores
├── paths.py                # Rutas centralizadas del sistema
├── strings.py              # Textos de la interfaz (localización)
├── gui/
│   ├── __init__.py
│   └── widgets.py          # Componentes reutilizables (InlineAppPicker, etc.)
├── tests/
│   ├── test_command_builder.py
│   ├── test_config_manager.py
│   ├── test_preset_filtering.py
│   ├── test_scrcpy_manager.py
│   └── test_paths.py
├── requirements.txt        # Dependencias de Python
├── ScrcpyGUI.spec          # Configuración de PyInstaller
└── LICENSE                 # Licencia MIT
```

---

## 📜 Licencia
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

*Desarrollado por [zTheNea](https://github.com/zTheNea) — Agosto 2026*
