from __future__ import annotations
from fastapi import APIRouter
import subprocess, os, signal, sys

router = APIRouter()
PID_FILE = os.environ.get("BOT_PID_FILE", "./control_tower_bot.pid")

@router.post("/control/start")
def start_bot():
    if os.path.exists(PID_FILE):
        return {"ok": False, "error": "bot already running"}

    # Get the project root directory (two levels up from control_tower/backend)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    p = subprocess.Popen(
        [sys.executable, "run.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=project_root
    )
    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(p.pid))
    return {"ok": True, "pid": p.pid}

@router.post("/control/stop")
def stop_bot():
    if not os.path.exists(PID_FILE):
        return {"ok": False, "error": "no pid file"}
    pid = int(open(PID_FILE, "r", encoding="utf-8").read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    try:
        os.remove(PID_FILE)
    except Exception:
        pass
    return {"ok": True, "pid": pid}

@router.get("/control/status")
def bot_status():
    if not os.path.exists(PID_FILE):
        return {"running": False, "pid": None}
    pid = int(open(PID_FILE, "r", encoding="utf-8").read().strip())
    try:
        os.kill(pid, 0)
        return {"running": True, "pid": pid}
    except OSError:
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
        return {"running": False, "pid": None}
