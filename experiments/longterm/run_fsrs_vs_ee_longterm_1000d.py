"""
FSRS vs EE+SM-2 Long-Term (1000-day) Monte Carlo Comparison

测试长期记忆保持能力（2.7 年模拟）
"""

import random
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

# 长期实验配置
N_RUNS = 15  # 独立模拟次数（1000天单次较慢，减少 runs）
SEED_BASE = 100  # 从 seed 100 开始（避开短期实验的 0-99）
SIM_TICKS = 1000  # 1000 天 ≈ 2.7 年
SAMPLE_INTERVAL = 25  # 每 25 天采样一次（40 个数据点）

# 模拟参数
SIM_CONFIG = {
    "markets": ["BTC", "ETH", "AAPL", "SPY"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175, "SPY": 440},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015, "SPY": 0.012},
    "shock_prob": 0.02,  # 每日 2% 黑天鹅概率
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

def update_prices(world: WorldStateGraph):
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

def trigger_black_swan(world: WorldStateGraph) -> Tuple[bool, str, float]:
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

def create_agent(agent_type: str, agent_id: str):
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
    seed = SEED_BASE + run_id
    random.seed(seed)
    np.random.seed(seed)
    
    world = create_world(seed)
    agent_ee = create_agent("ee", f"EE_{run_id:03d}")
    agent_fsrs = create_agent("fsrs", f"FSRS_{run_id:03d}")
    
    history_ee = []
    history_fsrs = []
    shock_log = []
    
    for tick in range(SIM_TICKS):
        shock_occurred, symbol, severity = trigger_black_swan(world)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            quality = rng.randint(3, 5)
            agent_ee.process_market_shock(shock_tick=tick, severity=severity, quality=quality)
            grade = 2 if severity >= 0.5 else 3
            agent_fsrs.process_market_shock(shock_tick=tick, shock_grade=grade)
        
        update_prices(world)
        
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
    print(f"FSRS vs EE+SM-2 LONG-TERM ({SIM_TICKS} days) MONTE CARLO")
    print(f"  {stats['n_runs']} independent runs | shock_prob={SIM_CONFIG['shock_prob']:.1%} | sample every {SAMPLE_INTERVAL} days")
    print("="*80)
    
    ee = stats["ee"]["final_R"]
    fsrs = stats["fsrs"]["final_R"]
    comp = stats["comparison"]
    
    print(f"\n{'Metric':<25} {'EE+SM-2':>18} {'FSRS':>18} {'Diff':>12}")
    print("-" * 80)
    print(f"{'Final R(1000) Mean':<25} {ee['mean']:>18.3f} {fsrs['mean']:>18.3f} {comp['delta_mean']:>+12.3f}")
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
        fig.suptitle(f"FSRS vs EE+SM-2: Long-Term ({SIM_TICKS} days) Monte Carlo - {stats['n_runs']} Runs", fontsize=14)
        
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
        ax2.set_ylabel("Final R(1000)")
        ax2.set_title("Distribution of Final Retention")
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Delta 分布
        ax3 = axes[1, 0]
        deltas = [r["R_delta"] for r in all_results] if 'all_results' in locals() else stats["comparison"].get("delta_raw", [])
        if deltas:
            ax3.hist(deltas, bins=12, edgecolor='black', alpha=0.7, color='purple')
            ax3.axvline(0, color='k', linestyle='--', linewidth=1)
            ax3.set_xlabel("FSRS R - EE R (positive = FSRS better)")
            ax3.set_ylabel("Count")
            ax3.set_title("Performance Difference Distribution")
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 黑天鹅次数 vs 最终 R
        ax4 = axes[1, 1]
        shocks = stats["shocks"]["raw"]
        R_ee = stats["ee"]["final_R"]["raw"]
        R_fsrs = stats["fsrs"]["final_R"]["raw"]
        ax4.scatter(shocks, R_ee, alpha=0.7, label='EE', color='blue', s=60)
        ax4.scatter(shocks, R_fsrs, alpha=0.7, label='FSRS', color='red', s=60)
        ax4.set_xlabel("Number of Black Swan Events")
        ax4.set_ylabel("Final R(1000)")
        ax4.set_title("Retention vs Shock Frequency")
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("output/fsrs_vs_ee_longterm_1000d.png", dpi=150)
        print(f"[OK] Long-term comparison plot saved to output/fsrs_vs_ee_longterm_1000d.png")
        plt.close()
    except ImportError:
        print("[WARN] matplotlib not available, skipping plot")

def main():
    print("="*80)
    print("LONG-TERM (1000-day) FSRS vs EE+SM-2 MONTE CARLO")
    print(f"Runs: {N_RUNS} | Seeds: {SEED_BASE}–{SEED_BASE+N_RUNS-1}")
    print("="*80)
    
    all_results = []
    for run_id in range(N_RUNS):
        print(f"\r[Run {run_id+1:2d}/{N_RUNS}]  ", end="", flush=True)
        result = run_dual_engine_simulation(run_id)
        all_results.append(result)
    
    print(f"\n[OK] All {N_RUNS} long-term runs completed")
    
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
    with open("output/fsrs_vs_ee_longterm_1000d.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"[OK] Full results saved to output/fsrs_vs_ee_longterm_1000d.json")
    
    plot_comparison(stats)
    
    print("\n[Long-term experiment complete]")
    return stats

if __name__ == "__main__":
    stats = main()