from __future__ import annotations
import asyncio, json, os, time, random
from typing import Dict, Any, List
from bot.tournament.evolution_genome import Genome, random_genome, crossover, mutate
from bot.tournament.evolution_variant import apply_genome
from bot.tournament.evolution_score import compute_score

def _now_id(): return time.strftime("%Y%m%d-%H%M%S")
def _lerp(a: float, b: float, t: float) -> float: return a + (b-a)*t
async def _sleep_minutes(m: float): await asyncio.sleep(m*60.0)

class EvolutionManager:
    def __init__(self, base_cfg: Dict[str, Any]):
        self.base_cfg = base_cfg
        self.ecfg = base_cfg.get("evolution", {})
        self.space = self.ecfg["space"]
        self.objective = self.ecfg["objective"]
        self.constraints = self.ecfg["constraints"]
        self.wf_cfg = self.ecfg.get("walkforward", {})
        self.rng = random.Random(int(self.ecfg.get("seed", 1337)))
        self.base_runs_dir = str(base_cfg.get("paper", {}).get("runs", {}).get("base_dir", "./runs"))
        self.evo_dir = os.path.join(self.base_runs_dir, "evolution")
        os.makedirs(self.evo_dir, exist_ok=True)

    async def run(self):
        G = int(self.ecfg.get("generations", 4))
        N = int(self.ecfg.get("population", 8))
        elite_k = int(self.ecfg.get("elite", 2))
        max_parallel = int(self.ecfg.get("max_parallel", 2))
        eval_minutes = float(self.ecfg.get("eval_minutes", 2))

        anneal = self.ecfg.get("annealing", {})
        a_on = bool(anneal.get("enabled", True))
        r0 = float(anneal.get("mutation_rate_start", 0.45))
        r1 = float(anneal.get("mutation_rate_end", 0.15))
        s0 = float(anneal.get("mutation_strength_start", 0.25))
        s1 = float(anneal.get("mutation_strength_end", 0.08))

        pop: List[Genome] = [random_genome(self.rng, self.space) for _ in range(N)]

        for gen in range(1, G+1):
            gen_id = f"gen{gen:02d}-{_now_id()}"
            t = 0.0 if G<=1 else (gen-1)/(G-1)
            mut_rate = _lerp(r0, r1, t) if a_on else 0.35
            mut_strength = _lerp(s0, s1, t) if a_on else 0.18

            results = await self._eval_population(gen_id, pop, eval_minutes, max_parallel=max_parallel)
            ranked = sorted(results, key=lambda x: x["score"], reverse=True)
            out_path = os.path.join(self.evo_dir, f"{gen_id}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(ranked, f, indent=2)
            print(f"[EVOLUTION] gen={gen} best={ranked[0]['score']:.4f} run={ranked[0].get('run_id')} reason={ranked[0].get('reason')}")

            elites = ranked[:elite_k]
            elite_genomes = [Genome(**e["genome"]) for e in elites]

            next_pop: List[Genome] = []
            next_pop.extend(elite_genomes)
            while len(next_pop) < N:
                p1 = self.rng.choice(elite_genomes)
                p2 = self.rng.choice(elite_genomes)
                child = crossover(self.rng, p1, p2)
                child = mutate(self.rng, child, self.space, rate=mut_rate, strength=mut_strength)
                next_pop.append(child)
            pop = next_pop

    async def _eval_population(self, gen_id: str, pop: List[Genome], eval_minutes: float, *, max_parallel: int):
        sem = asyncio.Semaphore(max_parallel)
        tasks = []
        for i, g in enumerate(pop):
            tag = f"evo-{gen_id}-v{i:02d}"
            tasks.append(asyncio.create_task(self._run_one(sem, g, tag, eval_minutes)))
        return await asyncio.gather(*tasks)

    async def _run_one(self, sem: asyncio.Semaphore, genome: Genome, tag: str, eval_minutes: float):
        async with sem:
            cfg = apply_genome(self.base_cfg, genome, tag=tag)
            from bot.app import App
            app = App(cfg)
            task = asyncio.create_task(app.run())
            await _sleep_minutes(eval_minutes)
            try: await app.shutdown()
            except Exception: pass
            task.cancel()
            try: await task
            except Exception: pass

            run_id = self._find_latest_run_id(prefix=f"{tag}-")
            summary = self._load_summary(run_id) if run_id else None
            if not summary:
                return {"tag": tag, "run_id": run_id, "genome": genome.to_dict(), "score": -1e9, "ok": False, "reason": "no summary"}

            run_dir = os.path.join(self.base_runs_dir, run_id)
            perf_regime_cfg = self.base_cfg.get("paper", {}).get("performance", {}).get("regime", {})
            if self.wf_cfg.get("enabled", True):
                from bot.tournament.rolling_walkforward_score import rolling_walkforward_score
                rwf = rolling_walkforward_score(run_dir=run_dir, summary=summary, objective=self.objective, constraints=self.constraints, wf_cfg=self.wf_cfg, perf_regime_cfg=perf_regime_cfg)
                return {"tag": tag, "run_id": run_id, "genome": genome.to_dict(), "score": rwf.score, "ok": rwf.ok, "reason": rwf.reason, "rolling_walkforward": [fr.__dict__ for fr in rwf.folds]}
            sc = compute_score(summary, self.objective, self.constraints)
            return {"tag": tag, "run_id": run_id, "genome": genome.to_dict(), "score": sc.value, "ok": sc.ok, "reason": sc.reason}

    def _find_latest_run_id(self, prefix: str):
        if not os.path.exists(self.base_runs_dir): return None
        ds = [d for d in os.listdir(self.base_runs_dir) if d.startswith(prefix)]
        if not ds: return None
        ds.sort()
        return ds[-1]

    def _load_summary(self, run_id: str | None):
        if not run_id: return None
        p = os.path.join(self.base_runs_dir, run_id, "performance_summary.json")
        if not os.path.exists(p): return None
        try: return json.loads(open(p, "r", encoding="utf-8").read())
        except Exception: return None
