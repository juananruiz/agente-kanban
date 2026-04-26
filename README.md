# Agente Kanban

Sistema local para gestionar tareas asignadas a agentes de IA mediante un tablero Kanban.

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Kanban UI  │────▶│  FastAPI     │────▶│  tasks.json  │
│  :3000      │◀────│  server.py   │◀────│              │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │  watcher.py  │
                                         │  (polling)   │
                                         └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │ dispatcher   │
                                         │  → agentes   │
                                         └──────────────┘
```

## Instalación (primera vez)

```bash
# Solo una vez: crear el entorno virtual e instalar dependencias
./setup.sh
```

Este script:
1. Crea un entorno virtual Python aislado (`venv/`)
2. Instala todas las dependencias en ese entorno

## Uso

### 1. Arrancar el servidor web (Terminal 1)

```bash
./server.sh
```

Abre http://localhost:3000 en el navegador.

### 2. Arrancar el watcher (Terminal 2)

```bash
./watcher.sh
```

El watcher vigila `tasks.json`. Cuando una tarea pasa a **TODO**, la despacha
automáticamente al agente asignado.

## Flujo de trabajo

1. Crea una tarea en el tablero (botón "Nueva tarea" o tecla `N`)
2. Asigna un agente, escribe el prompt y los archivos de contexto
3. Déjala en **Backlog** hasta que esté lista
4. Arrástrala a **Todo** cuando quieras que el agente la ejecute
5. El watcher la detecta → la mueve a **Doing** → lanza al agente
6. El resultado se guarda y la tarea pasa a **Review**
7. Tú revisas el output y la mueves a **Done**

## Columnas

| Columna  | Significado                         |
|----------|-------------------------------------|
| Backlog  | Ideas y tareas pendientes de definir |
| Todo     | Lista para ejecutar (dispara el agente) |
| Doing    | El agente está trabajando            |
| Review   | Completada, pendiente de revisión    |
| Done     | Revisada y cerrada                   |

## Agentes disponibles

| Agente         | Invocación               | Uso típico                     |
|----------------|--------------------------|--------------------------------|
| claude-code    | `claude -p "..."`        | Código, refactoring, archivos  |
| claude-api     | SDK Python de Anthropic  | Texto, análisis, redacción     |
| custom-script  | `python script.py`       | Flujos específicos             |
| copilot        | CLI / extensión          | Edición asistida de código     |
| script         | bash / python            | Automatización sin IA          |

## Configurar agentes reales

Edita `dispatcher.py` y descomenta las líneas de ejecución real en cada
función `_run_*`. En el prototipo todo funciona en modo simulación.

## Atajos de teclado

- `N` — Nueva tarea
- `Esc` — Cerrar modal
- Doble clic en tarjeta — Editar

## .gitignore

Si versiona tu proyecto con Git, ignora estas carpetas:

```
venv/
__pycache__/
*.pyc
.DS_Store
```
