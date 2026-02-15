from __future__ import annotations
from fastapi import APIRouter
import subprocess, os, signal

router = APIRouter()
PID_FILE = os.environ.get("BOT_PID_FILE", "./control_tower_bot.pid")

@router.post("/control/start")
def start_bot():
    if os.path.exists(PID_FILE):
        return {"ok": False, "error": "bot already running"}
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    p = subprocess.Popen(["python", "run.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
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
