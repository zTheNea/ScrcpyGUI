# Scrcpy Studio v2.0.0 (ScrcpyGUI)

> [!IMPORTANT]
> **Aviso Legal / Disclaimer**: Scrcpy Studio es una interfaz gráfica (GUI) independiente y no oficial diseñada para facilitar el uso de [scrcpy](https://github.com/Genymobile/scrcpy). Este proyecto es un **complemento** y no está afiliado, asociado ni respaldado por **Genymobile** ni por los desarrolladores originales de scrcpy. Todas las marcas comerciales y el motor de streaming pertenecen a sus respectivos dueños.

Una suite visual profesional, moderna y optimizada para la gestión, control y transmisión de dispositivos Android mediante `scrcpy`. Diseñada con una arquitectura desacoplada en PySide6 (Qt) con estética glassmorphism contemporánea, motor backend unificado (`engine/adb.py`) con telemetría en tiempo real y soporte integral para **scrcpy 5.0+**.

---

## 🚀 Novedades de la Versión 2.0.0

* **Nueva Suite Scrcpy Studio (PySide6)**:
  * **Navigation Rail** moderno con vistas modulares: **Inicio**, **Dispositivos**, **Perfiles**, **Grabaciones** y **Ajustes**.
  * **Ajustes Rápidos con Menús Desplegables**: Reemplazo de barras deslizantes imprecisas por selectores desplegables con valores estándar (Resolución, FPS, Bitrate, Códec).
  * **Presets Inteligentes a 1 Clic**: Presets preconfigurados y validados por hardware (Webcam Pro, Ultra Baja Latencia, Gaming 120 FPS, Pantalla Virtual y Audio OTG).
  * **Apartado de Cámara Especializado**: La sección de cámara web adapta los controles exclusivamente para la captura de video (antorcha flash, zoom y orientación).
* **Motor Backend Unificado (`engine/adb.py`)**:
  * Gateway singleton thread-safe con DTOs fuertemente tipados (`DeviceRecord`, `BatteryStatus`, `DisplayMetrics`, `InstalledApp`).
  * Caché de propiedades de hardware en memoria que reduce la latencia de escaneo en más del 70%.
* **Persistencia Atómica y Resiliente (`paths.py`)**:
  * Escritura atómica (`atomic_write_json`) con `fsync` y reemplazo atómico `os.replace` para evitar archivos truncados.
  * Respaldos automáticos `.bak` y auto-recuperación transparente ante archivos dañados.
* **Pool de Workers Controlado (`ui/services.py`)**:
  * Concurrencia acotada con `ThreadPoolExecutor(max_workers=4)` que previene la saturación del bus USB y del servidor ADB.
* **Compatibilidad Total con Scrcpy 5.0+**:
  * Decodificación de video por hardware en GPU (`--hwdec=d3d11va`, `auto`).
  * Alineación de dimensiones (`--min-size-alignment`) y desactivación de mipmaps (`--no-mipmaps`).
  * Sintaxis de forzado de apps (`--start-app=+pkg`) condicional a la versión detectada.
* **Selector Inteligente de Aplicaciones**:
  * Escaneo automático de apps instaladas con resolución de nombres amigables offline sin requerir paquetes manuales.
* **Gestor de Grabaciones**:
  * Explorador de archivos de video grabados con reproducción directa y acceso a directorio.
* **99 Tests Automatizados**:
  * Suite de pruebas unitarias cubriendo DTOs, versionado, persistencia y gateways.

---

## 📋 Requisitos Previos

### En tu PC (Windows / Linux / macOS)

| Requisito | Detalle |
|---|---|
| **Sistema Operativo** | Windows 10/11 (64-bit), Linux o macOS |
| **Python** | Python 3.10 o superior ([python.org](https://www.python.org/downloads/)) |
| **pip** | Viene incluido con Python. Se usa para instalar dependencias |
| **scrcpy** | Se descarga automáticamente desde la app, o puedes instalarlo manualmente desde [github.com/Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) |
| **ADB (Android Debug Bridge)** | Incluido automáticamente con scrcpy en Windows. En Linux/macOS, instálalo con tu gestor de paquetes (`sudo apt install adb` / `brew install android-platform-tools`) |
| **Cable USB** | Necesario para la conexión inicial. Posteriormente puedes conectar por Wi-Fi |

> [!TIP]
> **¿No tienes scrcpy?** Scrcpy Studio detecta si scrcpy no está instalado y te ofrece un botón de **descarga automática** directamente desde GitHub Releases.

### En tu Teléfono Android

| Requisito | Detalle |
|---|---|
| **Versión de Android** | Android 5.0 (Lollipop) como mínimo |
| **Depuración USB** | **Obligatorio.** Debe estar activada en *Opciones de Desarrollador* |
| **Cable USB** | Para la conexión inicial entre el teléfono y el PC |

#### Cómo activar la Depuración USB:
1. Ve a **Ajustes -> Acerca del teléfono**.
2. Toca **"Número de compilación"** 7 veces seguidas hasta que se active el modo desarrollador.
3. Vuelve a **Ajustes -> Opciones de desarrollador**.
4. Activa la opción **"Depuración USB"**.
5. Conecta el cable USB al PC y presiona **"Permitir depuración USB"** en la pantalla del teléfono.

---

## 💻 Instalación y Uso

### Ejecutar desde el código fuente (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/zTheNea/ScrcpyGUI.git
cd ScrcpyGUI

# 2. Instalar dependencias de Python
pip install -r requirements.txt

# 3. Iniciar Scrcpy Studio (Interfaz Moderna PySide6)
python main.py

# Alternativa: Modo Legado (CustomTkinter)
python scrcpy_gui.py
```

### Ejecutar Pruebas Unitarias

```bash
python -m unittest discover tests
```

---

## 🏗️ Arquitectura del Proyecto

```
ScrcpyGUI/
├── main.py                 # Punto de entrada de Scrcpy Studio (PySide6)
├── scrcpy_gui.py           # Interfaz clásica / modo legado (CustomTkinter)
├── paths.py                # Rutas del sistema y persistencia atómica JSON
├── diagnostics.py          # Verificaciones previas pre-flight y auto-remediación
├── history_manager.py      # Historial de sesiones y estadísticas
├── config_manager.py       # Gestión segura de perfiles y configuración
├── command_builder.py      # Generador de comandos scrcpy sensible a versiones
├── presets.py              # Catálogo de presets optimizados
├── strings.py              # Textos y localización en español
├── engine/                 # Capa de infraestructura y comunicación
│   ├── __init__.py
│   └── adb.py              # ADBGateway unificado, DTOs y caché de hardware
├── ui/                     # Componentes visuales de Scrcpy Studio (Qt)
│   ├── app_window.py       # Shell de ventana principal y barra de navegación
│   ├── home.py             # Página principal con ajustes rápidos y chips
│   ├── devices.py          # Gestión avanzada de dispositivos USB y Wi-Fi
│   ├── profiles.py         # Diseñador y selector de perfiles
│   ├── recordings.py       # Gestor y reproductor de grabaciones
│   ├── settings.py         # Preferencias generales y rutas
│   ├── theme.py            # Tokens de diseño, paleta y stylesheet global
│   ├── services.py         # Pool de workers y gestión de subprocesos
│   └── widgets.py          # Componentes reutilizables (Toasts, Toggles, Cards)
└── tests/                  # Suite de pruebas unitarias (99 tests)
    ├── test_adb_gateway.py
    ├── test_command_builder.py
    ├── test_config_manager.py
    ├── test_diagnostics.py
    ├── test_history_manager.py
    ├── test_paths.py
    ├── test_preset_filtering.py
    ├── test_ui_studio.py
    └── test_ui_ux.py
```

---

## 📄 Licencia
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

*Desarrollado por [zTheNea](https://github.com/zTheNea) — Octubre 2026*
