from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import csv, os, math

@dataclass(frozen=True)
class FoldWindow:
    start_idx: int
    end_idx: int
    points: int
    high_frac: float
    vol_mean: float

def _rolling_vol(xs: List[float], window: int) -> List[float]:
    out = [0.0]*len(xs)
    roll = []
    for i, x in enumerate(xs):
        roll.append(x)
        if len(roll) > window:
            roll.pop(0)
        if len(roll) < max(10, window//3):
            out[i] = 0.0
            continue
        mu = sum(roll)/len(roll)
        var = sum((r-mu)**2 for r in roll)/max(1,(len(roll)-1))
        out[i] = math.sqrt(var)
    return out

def select_market_vol_balanced_folds(market_mid_csv: str, *, folds: int, min_fold_points: int, min_high_frac: float, max_overlap_frac: float, candidate_stride_points: int, candidates_per_fold: int, vol_window_points: int, high_vol_threshold: float) -> List[FoldWindow]:
    if not os.path.exists(market_mid_csv):
        return []
    mids = []
    with open(market_mid_csv, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try: mids.append(float(row["mid"]))
            except Exception: pass
    if len(mids) < min_fold_points*2:
        return []
    rets = [(mids[i]/mids[i-1]-1.0) for i in range(1,len(mids)) if mids[i-1] > 0]
    vols = _rolling_vol(rets, vol_window_points)
    vols = [0.0] + vols  # align to mids length

    windows: List[FoldWindow] = []
    used: List[Tuple[int,int]] = []

    def overlap(a: Tuple[int,int], b: Tuple[int,int]) -> float:
        s1,e1=a; s2,e2=b
        inter = max(0, min(e1,e2)-max(s1,s2))
        return inter / max(1, min(e1-s1, e2-s2))

    L = len(mids)
    for _ in range(folds):
        best: Optional[FoldWindow] = None
        attempts = 0
        for start in range(0, L-min_fold_points, candidate_stride_points):
            end = start + min_fold_points
            if end > L: break
            attempts += 1
            if attempts > candidates_per_fold: break
            vol_slice = vols[start:end]
            high = sum(1 for v in vol_slice if v >= high_vol_threshold)
            high_frac = high / max(1, len(vol_slice))
            if high_frac < min_high_frac:
                continue
            vmean = sum(vol_slice)/max(1,len(vol_slice))
            cand = FoldWindow(start, end, end-start, high_frac, vmean)
            if any(overlap((start,end), u) > max_overlap_frac for u in used):
                continue
            if best is None or (cand.high_frac > best.high_frac) or (cand.high_frac == best.high_frac and cand.vol_mean > best.vol_mean):
                best = cand
        if best is None:
            break
        windows.append(best)
        used.append((best.start_idx, best.end_idx))
    return windows
