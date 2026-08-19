# Informe de Mejoras y Cambios - ScrcpyGUI v1.2.0

**Fecha:** 3 de Mayo, 2026  
**Versión:** 1.2.0 "Wireless Revolution"

---

## Resumen Ejecutivo

Este informe detalla la evolución de ScrcpyGUI hacia una suite de control profesional y automatizada. Los cambios se centran en la conectividad inalámbrica, la optimización para hardware moderno y la robustez del sistema.

---

## Cambios Técnicos y Funcionales

### 1. Módulo de Conectividad Inalámbrica
- **Implementación de `adb pair`**: Integración de la lógica de emparejamiento por código (Android 11+).
- **Automatización de IP**: Script de backend que consulta el dispositivo vía `shell ip addr` para eliminar la necesidad de que el usuario busque su IP manualmente.
- **Toggle TCP/IP**: Función directa para habilitar el puerto 5555.

### 2. Actualización de Motor de Video
- **Migración a AV1**: Configuración predeterminada de mayor calidad para dispositivos compatibles.
- **Soporte 144Hz**: Ajuste de los parámetros de `max-fps` para aprovechar pantallas de alta tasa de refresco.
- **Optimización de Audio**: Reducción de latencia en el stream de audio a 20ms mediante ajustes de buffer.

### 3. Arquitectura Adaptativa por Sistema Operativo
- **Lógica de Detección**: Implementación de `mgr.IS_WINDOWS` para adaptar la interfaz en tiempo real.
- **Restricciones Automáticas**: 
  - Ocultación de botones de descarga en Linux (se delega al gestor de paquetes).
  - Ocultación de V4L2 (Video4Linux2) en Windows para evitar errores de ejecución.

### 4. Refactorización y Estabilidad
- **Eliminación del Lanzador de Apps Antiguo**: Se retiró para priorizar la estabilidad del mirroring antes de la llegada de las pantallas virtuales.
- **Manejo de Hilos**: Todas las tareas de ADB (conectar, listar, refrescar) corren en hilos separados (`threading`), evitando que la interfaz se bloquee.
- **Gestión de Errores**: Se corrigieron errores de `ValueError` en componentes de CustomTkinter.

---

## Impacto en el Usuario

- **Configuración más rápida**: El paso de cable a Wi-Fi es asistido y automático.
- **Estabilidad**: Se han protegido las entradas de texto contra errores de tipo de dato.
- **Interfaz Limpia**: Rediseño del panel inalámbrico para una mejor jerarquía visual.
