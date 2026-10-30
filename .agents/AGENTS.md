# Scrcpy Studio — Workspace Agent Instructions & Skill Orchestration

Este espacio de trabajo cuenta con un ecosistema de skills especializadas instaladas en `.agents/skills/`:

## 1. Skills Instaladas en el Proyecto

1. **`ui-ux-pro-max` / `consultor-senior-ui-ux`**:
   - **Propósito:** Sistema de diseño, tokens de color HSL de alto contraste (WCAG AAA), micro-interacciones Bento Grid y ergonomía visual para interfaces de escritorio modernas.
   - **Regla:** Mantener consistencia visual basada en `ui/theme.py`, bordes luminiscentes, badges de estado y diseño no intrusivo.

2. **`android-cli`**:
   - **Propósito:** Operaciones avanzadas con dispositivos Android y comandos ADB (screencaps, detección de apps, gestión de puertos inalámbricos, dumpsys y métricas de pantalla).
   - **Regla:** Toda comunicación ADB debe ser estrictamente asíncrona mediante `run_async` en `ui/services.py` para nunca bloquear el hilo de renderizado Qt.

3. **`accidental-data-loss-prevention`**:
   - **Propósito:** Prevención estricta de pérdida irreversible de datos de usuario.
   - **Regla:** Toda acción destructiva (eliminar grabaciones de disco, sobrescribir o borrar perfiles guardados, reiniciar configuraciones) debe requerir confirmación explícita mediante diálogo interactivo (`QMessageBox.question`).

4. **`managing-python-dependencies`**:
   - **Propósito:** Gestión controlada de paquetes y entornos Python.
   - **Regla:** Mantener sincronizado `requirements.txt` y la configuración de empaquetado en `ScrcpyGUI.spec` sin romper dependencias de PySide6 o bibliotecas estándar.

5. **`frontend-component-architect`**:
   - **Propósito:** Arquitectura modular de widgets y controles desacoplados en PySide6.
   - **Regla:** Mantener componentes limpios, reutilizables y con jerarquía predecible (`SettingRow`, `GoalCard`, `Toggle`, `Toast`).

6. **`frontend-state-data`**:
   - **Propósito:** Gestión reactiva del estado de la aplicación.
   - **Regla:** Utilizar el modelo de suscripción observable (`AppState`, `Var`) garantizando sincronización bidireccional entre la interfaz gráfica, el guardián de scrcpy y la persistencia en `config_manager`.

7. **`frontend-testing-qa`**:
   - **Propósito:** Aseguramiento continuo de calidad y prevención de regresiones.
   - **Regla:** Todo cambio o nueva funcionalidad debe validarse ejecutando la suite de pruebas unitarias (`python -m unittest discover tests`) garantizando 100% de tests aprobados.
