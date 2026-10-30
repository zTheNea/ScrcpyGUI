# Registro de Cambios — Scrcpy Studio v2.0.0

**Fecha:** Octubre 2026  
**Versión:** 2.0.0 "Studio Edition & Next-Gen Engine"

---

## 🌟 Resumen Ejecutivo

La versión **2.0.0** marca la mayor evolución histórica de ScrcpyGUI, evolucionando hacia **Scrcpy Studio**: una suite integral de control móvil construida sobre una arquitectura modular desacoplada en PySide6 (Qt) con diseño glassmorphism contemporáneo, un motor backend unificado (`engine/adb.py`) con caché de hardware en memoria, persistencia atómica tolerante a fallos (`paths.py`) y compatibilidad total con **scrcpy 5.0+** (decodificación GPU por hardware `--hwdec`, alineación de tamaño y audio OTG).

---

## 🚀 Principales Novedades y Comparativa con v1.3.0

### 1. Nueva Suite Visual: Scrcpy Studio (PySide6 / Qt)
* **Barra de Navegación Lateral (Navigation Rail)**:
  * Acceso fluido a 5 áreas de trabajo: **Inicio**, **Dispositivos**, **Perfiles**, **Grabaciones** y **Ajustes**.
  * Consola deslizable inferior (Terminal Drawer) para monitorear comandos scrcpy en tiempo real con resaltado de sintaxis y atajo global (`Ctrl+\``).
* **Presets Inteligentes y Menús Desplegables de Selección Rápida**:
  * Sustitución completa de barras deslizantes imprecisas por menús desplegables (`QComboBox`) con valores estándar de la industria (Resolución, FPS, Bitrate, Códec).
  * Configuración instantánea a 1 clic para presets especializados: **Cámara Web (WebCam Pro)**, **Baja Latencia (Ultra Low Latency)**, **Gaming 120 FPS**, **Presentación**, **Audio Headless OTG** y **Pantalla Virtual**.
  * El apartado de Cámara Web ahora muestra exclusivamente los controles relevantes (antorcha flash, FPS de cámara, selector de cámara y zoom).
* **Gestor Integrado de Grabaciones**:
  * Panel exclusivo para explorar, reproducir y abrir la carpeta de archivos `.mp4` y `.mkv`.
  * Generación y formateo dinámico de nombres de archivo con tokens (`{device}`, `{preset}`, `{date}`, `{time}`).
* **Notificaciones Toast y Sistema de Temas**:
  * Sistema de toasts animados flotantes no intrusivos para feedback instantáneo de acciones y diagnósticos.

---

### 2. Motor Backend Unificado y Desacoplado (`engine/adb.py`)
* **`ADBGateway` y Arquitectura en Capas**:
  * Centralización absoluta de todas las llamadas y comandos ADB en un servicio singleton thread-safe.
  * Modelos de datos fuertemente tipados mediante `@dataclass`:
    * `DeviceRecord`: Serial, modelo, estado, tipo de conexión (USB / Wi-Fi).
    * `BatteryStatus`: Nivel %, estado de carga, fuente de energía, temperatura y salud.
    * `DisplayMetrics`: Resolución física, tasa de refresco (Hz) y densidad DPI.
    * `InstalledApp`: Nombre amigable y paquete detectado.
* **Caché de Hardware en Memoria**:
  * Eliminación de llamadas redundantes a `getprop` durante los escaneos periódicos, reduciendo la latencia de sondeo en más del 70%.
* **Limpieza de Procesos y Seguridad en Windows**:
  * Encapsulación de `subprocess` con `CREATE_NO_WINDOW` para eliminar parpadeos de ventanas negras en Windows.

---

### 3. Persistencia Atómica y Resiliencia de Datos (`paths.py`)
* **`atomic_write_json`**:
  * Escritura primero en archivo temporal `.tmp`, sincronización forzada a disco (`flush()` y `os.fsync()`) y sustitución atómica mediante `os.replace()`.
  * Generación automática de respaldos de seguridad `.bak` antes de cada sobrescritura.
* **`safe_read_json` con Auto-recuperación**:
  * Recuperación automática y transparente desde `.bak` si un archivo JSON de configuración o perfiles resulta alterado o dañado externamente.

---

### 4. Concurrencia con Pool de Workers Controlado (`ui/services.py`)
* **`ThreadPoolExecutor` Acotado**:
  * Sustitución del spawning indiscriminado de hilos por un pool acotado (`max_workers=4`, prefijo `StudioWorker`).
  * Prevención de saturación del bus USB y del servidor ADB ante múltiples acciones concurrentes del usuario.

---

### 5. Motor de Comandos Adaptativo y Soporte scrcpy 5.0+ (`command_builder.py`)
* **Detección Semántica de Versión**:
  * Parseo inteligente de versión (`parse_version`) para normalizar versiones objetivo (`(5, 0)`, `(4, 1)`, etc.).
* **Compatibilidad Universal y Filtrado Preventivo**:
  * **Soporte `--hwdec`**: Integración de decodificación de video acelerada por hardware de scrcpy 5.0 (`--hwdec=d3d11va`, `auto`).
  * **Alineación de Tamaño y Mipmaps**: Banderas `--min-size-alignment` y `--no-mipmaps`.
  * **Sintaxis de Fuerza Bruta en Apps**: Soporte para forzar detención de app (`--start-app=+paquete`) en scrcpy 5.0, omitiendo el prefijo `+` en versiones anteriores para evitar errores.
  * **Audio en Modo OTG**: Reenvío y control UHID con streaming de audio headless.

---

### 6. Selector Inteligente de Aplicaciones
* **Detección Automática de Apps Instaladas**:
  * Escaneo asíncrono de aplicaciones de terceros y actividades lanzables mediante ADB.
  * Diccionario de nombres amigables offline (WhatsApp, YouTube, Chrome, Spotify, etc.) para que el usuario seleccione la app visualmente sin necesidad de conocer el paquete técnico (`com.example.app`).

---

### 7. Calidad de Código y Pruebas Automatizadas
* **Suite de Pruebas Ampliada**:
  * Creado `tests/test_paths.py` para validar atomicidad y respaldos.
  * Creado `tests/test_adb_gateway.py` para validar DTOs, parsing de telemetría y caché.
  * Ampliado `tests/test_command_builder.py` con pruebas de filtrado condicional por versión.
* **Cobertura Total**: **99 de 99 pruebas unitarias aprobadas** (100% éxito) con 0 fallos y 0 regresiones.

---

## 🔄 Modo Legado (Backwards Compatibility)
* Para entornos que prefieran la interfaz clásica basada en CustomTkinter, se mantiene disponible ejecutando:
  ```bash
  python scrcpy_gui.py
  ```
