from __future__ import annotations
from fastapi import APIRouter
import os, json, csv

router = APIRouter()
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
RUNS_DIR = os.environ.get("RUNS_DIR", os.path.join(_PROJECT_ROOT, "runs"))

@router.get("/runs")
def list_runs():
    if not os.path.exists(RUNS_DIR):
        return {"runs": []}
    out = []
    for d in sorted(os.listdir(RUNS_DIR)):
        p = os.path.join(RUNS_DIR, d)
        if not os.path.isdir(p) or d == "evolution":
            continue
        out.append({
            "run_id": d,
            "has_meta": os.path.exists(os.path.join(p, "run_meta.json")),
            "has_summary": os.path.exists(os.path.join(p, "performance_summary.json")),
        })
    return {"runs": out}

@router.get("/runs/{run_id}")
def get_run(run_id: str):
    p = os.path.join(RUNS_DIR, run_id)
    if not os.path.exists(p):
        return {"error": "not found"}
    meta, summ = {}, {}
    mp = os.path.join(p, "run_meta.json")
    sp = os.path.join(p, "performance_summary.json")
    if os.path.exists(mp):
        meta = json.loads(open(mp, "r", encoding="utf-8").read())
    if os.path.exists(sp):
        summ = json.loads(open(sp, "r", encoding="utf-8").read())
    return {"run_id": run_id, "meta": meta, "summary": summ}

def _read_csv(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            parsed = {}
            for k, v in row.items():
                try:
                    parsed[k] = float(v)
                except (ValueError, TypeError):
                    if v.lower() == "true":
                        parsed[k] = True
                    elif v.lower() == "false":
                        parsed[k] = False
                    else:
                        parsed[k] = v
            rows.append(parsed)
        return rows

@router.get("/runs/{run_id}/timeseries")
def get_timeseries(run_id: str):
    p = os.path.join(RUNS_DIR, run_id)
    if not os.path.exists(p):
        return {"error": "not found"}
    return {
        "equity": _read_csv(os.path.join(p, "equity_timeseries.csv")),
        "market_mid": _read_csv(os.path.join(p, "market_mid_timeseries.csv")),
        "fills": _read_csv(os.path.join(p, "paper_fills.csv")),
        "orders": _read_csv(os.path.join(p, "order_attempts.csv")),
    }
