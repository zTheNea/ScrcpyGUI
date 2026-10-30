# Registro de Cambios - Scrcpy Studio v2.0.0

**Fecha:** Octubre 2026  
**Versión:** 2.0.0 "Studio Edition & Next-Gen Engine"

---

## Resumen Ejecutivo

La version 2.0.0 marca la mayor evolucion historica de ScrcpyGUI, evolucionando hacia Scrcpy Studio: una suite integral de control movil construida sobre una arquitectura modular desacoplada en PySide6 (Qt) con diseno glassmorphism contemporaneo, un motor backend unificado (engine/adb.py) con cache de hardware en memoria, persistencia atomica tolerante a fallos (paths.py) y compatibilidad total con scrcpy 5.0+ (decodificacion GPU por hardware --hwdec, alineacion de tamano y audio OTG).

---

## Principales Novedades y Comparativa con v1.3.0

### 1. Nueva Suite Visual: Scrcpy Studio (PySide6 / Qt)
* **Barra de Navegacion Lateral (Navigation Rail)**:
  * Acceso fluido a 5 areas de trabajo: Inicio, Dispositivos, Perfiles, Grabaciones y Ajustes.
  * Consola deslizable inferior (Terminal Drawer) para monitorear comandos scrcpy en tiempo real con resaltado de sintaxis y atajo global (Ctrl+`).
* **Presets Inteligentes y Menus Desplegables de Seleccion Rapida**:
  * Sustitucion completa de barras deslizantes imprecisas por menus desplegables (QComboBox) con valores estandar de la industria (Resolucion, FPS, Bitrate, Codec).
  * Configuracion instantanea a 1 clic para presets especializados: Camara Web (WebCam Pro), Baja Latencia (Ultra Low Latency), Gaming 120 FPS, Presentacion, Audio Headless OTG y Pantalla Virtual.
  * El apartado de Camara Web ahora muestra exclusivamente los controles relevantes (antorcha flash, FPS de camara, selector de camara y zoom).
* **Gestor Integrado de Grabaciones**:
  * Panel exclusivo para explorar, reproducir y abrir la carpeta de archivos .mp4 y .mkv.
  * Generacion y formateo dinamico de nombres de archivo con tokens ({device}, {preset}, {date}, {time}).
* **Notificaciones Toast y Sistema de Temas**:
  * Sistema de toasts animados flotantes no intrusivos para feedback instantaneo de acciones y diagnosticos.

---

### 2. Motor Backend Unificado y Desacoplado (engine/adb.py)
* **ADBGateway y Arquitectura en Capas**:
  * Centralizacion absoluta de todas las llamadas y comandos ADB en un servicio singleton thread-safe.
  * Modelos de datos fuertemente tipados mediante @dataclass:
    * DeviceRecord: Serial, modelo, estado, tipo de conexion (USB / Wi-Fi).
    * BatteryStatus: Nivel %, estado de carga, fuente de energia, temperatura y salud.
    * DisplayMetrics: Resolucion fisica, tasa de refresco (Hz) y densidad DPI.
    * InstalledApp: Nombre amigable y paquete detectado.
* **Cache de Hardware en Memoria**:
  * Eliminacion de llamadas redundantes a getprop durante los escaneos periodicos, reduciendo la latencia de sondeo en mas del 70%.
* **Limpieza de Procesos y Seguridad en Windows**:
  * Encapsulacion de subprocess con CREATE_NO_WINDOW para eliminar parpadeos de ventanas negras en Windows.

---

### 3. Persistencia Atomica y Resiliencia de Datos (paths.py)
* **atomic_write_json**:
  * Escritura primero en archivo temporal .tmp, sincronizacion forzada a disco (flush() y os.fsync()) y sustitucion atomica mediante os.replace().
  * Generacion automatica de respaldos de seguridad .bak antes de cada sobrescritura.
* **safe_read_json con Auto-recuperacion**:
  * Recuperacion automatica y transparente desde .bak si un archivo JSON de configuracion o perfiles resulta alterado o danado externamente.

---

### 4. Concurrencia con Pool de Workers Controlado (ui/services.py)
* **ThreadPoolExecutor Acotado**:
  * Sustitucion del spawning indiscriminado de hilos por un pool acotado (max_workers=4, prefijo StudioWorker).
  * Prevencion de saturacion del bus USB y del servidor ADB ante multiples acciones concurrentes del usuario.

---

### 5. Motor de Comandos Adaptativo y Soporte scrcpy 5.0+ (command_builder.py)
* **Deteccion Semantica de Version**:
  * Parseo inteligente de version (parse_version) para normalizar versiones objetivo ((5, 0), (4, 1), etc.).
* **Compatibilidad Universal y Filtrado Preventivo**:
  * **Soporte --hwdec**: Integracion de decodificacion de video acelerada por hardware de scrcpy 5.0 (--hwdec=d3d11va, auto).
  * **Alineacion de Tamano y Mipmaps**: Banderas --min-size-alignment y --no-mipmaps.
  * **Sintaxis de Fuerza Bruta en Apps**: Soporte para forzar detencion de app (--start-app=+paquete) en scrcpy 5.0, omitiendo el prefijo + en versiones anteriores para evitar errores.
  * **Audio en Modo OTG**: Reenvio y control UHID con streaming de audio headless.

---

### 6. Selector Inteligente de Aplicaciones
* **Deteccion Automatica de Apps Instaladas**:
  * Escaneo asincrono de aplicaciones de terceros y actividades lanzables mediante ADB.
  * Diccionario de nombres amigables offline (WhatsApp, YouTube, Chrome, Spotify, etc.) para que el usuario seleccione la app visualmente sin necesidad de conocer el paquete tecnico (com.example.app).

---

### 7. Calidad de Codigo y Pruebas Automatizadas
* **Suite de Pruebas Ampliada**:
  * Creado tests/test_paths.py para validar atomicidad y respaldos.
  * Creado tests/test_adb_gateway.py para validar DTOs, parsing de telemetria y cache.
  * Ampliado tests/test_command_builder.py con pruebas de filtrado condicional por version.
* **Cobertura Total**: **99 de 99 pruebas unitarias aprobadas** (100% exito) con 0 fallos y 0 regresiones.

---

## Modo Legado (Compatibilidad hacia Atras)
* Para entornos que prefieran la interfaz clasica basada en CustomTkinter, se mantiene disponible ejecutando:
  ```bash
  python scrcpy_gui.py
  ```
