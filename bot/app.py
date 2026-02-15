from __future__ import annotations
import asyncio, time, os
from typing import Dict, Any
from bot.types import TopOfBook, OrderIntent
from bot.paper.run_manager import RunManager
from bot.paper.broker import PaperBroker
from bot.paper.attempts import AttemptLogger
from bot.paper.performance import PerformanceTracker
from bot.paper.ws_l2_book import WSL2BookStore
from bot.paper.microstructure import MicrostructureTracker
from bot.paper.advsel import AdvSelConfig, compute_advsel_penalty
from bot.paper.latency_profiles import RegionLatency, LatencyProfile
from bot.paper.market_vol_logger import MarketVolLogger

class KillSwitch:
    def __init__(self): self.tripped = False; self.reason = ""
    def trip(self, reason: str): self.tripped = True; self.reason = reason

class App:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.ks = KillSwitch()
        self.tob: Dict[str, TopOfBook] = {}
        # MVP uses mock "market tokens"
        self.token_a = "MARKET_A"
        self.token_b = "MARKET_B"

        pruns = cfg.get("paper", {}).get("runs", {})
        self.run_paths = None
        if pruns.get("enabled", True):
            rm = RunManager(base_dir=str(pruns.get("base_dir", "./runs")))
            self.run_paths = rm.start_run(
                tag=str(pruns.get("tag", "paper")),
                pair={"a": self.token_a, "b": self.token_b},
                cfg={"paper": cfg.get("paper", {}), "dependency": cfg.get("dependency", {})},
            )

        fills_path = self.run_paths.fills_csv if self.run_paths else "./data/paper_fills.csv"
        attempts_path = self.run_paths.attempts_csv if self.run_paths else "./data/order_attempts.csv"
        equity_path = self.run_paths.equity_csv if self.run_paths else "./data/equity_timeseries.csv"
        summary_path = self.run_paths.summary_json if self.run_paths else "./data/performance_summary.json"

        pcfg = cfg.get("paper", {})
        self.paper = PaperBroker(
            starting_cash_usd=float(pcfg.get("starting_cash_usd", 1000.0)),
            fee_bps=float(pcfg.get("fee_bps", 0.0)),
            slippage_bps=float(pcfg.get("slippage_bps", 5.0)),
            mark_method=str(pcfg.get("mark_method", "mid")),
            save_fills_csv=True,
            fills_csv_path=fills_path,
        )
        self.attempts = AttemptLogger(attempts_path)

        perf_cfg = pcfg.get("performance", {})
        reg = perf_cfg.get("regime", {})
        self.perf = PerformanceTracker(
            equity_csv_path=equity_path,
            summary_json_path=summary_path,
            returns_window_points=int(perf_cfg.get("returns_window_points", 720)),
            log_interval_sec=int(perf_cfg.get("log_interval_sec", 5)),
            print_interval_sec=int(perf_cfg.get("print_interval_sec", 15)),
            regime_enabled=bool(reg.get("enabled", True)),
            regime_vol_window_points=int(reg.get("vol_window_points", 60)),
            regime_high_vol_threshold=float(reg.get("high_vol_threshold", 0.0015)),
            regime_min_points_each=int(reg.get("min_points_each", 80)),
        )

        self.ws_book = WSL2BookStore(max_levels=int(pcfg.get("ws_l2", {}).get("max_levels", 200)))
        self.micro = MicrostructureTracker()

        micro_cfg = pcfg.get("micro", {})
        profs_raw = micro_cfg.get("latency_profiles", {})
        profs = {k: LatencyProfile(int(v["base_ms"]), int(v["jitter_ms"]), float(v["tail_prob"]), int(v["extra_tail_ms"]), float(v["drop_prob"])) for k, v in profs_raw.items()}
        self.lat = RegionLatency(profiles=profs, region=str(micro_cfg.get("region", "us-central")))

        adv = micro_cfg.get("advsel", {})
        self.advsel_cfg = AdvSelConfig(
            k_bps_per_vol=float(adv.get("k_bps_per_vol", 18.0)),
            max_extra_bps=float(adv.get("max_extra_bps", 80.0)),
            liquidity_shrink_per_vol=float(adv.get("liquidity_shrink_per_vol", 0.35)),
            max_liquidity_shrink=float(adv.get("max_liquidity_shrink", 0.75)),
        )

        mv = pcfg.get("market_vol", {})
        self.market_vol_logger = None
        if mv.get("enabled", True):
            csv_name = str(mv.get("csv_name", "market_mid_timeseries.csv"))
            interval = float(mv.get("log_interval_sec", 1))
            base_dir = self.run_paths.run_dir if self.run_paths else "./data"
            self.market_vol_logger = MarketVolLogger(path=os.path.join(base_dir, csv_name), log_interval_sec=interval)

    async def shutdown(self):
        self.ks.trip("shutdown")

    def _perf_tick(self):
        ts = time.time()
        eq = self.paper.equity_mark_to_market(self.tob)
        unrl = self.paper.unrealized_pnl(self.tob)
        self.perf.update(ts=ts, equity=eq, cash=self.paper.cash, realized_pnl=self.paper.realized_pnl, unrealized_pnl=unrl, fills=len(self.paper.fills))

    async def run(self):
        print("[APP] starting (mock feed). TODO: integrate real Polymarket WS + py-clob-client.")
        a_mid = 0.50
        b_mid = 0.50

        dep_cfg = self.cfg.get("dependency", {})
        trigger_move = float(dep_cfg.get("trigger_move_pct", 0.03))
        min_gap = float(dep_cfg.get("min_gap_pct", 0.02))
        lin = dep_cfg.get("linear", {})
        beta = float(lin.get("beta", 1.0))
        intercept = float(lin.get("intercept", 0.0))

        def seed_book(token, mid):
            bids = [[round(mid - i*0.001, 4), 500] for i in range(1, 60)]
            asks = [[round(mid + i*0.001, 4), 500] for i in range(1, 60)]
            self.ws_book.on_message({"token_id": token, "payload": {"bids": bids, "asks": asks}})

        seed_book(self.token_b, b_mid)
        last_a = a_mid

        while not self.ks.tripped:
            await asyncio.sleep(0.2)
            now = time.time()

            # mock movement
            a_mid = max(0.01, min(0.99, a_mid + (0.004 if int(now*2) % 17 == 0 else -0.001)))
            b_mid = max(0.01, min(0.99, b_mid + (0.002 if int(now*2) % 19 == 0 else -0.0008)))

            self.tob[self.token_a] = TopOfBook(self.token_a, now, a_mid-0.001, a_mid+0.001)
            self.tob[self.token_b] = TopOfBook(self.token_b, now, b_mid-0.001, b_mid+0.001)
            self.micro.on_tob(self.tob[self.token_b])

            if self.market_vol_logger:
                self.market_vol_logger.maybe_log(self.token_b, self.tob[self.token_b].midpoint)

            if int(now) % 5 == 0:
                seed_book(self.token_b, b_mid)

            self._perf_tick()

            move = abs(a_mid - last_a) / max(last_a, 1e-9)
            last_a = a_mid
            if move < trigger_move:
                continue

            fair_b = max(0.01, min(0.99, intercept + beta * a_mid))
            tob_b = self.tob[self.token_b].midpoint or b_mid
            gap = (fair_b - tob_b) / max(tob_b, 1e-9)
            if abs(gap) < min_gap:
                continue

            side = "BUY" if gap > 0 else "SELL"
            limit_price = tob_b * (1.0 + (0.001 if side == "BUY" else -0.001))
            size_usd = min(self.paper.cash * 0.02, 25.0)

            intent = OrderIntent(self.token_b, side, float(limit_price), float(size_usd))

            ok, lat_sec = await self.lat.wait()
            if not ok:
                self.attempts.log(intent.token_id, intent.side, intent.price, intent.size_usd, ok=False, reason="dropped")
                continue

            extra_slip = 0.0
            liq_shrink = 0.0
            stats = self.micro.stats_over(lat_sec)
            if stats:
                pen = compute_advsel_penalty(stats.abs_move_pct, self.advsel_cfg)
                extra_slip = pen.extra_slippage_bps
                liq_shrink = pen.liquidity_shrink

            book = self.ws_book.get_book(intent.token_id)
            if book is None:
                self.attempts.log(intent.token_id, intent.side, intent.price, intent.size_usd, ok=False, reason="no_book")
                continue

            self.attempts.log(intent.token_id, intent.side, intent.price, intent.size_usd, ok=False, reason=f"attempt lat={lat_sec*1000:.0f}ms")
            fill = self.paper.try_fill_fok_with_depth(
                intent, book,
                reason=f"dep(lat={lat_sec*1000:.0f}ms extra={extra_slip:.1f} shrink={liq_shrink:.2f})",
                extra_slippage_bps=extra_slip, liquidity_shrink=liq_shrink
            )
            self.attempts.log(intent.token_id, intent.side, intent.price, intent.size_usd, ok=bool(fill), reason=("filled" if fill else "canceled"))
            if fill:
                self._perf_tick()

        print(f"[APP] stopped: {self.ks.reason}")
