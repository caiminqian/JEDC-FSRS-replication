"""
FSRS vs EE+SM-2 ULTRA LONG-TERM (10-year / 3650-day) Monte Carlo

测试两种记忆引擎在 10 年时间尺度下的极限行为
"""

import random
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

# 超长期实验配置
N_RUNS = 8  # 8 次独立运行（10 年单次较慢）
SEED_BASE = 200  # 种子 200-207
SIM_TICKS = 3650  # 10 年 ≈ 3650 天
SAMPLE_INTERVAL = 50  # 每 50 天采样（73 个点）

# 市场参数（保持不变）
SIM_CONFIG = {
    "markets": ["BTC", "ETH", "AAPL", "SPY"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175, "SPY": 440},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015, "SPY": 0.012},
    "shock_prob": 0.02,  # 每日 2% → 10 年预期 73 次冲击
    "shock_severity_range": (0.15, 0.40),
}

def create_world(seed: int) -> WorldStateGraph:
    rng = random.Random(seed)
    world = WorldStateGraph()
    for symbol in SIM_CONFIG["markets"]:
        price = SIM_CONFIG["initial_prices"][symbol]
        vol = SIM_CONFIG["volatilities"][symbol]
        world.add_node(
            node_id=f"market:{symbol}",
            node_type="market",
            attributes={
                "symbol": symbol,
                "price": price,
                "change": 0.0,
                "volume": rng.uniform(1e6, 1e7),
                "liquidity": rng.uniform(0.7, 1.0),
                "bid": round(price * 0.999, 2),
                "ask": round(price * 1.001, 2),
                "volatility": vol,
                "category": "crypto" if symbol in ["BTC", "ETH"] else "equity"
            }
        )
    return world

def update_prices(world: WorldStateGraph, rng: random.Random):
    for node_id, data in world.graph.nodes(data=True):
        if data.get("type") != "market":
            continue
        vol = data.get("volatility", 0.02)
        drift = 0.0002
        shock = rng.gauss(0, vol)
        change_pct = drift + shock
        new_price = data["price"] * (1 + change_pct)
        world.update_node(node_id, {
            "price": round(new_price, 2),
            "change": round(change_pct, 6),
            "bid": round(new_price * 0.999, 2),
            "ask": round(new_price * 1.001, 2)
        })

def trigger_black_swan(world: WorldStateGraph, rng: random.Random) -> Tuple[bool, str, float]:
    if rng.random() < SIM_CONFIG["shock_prob"]:
        markets = [n for n, d in world.graph.nodes(data=True) if d.get("type") == "market"]
        if markets:
            target = rng.choice(markets)
            data = world.graph.nodes[target]
            severity = rng.uniform(*SIM_CONFIG["shock_severity_range"])
            new_price = data["price"] * (1 - severity)
            world.update_node(target, {"price": round(new_price, 2), "change": -severity})
            return True, data["symbol"], severity
    return False, None, 0.0

def create_agent(agent_type: str, agent_id: str, rng: random.Random):
    if agent_type == "ee":
        return HumanAgent(agent_id, config={
            "use_fsrs": False,
            "ee_difficulty_factor": 1.0,
            "initial_balance": 250000,
            "max_positions": 10,
            "fomo_factor": 0.7,
            "panic_factor": 0.8,
            "loss_aversion": 2.0
        }, rng=rng)
    elif agent_type == "fsrs":
        return HumanAgent(agent_id, config={
            "use_fsrs": True,
            "fsrs_agent_type": "retail",
            "initial_balance": 250000,
            "max_positions": 10,
            "fomo_factor": 0.7,
            "panic_factor": 0.8,
            "loss_aversion": 2.0
        }, rng=rng)
    else:
        raise ValueError(f"Unknown agent_type: {agent_type}")

def run_dual_engine_simulation(run_id: int) -> Dict:
    """执行单次 10 年双引擎模拟"""
    seed = SEED_BASE + run_id
    rng = random.Random(seed)  # local RNG for this run

    world = create_world(seed)
    agent_ee = create_agent("ee", f"EE_{run_id:03d}", rng=rng)
    agent_fsrs = create_agent("fsrs", f"FSRS_{run_id:03d}", rng=rng)
    
    history_ee = []
    history_fsrs = []
    shock_log = []
    
    print(f"\r[Run {run_id+1:2d}/{N_RUNS}]  ", end="", flush=True)
    
    for tick in range(SIM_TICKS):
        shock_occurred, symbol, severity = trigger_black_swan(world, rng)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            quality = rng.randint(3, 5)
            agent_ee.process_market_shock(shock_tick=tick, severity=severity, quality=quality)
            grade = 2 if severity >= 0.5 else 3
            agent_fsrs.process_market_shock(shock_tick=tick, shock_grade=grade)
        
        update_prices(world, rng)
        
        if tick % SAMPLE_INTERVAL == 0:
            sim_time = datetime.now(timezone.utc) + timedelta(days=tick)
            R_ee = agent_ee.cognitive_memory.get_risk_awareness(current_time=sim_time)["overall_R"]
            R_fsrs = agent_fsrs.memory_fsrs.get_risk_awareness(current_tick=tick)["overall_R"]
            history_ee.append({"tick": tick, "R": R_ee})
            history_fsrs.append({"tick": tick, "R": R_fsrs})
    
    final_time = datetime.now(timezone.utc) + timedelta(days=SIM_TICKS)
    final_R_ee = agent_ee.cognitive_memory.get_risk_awareness(current_time=final_time)["overall_R"]
    final_R_fsrs = agent_fsrs.memory_fsrs.get_risk_awareness(current_tick=SIM_TICKS)["overall_R"]
    
    memories_ee = {
        k: {"S": m.S, "EF": m.EF, "repetitions": m.repetition_count, "interval": m.interval_days}
        for k, m in agent_ee.cognitive_memory.memories.items()
    }
    memories_fsrs = {
        k: {"S": m.S, "difficulty": m.difficulty}
        for k, m in agent_fsrs.memory_fsrs.memories.items()
    }
    
    return {
        "run_id": run_id,
        "seed": seed,
        "final_R_ee": final_R_ee,
        "final_R_fsrs": final_R_fsrs,
        "R_delta": final_R_fsrs - final_R_ee,
        "history_ee": history_ee,
        "history_fsrs": history_fsrs,
        "total_shocks": len(shock_log),
        "shocks": shock_log,
        "memories_ee": memories_ee,
        "memories_fsrs": memories_fsrs
    }

def analyze_dual_results(all_results: List[Dict]) -> Dict:
    n_runs = len(all_results)
    R_ee_all = [r["final_R_ee"] for r in all_results]
    R_fsrs_all = [r["final_R_fsrs"] for r in all_results]
    R_delta_all = [r["R_delta"] for r in all_results]
    shocks_all = [r["total_shocks"] for r in all_results]
    
    n_points = len(all_results[0]["history_ee"])
    traj_ee = np.zeros((n_runs, n_points))
    traj_fsrs = np.zeros((n_runs, n_points))
    for i, res in enumerate(all_results):
        for j, pt in enumerate(res["history_ee"]):
            traj_ee[i, j] = pt["R"]
        for j, pt in enumerate(res["history_fsrs"]):
            traj_fsrs[i, j] = pt["R"]
    
    stats = {
        "n_runs": n_runs,
        "ee": {
            "final_R": {
                "mean": float(np.mean(R_ee_all)),
                "std": float(np.std(R_ee_all)),
                "median": float(np.median(R_ee_all)),
                "q25": float(np.percentile(R_ee_all, 25)),
                "q75": float(np.percentile(R_ee_all, 75)),
                "min": float(np.min(R_ee_all)),
                "max": float(np.max(R_ee_all)),
                "raw": R_ee_all
            },
            "trajectory": {
                "mean": traj_ee.mean(axis=0).tolist(),
                "std": traj_ee.std(axis=0).tolist(),
                "q25": np.percentile(traj_ee, 25, axis=0).tolist(),
                "q75": np.percentile(traj_ee, 75, axis=0).tolist()
            }
        },
        "fsrs": {
            "final_R": {
                "mean": float(np.mean(R_fsrs_all)),
                "std": float(np.std(R_fsrs_all)),
                "median": float(np.median(R_fsrs_all)),
                "q25": float(np.percentile(R_fsrs_all, 25)),
                "q75": float(np.percentile(R_fsrs_all, 75)),
                "min": float(np.min(R_fsrs_all)),
                "max": float(np.max(R_fsrs_all)),
                "raw": R_fsrs_all
            },
            "trajectory": {
                "mean": traj_fsrs.mean(axis=0).tolist(),
                "std": traj_fsrs.std(axis=0).tolist(),
                "q25": np.percentile(traj_fsrs, 25, axis=0).tolist(),
                "q75": np.percentile(traj_fsrs, 75, axis=0).tolist()
            }
        },
        "comparison": {
            "delta_mean": float(np.mean(R_delta_all)),
            "delta_std": float(np.std(R_delta_all)),
            "delta_median": float(np.median(R_delta_all)),
            "delta_raw": R_delta_all,
            "wins_fsrs": sum(1 for d in R_delta_all if d > 0),
            "wins_ee": sum(1 for d in R_delta_all if d < 0),
            "ties": sum(1 for d in R_delta_all if abs(d) < 1e-6)
        },
        "shocks": {
            "mean": float(np.mean(shocks_all)),
            "std": float(np.std(shocks_all)),
            "raw": shocks_all
        },
        "ticks": SIM_TICKS,
        "sample_interval": SAMPLE_INTERVAL
    }
    return stats

def print_comparison_table(stats: Dict):
    print("\n" + "="*80)
    print(f"FSRS vs EE+SM-2 ULTRA LONG-TERM ({SIM_TICKS} days / 10 years) MONTE CARLO")
    print(f"  {stats['n_runs']} independent runs | shock_prob={SIM_CONFIG['shock_prob']:.1%} | sample every {SAMPLE_INTERVAL} days")
    print("="*80)
    
    ee = stats["ee"]["final_R"]
    fsrs = stats["fsrs"]["final_R"]
    comp = stats["comparison"]
    
    print(f"\n{'Metric':<25} {'EE+SM-2':>18} {'FSRS':>18} {'Diff':>12}")
    print("-" * 80)
    print(f"{'Final R(3650) Mean':<25} {ee['mean']:>18.3f} {fsrs['mean']:>18.3f} {comp['delta_mean']:>+12.3f}")
    print(f"{'Final R Std':<25} {ee['std']:>18.3f} {fsrs['std']:>18.3f} {'':>12}")
    print(f"{'Median (IQR)':<25} {ee['median']:>18.3f} {fsrs['median']:>18.3f} {'':>12}")
    print(f"{'Range':<25} [{ee['min']:.3f}, {ee['max']:.3f}]  [{fsrs['min']:.3f}, {fsrs['max']:.3f}] {'':>12}")
    print(f"\n{'Win Rate':<25} {'':>18} {comp['wins_fsrs']}/{stats['n_runs']} (FSRS better) {'':>12}")
    print(f"{'Tie Rate':<25} {'':>18} {comp['ties']}/{stats['n_runs']} {'':>12}")
    print(f"{'Black Swans (mean)':<25} {stats['shocks']['mean']:>18.1f} ± {stats['shocks']['std']:>5.1f} {'':>12}")
    print("="*80)

def plot_comparison(stats: Dict):
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        ticks = list(range(0, SIM_TICKS + 1, SAMPLE_INTERVAL))
        if len(ticks) != len(stats["ee"]["trajectory"]["mean"]):
            ticks = list(range(len(stats["ee"]["trajectory"]["mean"])))
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(f"FSRS vs EE+SM-2: 10-Year ({SIM_TICKS} days) Monte Carlo - {stats['n_runs']} Runs", fontsize=14)
        
        # 1. 轨迹对比（均值 ± IQR）
        ax1 = axes[0, 0]
        ee_mean = stats["ee"]["trajectory"]["mean"]
        ee_q25 = stats["ee"]["trajectory"]["q25"]
        ee_q75 = stats["ee"]["trajectory"]["q75"]
        fsrs_mean = stats["fsrs"]["trajectory"]["mean"]
        fsrs_q25 = stats["fsrs"]["trajectory"]["q25"]
        fsrs_q75 = stats["fsrs"]["trajectory"]["q75"]
        
        ax1.plot(ticks, ee_mean, 'b-', label='EE+SM-2', linewidth=2.5)
        ax1.fill_between(ticks, ee_q25, ee_q75, color='blue', alpha=0.2)
        ax1.plot(ticks, fsrs_mean, 'r-', label='FSRS', linewidth=2.5)
        ax1.fill_between(ticks, fsrs_q25, fsrs_q75, color='red', alpha=0.2)
        ax1.set_xlabel("Day")
        ax1.set_ylabel("Risk Awareness R")
        ax1.set_title("Trajectory Comparison (mean ± IQR)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1.0)
        
        # 2. 最终 R 分布箱线图
        ax2 = axes[0, 1]
        data = [stats["ee"]["final_R"]["raw"], stats["fsrs"]["final_R"]["raw"]]
        ax2.boxplot(data, tick_labels=['EE+SM-2', 'FSRS'])
        ax2.set_ylabel("Final R(3650)")
        ax2.set_title("Distribution of Final Retention (10 years)")
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Delta 分布
        ax3 = axes[1, 0]
        ax3.hist(stats["comparison"]["delta_raw"], bins=10, edgecolor='black', alpha=0.7, color='purple')
        ax3.axvline(0, color='k', linestyle='--', linewidth=1)
        ax3.set_xlabel("FSRS R - EE R")
        ax3.set_ylabel("Count")
        ax3.set_title("Performance Difference (positive = FSRS better)")
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 时间演化：EE 标准差 vs FSRS 标准差
        ax4 = axes[1, 1]
        ax4.plot(ticks, stats["ee"]["trajectory"]["std"], 'b-', label='EE Std', linewidth=2)
        ax4.plot(ticks, stats["fsrs"]["trajectory"]["std"], 'r-', label='FSRS Std', linewidth=2)
        ax4.set_xlabel("Day")
        ax4.set_ylabel("Standard Deviation of R (across runs)")
        ax4.set_title("Stability Comparison Over Time")
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_yscale('log')  # 对数尺度，因差异巨大
        
        plt.tight_layout()
        plt.savefig("output/fsrs_vs_ee_10year_3650d.png", dpi=150)
        print(f"[OK] 10-year comparison plot saved to output/fsrs_vs_ee_10year_3650d.png")
        plt.close()
    except ImportError:
        print("[WARN] matplotlib not available, skipping plot")

def main():
    print("="*80)
    print("ULTRA LONG-TERM (10-YEAR / 3650-day) FSRS vs EE+SM-2 MONTE CARLO")
    print(f"Runs: {N_RUNS} | Seeds: {SEED_BASE}–{SEED_BASE+N_RUNS-1}")
    print("="*80)
    
    all_results = []
    for run_id in range(N_RUNS):
        result = run_dual_engine_simulation(run_id)
        all_results.append(result)
    
    print(f"\n[OK] All {N_RUNS} 10-year runs completed")
    
    stats = analyze_dual_results(all_results)
    print_comparison_table(stats)
    
    output = {
        "experiment_config": {
            "n_runs": N_RUNS,
            "seed_base": SEED_BASE,
            "sim_ticks": SIM_TICKS,
            "sample_interval": SAMPLE_INTERVAL,
            "sim_config": SIM_CONFIG
        },
        "summary_stats": stats,
        "individual_runs": all_results
    }
    with open("output/fsrs_vs_ee_10year_3650d.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"[OK] Full results saved to output/fsrs_vs_ee_10year_3650d.json")
    
    plot_comparison(stats)
    
    print("\n[10-year experiment complete]")
    return stats

if __name__ == "__main__":
    stats = main()