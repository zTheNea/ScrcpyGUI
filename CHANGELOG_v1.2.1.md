# Informe de Mejoras y Cambios - ScrcpyGUI v1.2.1
**Fecha:** 5 de Julio, 2026  
**Versión:** 1.2.1 "Refactor & Polish"

## 📝 Resumen Ejecutivo
Esta versión se enfoca en la estabilización, refactorización de arquitectura para hacer el código más mantenible y testeable, y la corrección de errores reportados tras el lanzamiento de la versión 1.2.0.

---

## 🌟 Nuevas Características y Mejoras
- **Refactorización de la arquitectura**: Se extrajeron los presets, colores y constantes a `presets.py`.
- **Desacoplamiento de lógica**: La lógica de construcción de comandos de scrcpy fue desacoplada a una función pura sin dependencias de GUI (`command_builder.py`).
- **Persistencia de estado**: El GUI ahora recuerda y restaura el preset visualmente seleccionado al iniciar la aplicación.
- **Manejo seguro de configuración**: Manejo de archivos de configuración corruptos con creación automática de respaldos (`.bak`).
- **Feedback visual mejorado**: Al detener scrcpy, el botón de inicio muestra un indicador de éxito temporal (✅ Terminado).

---

## 🐛 Correcciones de Bugs
- Eliminado un fallo crítico que duplicaba el argumento `--keep-active`, causando errores de ejecución en scrcpy.
- Se limpiaron variables de estado huérfanas en memoria relacionadas con la cámara que ya no se usaban (`v_camera_size`, `v_camera_ar`, etc.).
- Corregida la actualización de la ruta del directorio ejecutable tras descargar una actualización, garantizando que el nuevo ejecutable se use inmediatamente sin reiniciar la app.
- Reemplazada la etiqueta incorrecta del preset *"ultra"* por *"compatible"*.
- Validación numérica segura (`_safe_int`) implementada para evitar cuelgues si el usuario introduce texto en campos exclusivamente numéricos de la configuración personalizada.
