"""
Agente Kanban — Dispatcher
Enruta cada tarea al agente correcto y gestiona su ciclo de vida.
"""

import json
import subprocess
import shlex
from pathlib import Path
from datetime import datetime

# Importa o define aquí tus clientes de API si los necesitas
# from anthropic import Anthropic


def dispatch(task: dict, tasks_file: Path) -> dict:
    """
    Ejecuta la tarea con el agente asignado.
    Devuelve la tarea actualizada con output/error.
    """
    agent = task.get("agent", "")
    prompt = task.get("prompt", "")
    context_files = task.get("context_files", [])

    print(f"  🚀 Dispatching [{task['id']}] → {agent}")
    print(f"     Título: {task['title']}")
    print(f"     Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    # ── Marcar como DOING ───────────────────────────────
    task["status"] = "DOING"
    task["updated"] = datetime.now().isoformat()
    _save_task(task, tasks_file)

    try:
        if agent == "claude-code":
            result = _run_claude_code(prompt, context_files)
        elif agent == "claude-api":
            result = _run_claude_api(prompt, context_files)
        elif agent == "custom-script":
            result = _run_custom_script(task)
        elif agent == "copilot":
            result = _run_copilot(prompt, context_files)
        elif agent == "script":
            result = _run_script(task)
        else:
            result = f"⚠️ Agente desconocido: {agent}"

        task["output"] = result
        task["status"] = "REVIEW"
        task["error"] = None
        print(f"  ✅ Completada [{task['id']}]")

    except Exception as e:
        task["error"] = str(e)
        task["status"] = "REVIEW"
        task["output"] = None
        print(f"  ❌ Error [{task['id']}]: {e}")

    task["updated"] = datetime.now().isoformat()
    _save_task(task, tasks_file)
    return task


# ── Agentes ─────────────────────────────────────────────

def _run_claude_code(prompt: str, context_files: list[str]) -> str:
    """Invoca Claude Code CLI."""
    files_arg = " ".join(shlex.quote(f) for f in context_files)
    cmd = f'claude -p {shlex.quote(prompt)} {files_arg}'.strip()
    print(f"     $ {cmd}")

    # ⚠️ PROTOTIPO: descomentar para ejecución real
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    # if result.returncode != 0:
    #     raise RuntimeError(f"Claude Code falló: {result.stderr}")
    # return result.stdout

    return f"[SIMULACIÓN] Claude Code ejecutaría: {cmd}"


def _run_claude_api(prompt: str, context_files: list[str]) -> str:
    """Llama a la API de Anthropic directamente."""
    # ⚠️ PROTOTIPO: descomentar para ejecución real
    # client = Anthropic()
    # context = ""
    # for f in context_files:
    #     p = Path(f)
    #     if p.exists():
    #         context += f"\n--- {f} ---\n{p.read_text()}\n"
    # message = client.messages.create(
    #     model="claude-sonnet-4-20250514",
    #     max_tokens=4096,
    #     messages=[{"role": "user", "content": f"{prompt}\n\nContexto:\n{context}"}]
    # )
    # return message.content[0].text

    return f"[SIMULACIÓN] Claude API procesaría el prompt con {len(context_files)} archivo(s) de contexto"


def _run_custom_script(task: dict) -> str:
    """Ejecuta un script Python personalizado."""
    script = task.get("agent_script", "")
    if not script:
        return "[SIMULACIÓN] No se definió agent_script en la tarea"

    # cmd = f"python {shlex.quote(script)} --task-id {shlex.quote(task['id'])}"
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
    # return result.stdout

    return f"[SIMULACIÓN] Ejecutaría: python {script} --task-id {task['id']}"


def _run_copilot(prompt: str, context_files: list[str]) -> str:
    """Placeholder para Copilot/Cursor CLI."""
    return f"[SIMULACIÓN] Copilot procesaría: {prompt[:100]}"


def _run_script(task: dict) -> str:
    """Ejecuta un script bash/python sin IA."""
    script = task.get("agent_script", "")
    if not script:
        return "[SIMULACIÓN] No se definió agent_script en la tarea"

    # result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=300)
    # return result.stdout

    return f"[SIMULACIÓN] Ejecutaría: {script}"


# ── Utilidades ──────────────────────────────────────────

def _save_task(task: dict, tasks_file: Path):
    """Actualiza una tarea concreta en el archivo JSON."""
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    for i, t in enumerate(tasks):
        if t["id"] == task["id"]:
            tasks[i] = task
            break

    with open(tasks_file, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
