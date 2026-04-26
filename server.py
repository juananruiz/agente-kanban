"""
Agente Kanban — Servidor FastAPI
Sirve la UI y expone la API REST para gestionar tareas.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

# ── Config ──────────────────────────────────────────────
TASKS_FILE = Path(__file__).parent / "tasks.json"
HEARTBEAT_FILE = Path(__file__).parent / ".watcher_heartbeat"
WATCHER_TIMEOUT = 5  # segundos sin heartbeat → watcher inactivo
VALID_STATUSES = ["BACKLOG", "TODO", "DOING", "DONE", "REVIEW"]
VALID_AGENTS = ["claude-code", "claude-api", "custom-script", "copilot", "script"]
VALID_PRIORITIES = ["alta", "media", "baja"]

# ── Helpers ─────────────────────────────────────────────

def load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks: list[dict]):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


# ── App ─────────────────────────────────────────────────

app = FastAPI(title="Agente Kanban", version="0.1.0")

# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent / "static" / "index.html")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


# ── Models ──────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    agent: str = "claude-code"
    prompt: str = ""
    context_files: list[str] = []
    priority: str = "media"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    agent: Optional[str] = None
    prompt: Optional[str] = None
    context_files: Optional[list[str]] = None
    priority: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None


class TaskReorder(BaseModel):
    task_id: str
    new_status: str
    position: int = -1  # -1 = append at end


# ── API Endpoints ───────────────────────────────────────

@app.get("/api/tasks")
async def get_tasks():
    return load_tasks()


@app.post("/api/tasks")
async def create_task(data: TaskCreate):
    tasks = load_tasks()
    task = {
        "id": f"task-{uuid.uuid4().hex[:6]}",
        "title": data.title,
        "description": data.description,
        "status": "BACKLOG",
        "agent": data.agent,
        "prompt": data.prompt,
        "context_files": data.context_files,
        "priority": data.priority,
        "created": datetime.now().isoformat(),
        "updated": None,
        "output": None,
        "error": None,
    }
    tasks.append(task)
    save_tasks(tasks)
    return task


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, data: TaskUpdate):
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(404, "Tarea no encontrada")

    update_data = data.model_dump(exclude_none=True)
    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(400, f"Estado inválido. Usa: {VALID_STATUSES}")

    task.update(update_data)
    task["updated"] = datetime.now().isoformat()
    save_tasks(tasks)
    return task


@app.put("/api/tasks/{task_id}/move")
async def move_task(task_id: str, data: TaskReorder):
    """Move a task to a new status column (triggered by drag & drop)."""
    tasks = load_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(404, "Tarea no encontrada")
    if data.new_status not in VALID_STATUSES:
        raise HTTPException(400, f"Estado inválido. Usa: {VALID_STATUSES}")

    old_status = task["status"]
    task["status"] = data.new_status
    task["updated"] = datetime.now().isoformat()
    save_tasks(tasks)

    return {
        "task": task,
        "moved": old_status != data.new_status,
        "from": old_status,
        "to": data.new_status,
    }


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return {"deleted": task_id}


@app.get("/api/watcher/status")
async def watcher_status():
    if not HEARTBEAT_FILE.exists():
        return {"active": False}
    age = (datetime.now() - datetime.fromtimestamp(HEARTBEAT_FILE.stat().st_mtime)).total_seconds()
    return {"active": age < WATCHER_TIMEOUT}


@app.get("/api/agents")
async def get_agents():
    """List available agents for the UI dropdown."""
    return [
        {"id": "claude-code", "name": "Claude Code", "icon": "terminal", "description": "Código, refactoring, generación de archivos"},
        {"id": "claude-api", "name": "Claude API", "icon": "cpu", "description": "Texto, análisis, redacción"},
        {"id": "custom-script", "name": "Script custom", "icon": "file-code", "description": "Python/bash específico"},
        {"id": "copilot", "name": "Copilot / Cursor", "icon": "edit", "description": "Edición asistida de código"},
        {"id": "script", "name": "Script sin IA", "icon": "play", "description": "Automatización pura"},
    ]


# ── Run ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n  🗂️  Agente Kanban → http://localhost:3000\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
