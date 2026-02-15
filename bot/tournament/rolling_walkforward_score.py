from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import os, json
from bot.tournament.walkforward_stats import compute_slice_stats
from bot.tournament.market_vol_folds import select_market_vol_balanced_folds, FoldWindow
from bot.tournament.evolution_score import compute_score, Score

@dataclass
class FoldResult:
    fold_idx: int
    start_idx: int
    end_idx: int
    ok: bool
    score: float
    reason: str

@dataclass
class RollingWFResult:
    ok: bool
    score: float
    reason: str
    folds: List[FoldResult]

def rolling_walkforward_score(*, run_dir: str, summary: Dict[str, Any], objective: Dict[str, float], constraints: Dict[str, Any], wf_cfg: Dict[str, Any], perf_regime_cfg: Dict[str, Any]) -> RollingWFResult:
    equity_csv = os.path.join(run_dir, "equity_timeseries.csv")
    market_mid_csv = os.path.join(run_dir, wf_cfg.get("market_mid_csv_name", "market_mid_timeseries.csv"))
    folds = int(wf_cfg.get("folds", 4))
    min_fold_minutes = float(wf_cfg.get("min_fold_minutes", 1))
    # rough: 5 logs/sec in mock, but we keep it simple and require 30 points per minute
    min_fold_points = max(30, int(min_fold_minutes * 30))

    use_vol_balanced = bool(wf_cfg.get("market_vol_balanced_folds", True))
    windows: List[FoldWindow] = []
    if use_vol_balanced:
        windows = select_market_vol_balanced_folds(
            market_mid_csv,
            folds=folds,
            min_fold_points=min_fold_points,
            min_high_frac=float(wf_cfg.get("min_high_frac", 0.2)),
            max_overlap_frac=float(wf_cfg.get("max_overlap_frac", 0.35)),
            candidate_stride_points=int(wf_cfg.get("candidate_stride_points", 10)),
            candidates_per_fold=int(wf_cfg.get("candidates_per_fold", 200)),
            vol_window_points=int(wf_cfg.get("market_vol_window_points", 60)),
            high_vol_threshold=float(wf_cfg.get("market_high_vol_threshold", 0.0015)),
        )
    if not windows:
        # fallback single window: last min_fold_points
        windows = [FoldWindow(max(0, 0), max(0, min_fold_points), min_fold_points, 0.0, 0.0)]

    fold_results: List[FoldResult] = []
    for i, win in enumerate(windows):
        st = compute_slice_stats(
            equity_csv,
            start_idx=win.start_idx,
            end_idx=win.end_idx,
            vol_window_points=int(perf_regime_cfg.get("vol_window_points", 60)),
            high_vol_threshold=float(perf_regime_cfg.get("high_vol_threshold", 0.0015)),
            min_points_each=int(perf_regime_cfg.get("min_points_each", 60)),
        )
        if not st:
            fold_results.append(FoldResult(i, win.start_idx, win.end_idx, False, -1e9, "no_stats"))
            continue
        fold_summary = {
            "equity": st.equity_end,
            "fills": summary.get("fills", 0),
            "max_drawdown_pct": st.max_drawdown,
            "sharpe_like": st.sharpe_like,
            "sharpe_low": st.sharpe_low,
            "sharpe_high": st.sharpe_high,
            "points_low": st.points_low,
            "points_high": st.points_high,
            "regime_ok": st.regime_ok,
        }
        sc: Score = compute_score(fold_summary, objective, constraints)
        fold_results.append(FoldResult(i, win.start_idx, win.end_idx, sc.ok, sc.value, sc.reason))

    ok_folds = [f for f in fold_results if f.ok]
    if not ok_folds:
        return RollingWFResult(False, -1e9, "no_ok_folds", fold_results)

    avg_score = sum(f.score for f in ok_folds)/len(ok_folds)
    # instability penalty
    if len(ok_folds) >= 2:
        m = avg_score
        var = sum((f.score-m)**2 for f in ok_folds)/(len(ok_folds)-1)
        std = var**0.5
        avg_score -= float(wf_cfg.get("instability_penalty", 0.4)) * std
    return RollingWFResult(True, avg_score, "ok", fold_results)
