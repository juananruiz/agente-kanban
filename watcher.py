"""
Agente Kanban — Watcher (Enfoque B)
Vigila tasks.json y despacha automáticamente las tareas que pasan a TODO.

Uso:
    python watcher.py

El watcher:
  1. Lee tasks.json periódicamente (polling cada 2 segundos)
  2. Detecta tareas con status "TODO"
  3. Las envía al dispatcher
  4. El dispatcher las mueve a DOING → DONE/REVIEW

También soporta watchdog para detección por eventos del filesystem
(más eficiente, menos polling). Instala: pip install watchdog
"""

import json
import time
import sys
import hashlib
from pathlib import Path
from datetime import datetime

from dispatcher import dispatch

# ── Config ──────────────────────────────────────────────

TASKS_FILE = Path(__file__).parent / "tasks.json"
HEARTBEAT_FILE = Path(__file__).parent / ".watcher_heartbeat"
POLL_INTERVAL = 2  # segundos entre comprobaciones
USE_WATCHDOG = False  # cambiar a True si tienes watchdog instalado

# ── Estado interno ──────────────────────────────────────

_last_hash = None
_dispatching = set()  # IDs de tareas en proceso


def _write_heartbeat():
    HEARTBEAT_FILE.write_text(datetime.now().isoformat())


def _file_hash() -> str:
    """Hash rápido del contenido del archivo para detectar cambios."""
    content = TASKS_FILE.read_bytes()
    return hashlib.md5(content).hexdigest()


def _load_tasks() -> list[dict]:
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _check_and_dispatch():
    """Busca tareas en TODO y las despacha."""
    global _last_hash

    _write_heartbeat()
    current_hash = _file_hash()
    if current_hash == _last_hash:
        return  # sin cambios
    _last_hash = current_hash

    tasks = _load_tasks()
    todo_tasks = [
        t for t in tasks
        if t["status"] == "TODO" and t["id"] not in _dispatching
    ]

    for task in todo_tasks:
        _dispatching.add(task["id"])
        print(f"\n{'─' * 50}")
        print(f"  📋 Nueva tarea detectada en TODO:")
        print(f"     {task['title']}")
        print(f"     Agente: {task['agent']}")
        print(f"     Prioridad: {task['priority']}")
        print(f"{'─' * 50}")

        try:
            dispatch(task, TASKS_FILE)
        finally:
            _dispatching.discard(task["id"])


# ── Modo Polling ────────────────────────────────────────

def run_polling():
    """Polling simple: comprueba el archivo cada N segundos."""
    global _last_hash
    _last_hash = _file_hash()
    _write_heartbeat()

    print(f"  👁️  Watcher activo (polling cada {POLL_INTERVAL}s)")
    print(f"     Vigilando: {TASKS_FILE.resolve()}")
    print(f"     Esperando tareas en columna TODO...\n")

    try:
        while True:
            _check_and_dispatch()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n  🛑 Watcher detenido.\n")


# ── Modo Watchdog ───────────────────────────────────────

def run_watchdog():
    """Usa watchdog para detectar cambios por eventos del filesystem."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("  ⚠️  watchdog no instalado. Usando polling.")
        print("     Instala con: pip install watchdog\n")
        return run_polling()

    class TaskFileHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if Path(event.src_path).name == "tasks.json":
                _check_and_dispatch()

    observer = Observer()
    observer.schedule(TaskFileHandler(), str(TASKS_FILE.parent), recursive=False)
    observer.start()

    print(f"  👁️  Watcher activo (watchdog — eventos del filesystem)")
    print(f"     Vigilando: {TASKS_FILE.resolve()}")
    print(f"     Esperando tareas en columna TODO...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n  🛑 Watcher detenido.\n")
    observer.join()


# ── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  ┌────────────────────────────────────┐")
    print("  │   🗂️  Agente Kanban — Watcher       │")
    print("  └────────────────────────────────────┘\n")

    if USE_WATCHDOG:
        run_watchdog()
    else:
        run_polling()
