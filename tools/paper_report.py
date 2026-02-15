from __future__ import annotations
import csv, os, math, sys
from dataclasses import dataclass
from typing import List, Tuple

RUN_DIR = sys.argv[1] if len(sys.argv) > 1 else None
EQUITY_PATH = f"{RUN_DIR}/equity_timeseries.csv" if RUN_DIR else "./data/equity_timeseries.csv"

@dataclass
class EquityPoint: ts: float; equity: float

def read_equity(path: str) -> List[EquityPoint]:
    if not os.path.exists(path): return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try: out.append(EquityPoint(float(row["ts"]), float(row["equity"])))
            except Exception: pass
    return out

def mean_std(xs: List[float]) -> Tuple[float,float]:
    n = len(xs)
    if n < 2: return 0.0, 0.0
    m = sum(xs)/n
    v = sum((x-m)**2 for x in xs)/(n-1)
    return m, math.sqrt(v)

def max_dd(eq: List[float]) -> float:
    peak = eq[0]; maxdd = 0.0
    for e in eq:
        peak = max(peak, e)
        maxdd = max(maxdd, (peak-e)/max(peak,1e-9))
    return maxdd

def main():
    pts = read_equity(EQUITY_PATH)
    if not pts:
        print("No equity series found."); return
    eqs = [p.equity for p in pts]
    rs = [(eqs[i]/eqs[i-1]-1.0) for i in range(1,len(eqs)) if eqs[i-1]>0]
    m, s = mean_std(rs)
    sharpe = (m/s*math.sqrt(len(rs))) if s>0 else 0.0
    print("=== PAPER REPORT ===")
    print(f"Start: {eqs[0]:.2f} End: {eqs[-1]:.2f} Ret: {(eqs[-1]/eqs[0]-1.0):.2%}")
    print(f"MaxDD: {max_dd(eqs):.2%} Sharpe~: {sharpe:.2f}")
    print(f"Equity points: {len(pts)}")
if __name__ == "__main__":
    main()
