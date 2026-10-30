---
name: frontend-state-data
description: >-
  Especialista en gestión de estado y sincronización de datos en frontend. Úsalo cuando el usuario necesite estructurar el estado global (Zustand, Redux, Pinia), manejar caché de servidor y peticiones asíncronas (TanStack Query / React Query, SWR), implementar actualizaciones optimistas (Optimistic UI) o sincronizar filtros con el estado de la URL.
---

# Frontend State & Data Synchronization (Gestión de Estado y Datos)

Esta skill define la separación rigurosa de los tipos de estado en frontend para evitar sincronizaciones redundantes, bugs de renderizado y pérdida de reactividad.

---

## 1. La Regla de Oro: Las 4 Capas del Estado

```mermaid
flowchart TD
    URL["1. URL State (Search Params, Hash, Path)"]
    Server["2. Server State (Caché de APIs, TanStack Query)"]
    Global["3. Global Client State (Zustand: Auth, Theme, Sidebar)"]
    Local["4. Local Component State (useState: Acordeón abierto, Hover)"]
```

### ¿Dónde vive cada dato?
1. **URL State (`?filter=active&page=2`):** Filtros, búsquedas, pestañas y paginación. **Debe ser compartible por enlace.**
2. **Server State:** Datos que provienen de la base de datos o API. **No los copies a un store global (Redux/Zustand)**; usa un gestor de caché (TanStack Query, SWR, RTK Query).
3. **Global Client State:** Estado efímero de la aplicación que cruza múltiples pantallas (ej. estado de sesión en cliente, modo oscuro, carrito en memoria).
4. **Local State:** Estado interno que solo le importa a ese componente específico.

---

## 2. Caché de Servidor con TanStack Query (Best Practices)

### Query Key Factory (Evita strings mágicos)
```typescript
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: UserFilters) => [...userKeys.lists(), { filters }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};
```

### Actualizaciones Optimistas (Optimistic UI Pattern)
Para dar feedback instantáneo antes de que el servidor responda:

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario
    participant UI as Componente React
    participant Cache as TanStack Query Cache
    participant API as Backend Server

    User->>UI: Clic en "Dar Like"
    UI->>Cache: 1. Cancelar queries salientes
    UI->>Cache: 2. Snapshot del valor previo (para rollback)
    UI->>Cache: 3. Actualizar UI de inmediato (+1 Like)
    UI->>API: 4. Ejecutar POST /api/likes en background
    alt Éxito
        API-->>UI: 200 OK
        UI->>Cache: Invalidar o confirmar datos reales
    else Error de red
        API-->>UI: 500 Error
        UI->>Cache: Restaurar snapshot previo (Rollback suave)
        UI->>UI: Mostrar toast de error con opción de reintento
    end
```

---

## 3. Estado Global Ligero con Zustand

Usa stores atómicos y selecciona siempre el estado mínimo para evitar re-renderizados innecesarios:

```typescript
// Correcto: Selector atómico (solo renderiza si theme cambia)
const theme = useUIStore((state) => state.theme);

// Incorrecto: Desestructurar el store completo (renderiza ante cualquier cambio)
const { theme, isSidebarOpen } = useUIStore();
```
