from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import csv, os, math

@dataclass
class SliceStats:
    start_ts: float
    end_ts: float
    points: int
    equity_start: float
    equity_end: float
    total_return: float
    max_drawdown: float
    sharpe_like: float
    sharpe_low: float
    sharpe_high: float
    points_low: int
    points_high: int
    regime_ok: bool

def _mean_std(xs: List[float]) -> Tuple[float,float]:
    n = len(xs)
    if n < 2: return 0.0, 0.0
    m = sum(xs)/n
    v = sum((x-m)**2 for x in xs)/(n-1)
    return m, math.sqrt(v)

def _max_dd(eq: List[float]) -> float:
    peak = eq[0]; maxdd = 0.0
    for e in eq:
        peak = max(peak, e)
        maxdd = max(maxdd, (peak-e)/max(peak,1e-9))
    return maxdd

def _regime_split(returns: List[float], vol_window: int, high_thr: float):
    low, high = [], []
    roll = []
    for r in returns:
        roll.append(r)
        if len(roll) > vol_window: roll.pop(0)
        if len(roll) < max(10, vol_window//3):
            low.append(r); continue
        mu = sum(roll)/len(roll)
        var = sum((x-mu)**2 for x in roll)/max(1,(len(roll)-1))
        s = math.sqrt(var)
        (high if s >= high_thr else low).append(r)
    return low, high

def compute_slice_stats(equity_csv_path: str, *, start_idx: int, end_idx: int, vol_window_points: int = 60, high_vol_threshold: float = 0.0015, min_points_each: int = 60) -> Optional[SliceStats]:
    if not os.path.exists(equity_csv_path): return None
    rows = []
    with open(equity_csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try: rows.append((float(row["ts"]), float(row["equity"])))
            except Exception: pass
    if len(rows) < 10: return None
    start_idx = max(0, start_idx); end_idx = min(len(rows), end_idx)
    if end_idx - start_idx < 10: return None
    sl = rows[start_idx:end_idx]
    ts = [x[0] for x in sl]; eq = [x[1] for x in sl]
    returns = [(eq[i]/eq[i-1]-1.0) for i in range(1,len(eq)) if eq[i-1]>0]
    m, s = _mean_std(returns)
    sharpe_like = (m/s*math.sqrt(len(returns))) if s>0 else 0.0
    low_r, high_r = _regime_split(returns, vol_window_points, high_vol_threshold)
    ml, sl_ = _mean_std(low_r); mh, sh_ = _mean_std(high_r)
    sharpe_low = (ml/sl_*math.sqrt(len(low_r))) if sl_>0 else 0.0
    sharpe_high = (mh/sh_*math.sqrt(len(high_r))) if sh_>0 else 0.0
    regime_ok = len(low_r) >= min_points_each and len(high_r) >= min_points_each
    total_ret = (eq[-1]/eq[0]-1.0) if eq[0]>0 else 0.0
    return SliceStats(ts[0], ts[-1], len(eq), eq[0], eq[-1], total_ret, _max_dd(eq), sharpe_like, sharpe_low, sharpe_high, len(low_r), len(high_r), regime_ok)
