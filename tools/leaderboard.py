from __future__ import annotations
import os, json, csv

RUNS_DIR = "./runs"
OUT_CSV = "./runs/leaderboard.csv"

def load_json(p):
    try: return json.loads(open(p, "r", encoding="utf-8").read())
    except Exception: return None

def main():
    if not os.path.exists(RUNS_DIR):
        print("No runs dir."); return
    rows = []
    for d in sorted(os.listdir(RUNS_DIR)):
        p = os.path.join(RUNS_DIR, d)
        if not os.path.isdir(p) or d == "evolution":
            continue
        s = load_json(os.path.join(p, "performance_summary.json"))
        m = load_json(os.path.join(p, "run_meta.json")) or {}
        if not s: continue
        rows.append({
            "run_id": d,
            "created_at": m.get("created_at",""),
            "equity": float(s.get("equity", 0.0)),
            "fills": int(s.get("fills", 0)),
            "max_drawdown_pct": float(s.get("max_drawdown_pct", 0.0)),
            "sharpe_like": float(s.get("sharpe_like", 0.0)),
        })
    rows.sort(key=lambda r: (r["sharpe_like"], r["equity"]), reverse=True)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["run_id"])
        wtr.writeheader()
        for r in rows: wtr.writerow(r)
    print("Wrote:", OUT_CSV)
    for i, r in enumerate(rows[:10], 1):
        print(i, r["run_id"], "sharpe~", round(r["sharpe_like"],2), "equity", round(r["equity"],2))
if __name__ == "__main__":
    main()
