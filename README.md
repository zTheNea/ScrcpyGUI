# Scrcpy Studio v2.0.0 (ScrcpyGUI)

> [!IMPORTANT]
> **Aviso Legal / Disclaimer**: Scrcpy Studio es una interfaz grafica (GUI) independiente y no oficial disenada para facilitar el uso de [scrcpy](https://github.com/Genymobile/scrcpy). Este proyecto es un **complemento** y no esta afiliado, asociado ni respaldado por **Genymobile** ni por los desarrolladores originales de scrcpy. Todas las marcas comerciales y el motor de streaming pertenecen a sus respectivos duenos.

Una suite visual profesional, moderna y optimizada para la gestion, control y transmision de dispositivos Android mediante `scrcpy`. Disenada con una arquitectura desacoplada en PySide6 (Qt) con estetica glassmorphism contemporanea, motor backend unificado (`engine/adb.py`) con telemetria en tiempo real y soporte integral para **scrcpy 5.0+**.

---

## Novedades de la Version 2.0.0

* **Nueva Suite Scrcpy Studio (PySide6)**:
  * **Navigation Rail** moderno con vistas modulares: **Inicio**, **Dispositivos**, **Perfiles**, **Grabaciones** y **Ajustes**.
  * **Ajustes Rapidos con Menus Desplegables**: Reemplazo de barras deslizantes imprecisas por selectores desplegables con valores estandar (Resolucion, FPS, Bitrate, Codec).
  * **Presets Inteligentes a 1 Clic**: Presets preconfigurados y validados por hardware (Webcam Pro, Ultra Baja Latencia, Gaming 120 FPS, Pantalla Virtual y Audio OTG).
  * **Apartado de Camara Especializado**: La seccion de camara web adapta los controles exclusivamente para la captura de video (antorcha flash, zoom y orientacion).
* **Motor Backend Unificado (`engine/adb.py`)**:
  * Gateway singleton thread-safe con DTOs fuertemente tipados (`DeviceRecord`, `BatteryStatus`, `DisplayMetrics`, `InstalledApp`).
  * Cache de propiedades de hardware en memoria que reduce la latencia de escaneo en mas del 70%.
* **Persistencia Atomica y Resiliente (`paths.py`)**:
  * Escritura atomica (`atomic_write_json`) con `fsync` y reemplazo atomico `os.replace` para evitar archivos truncados.
  * Respaldos automaticos `.bak` y auto-recuperacion transparente ante archivos danados.
* **Pool de Workers Controlado (`ui/services.py`)**:
  * Concurrencia acotada con `ThreadPoolExecutor(max_workers=4)` que previene la saturacion del bus USB y del servidor ADB.
* **Compatibilidad Total con Scrcpy 5.0+**:
  * Decodificacion de video por hardware en GPU (`--hwdec=d3d11va`, `auto`).
  * Alineacion de dimensiones (`--min-size-alignment`) y desactivacion de mipmaps (`--no-mipmaps`).
  * Sintaxis de forzado de apps (`--start-app=+pkg`) condicional a la version detectada.
* **Selector Inteligente de Aplicaciones**:
  * Escaneo automatico de apps instaladas con resolucion de nombres amigables offline sin requerir paquetes manuales.
* **Gestor de Grabaciones**:
  * Explorador de archivos de video grabados con reproduccion directa y acceso a directorio.
* **99 Tests Automatizados**:
  * Suite de pruebas unitarias cubriendo DTOs, versionado, persistencia y gateways.

---

## Requisitos Previos

### En tu PC (Windows / Linux / macOS)

| Requisito | Detalle |
|---|---|
| **Sistema Operativo** | Windows 10/11 (64-bit), Linux o macOS |
| **Python** | Python 3.10 o superior ([python.org](https://www.python.org/downloads/)) |
| **pip** | Viene incluido con Python. Se usa para instalar dependencias |
| **scrcpy** | Se descarga automaticamente desde la app, o puedes instalarlo manualmente desde [github.com/Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) |
| **ADB (Android Debug Bridge)** | Incluido automaticamente con scrcpy en Windows. En Linux/macOS, instalalo con tu gestor de paquetes (`sudo apt install adb` / `brew install android-platform-tools`) |
| **Cable USB** | Necesario para la conexion inicial. Posteriormente puedes conectar por Wi-Fi |

> [!TIP]
> **No tienes scrcpy?** Scrcpy Studio detecta si scrcpy no esta instalado y te ofrece un boton de **descarga automatica** directamente desde GitHub Releases.

### En tu Telefono Android

| Requisito | Detalle |
|---|---|
| **Version de Android** | Android 5.0 (Lollipop) como minimo |
| **Depuracion USB** | **Obligatorio.** Debe estar activada en *Opciones de Desarrollador* |
| **Cable USB** | Para la conexion inicial entre el telefono y el PC |

#### Como activar la Depuracion USB:
1. Ve a **Ajustes -> Acerca del telefono**.
2. Toca **"Numero de compilacion"** 7 veces seguidas hasta que se active el modo desarrollador.
3. Vuelve a **Ajustes -> Opciones de desarrollador**.
4. Activa la opcion **"Depuracion USB"**.
5. Conecta el cable USB al PC y presiona **"Permitir depuracion USB"** en la pantalla del telefono.

---

## Instalacion y Uso

### Ejecutar desde el codigo fuente (Recomendado)

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

## Arquitectura del Proyecto

```
ScrcpyGUI/
├── main.py                 # Punto de entrada de Scrcpy Studio (PySide6)
├── scrcpy_gui.py           # Interfaz clasica / modo legado (CustomTkinter)
├── paths.py                # Rutas del sistema y persistencia atomica JSON
├── diagnostics.py          # Verificaciones previas pre-flight y auto-remediacion
├── history_manager.py      # Historial de sesiones y estadisticas
├── config_manager.py       # Gestion segura de perfiles y configuracion
├── command_builder.py      # Generador de comandos scrcpy sensible a versiones
├── presets.py              # Catalogo de presets optimizados
├── strings.py              # Textos y localizacion en espanol
├── engine/                 # Capa de infraestructura y comunicacion
│   ├── __init__.py
│   └── adb.py              # ADBGateway unificado, DTOs y cache de hardware
├── ui/                     # Componentes visuales de Scrcpy Studio (Qt)
│   ├── app_window.py       # Shell de ventana principal y barra de navegacion
│   ├── home.py             # Pagina principal con ajustes rapidos y chips
│   ├── devices.py          # Gestion avanzada de dispositivos USB y Wi-Fi
│   ├── profiles.py         # Disenador y selector de perfiles
│   ├── recordings.py       # Gestor y reproductor de grabaciones
│   ├── settings.py         # Preferencias generales y rutas
│   ├── theme.py            # Tokens de diseno, paleta y stylesheet global
│   ├── services.py         # Pool de workers y gestion de subprocesos
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

## Licencia
Este proyecto esta bajo la Licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para mas detalles.

*Desarrollado por [zTheNea](https://github.com/zTheNea) - Octubre 2026*
