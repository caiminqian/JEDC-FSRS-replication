"""
Monte Carlo Simulation: HumanAgent Memory Engine Statistics

运行多次独立模拟（不同随机种子），收集 R(t) 轨迹统计
输出: 均值/标准差/分位数 + 可视化图表
"""

import random
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

# 实验配置
N_RUNS = 30  # 独立模拟次数
SEED_BASE = 0  # 起始种子（每次 run 使用 seed=SEED_BASE + run_id）
SIM_TICKS = 250
SAMPLE_INTERVAL = 10  # 每多少 tick 采样一次 R

# 固定模拟参数（跨 run 一致）
SIM_CONFIG = {
    "markets": ["BTC", "ETH", "AAPL", "SPY"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175, "SPY": 440},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015, "SPY": 0.012},
    "shock_prob": 0.02,
    "shock_severity_range": (0.15, 0.40),
    "agent_counts": {"human": 1, "retail": 10, "institution": 3, "market_maker": 2}
}

def create_world() -> WorldStateGraph:
    """创建市场世界（每次 run 重新创建）"""
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

def create_agents():
    """创建 Agent 集合（每次 run 重新创建）"""
    agents = []
    
    # HumanAgent (主角, rng=rng)
    human = HumanAgent("AlphaTrader", config={
        "use_fsrs": False,
        "ee_difficulty_factor": 1.0,
        "initial_balance": 250000,
        "max_positions": 10,
        "fomo_factor": 0.7,
        "panic_factor": 0.8,
        "loss_aversion": 2.0
    }, rng=rng)
    agents.append(human)
    
    # RetailAgents
    for i in range(SIM_CONFIG["agent_counts"]["retail"]):
        retail = RetailAgent(f"Retail_{i+1:03d}", config={
            "initial_balance": rng.randint(30000, 80000, rng=rng),
            "fomo_factor": rng.uniform(0.5, 0.9),
            "panic_factor": rng.uniform(0.6, 0.9)
        })
        agents.append(retail)
    
    # Institutions
    for i in range(SIM_CONFIG["agent_counts"]["institution"]):
        inst = RetailAgent(f"Inst_{i+1:03d}", config={
            "initial_balance": rng.randint(500000, 2000000, rng=rng),
            "fomo_factor": rng.uniform(0.2, 0.5),
            "panic_factor": rng.uniform(0.3, 0.6)
        })
        agents.append(inst)
    
    # Market Makers
    for i in range(SIM_CONFIG["agent_counts"]["market_maker"]):
        mm = RetailAgent(f"MM_{i+1:03d}", config={
            "initial_balance": 1000000,
            "fomo_factor": 0.1,
            "panic_factor": 0.1
        }, rng=rng)
        agents.append(mm)
    
    return agents

def update_prices(world: WorldStateGraph):
    """价格随机游走"""
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
    """黑天鹅事件"""
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

def run_single_simulation(run_id: int) -> Dict:
    """执行单次独立模拟"""
    seed = SEED_BASE + run_id
    random.seed(seed)
    np.random.seed(seed)
    
    world = create_world()
    agents = create_agents()
    human_agent = agents[0]  # HumanAgent
    
    memory_log = []
    shock_log = []
    
    for tick in range(SIM_TICKS):
        shock_occurred, symbol, severity = trigger_black_swan(world)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            quality = rng.randint(3, 5)
            human_agent.process_market_shock(shock_tick=tick, severity=severity, quality=quality)
        
        update_prices(world)
        
        if tick % SAMPLE_INTERVAL == 0:
            sim_time = datetime.now(timezone.utc) + timedelta(days=tick)
            R = human_agent.cognitive_memory.get_risk_awareness(current_time=sim_time)["overall_R"]
            memory_log.append({"tick": tick, "R": R})
    
    # 最终状态
    final_time = datetime.now(timezone.utc) + timedelta(days=SIM_TICKS)
    final_R = human_agent.cognitive_memory.get_risk_awareness(current_time=final_time)["overall_R"]
    
    return {
        "run_id": run_id,
        "seed": seed,
        "final_R": final_R,
        "memory_history": memory_log,
        "shocks": shock_log,
        "total_shocks": len(shock_log),
        "final_memories": {
            k: {"S": m.S, "EF": m.EF, "repetitions": m.repetition_count, "interval": m.interval_days}
            for k, m in human_agent.cognitive_memory.memories.items()
        }
    }

def analyze_results(all_results: List[Dict]) -> Dict:
    """统计分析"""
    final_Rs = [r["final_R"] for r in all_results]
    total_shocks = [r["total_shocks"] for r in all_results]
    
    # 构建轨迹矩阵: runs × time_points
    n_runs = len(all_results)
    n_points = len(all_results[0]["memory_history"])
    trajectory_matrix = np.zeros((n_runs, n_points))
    for i, res in enumerate(all_results):
        for j, point in enumerate(res["memory_history"]):
            trajectory_matrix[i, j] = point["R"]
    
    # 统计
    stats = {
        "final_R": {
            "mean": float(np.mean(final_Rs)),
            "std": float(np.std(final_Rs)),
            "min": float(np.min(final_Rs)),
            "max": float(np.max(final_Rs)),
            "median": float(np.median(final_Rs)),
            "q25": float(np.percentile(final_Rs, 25)),
            "q75": float(np.percentile(final_Rs, 75)),
            "raw": final_Rs
        },
        "total_shocks": {
            "mean": float(np.mean(total_shocks)),
            "std": float(np.std(total_shocks)),
            "min": float(np.min(total_shocks)),
            "max": float(np.max(total_shocks)),
            "raw": total_shocks
        },
        "trajectory": {
            "mean": trajectory_matrix.mean(axis=0).tolist(),
            "std": trajectory_matrix.std(axis=0).tolist(),
            "q25": np.percentile(trajectory_matrix, 25, axis=0).tolist(),
            "q75": np.percentile(trajectory_matrix, 75, axis=0).tolist(),
            "ticks": [p["tick"] for p in all_results[0]["memory_history"]]
        }
    }
    return stats

def print_summary(stats: Dict):
    """打印统计摘要"""
    print("\n" + "="*70)
    print("MONTE CARLO RESULTS")
    print("="*70)
    print(f"Runs: {N_RUNS} | Tick span: {SIM_TICKS} days | Sample interval: {SAMPLE_INTERVAL} days")
    print()
    print("--- Final Retention R(250) ---")
    r_stats = stats["final_R"]
    print(f"  Mean ± Std : {r_stats['mean']:.3f} ± {r_stats['std']:.3f}")
    print(f"  Range      : [{r_stats['min']:.3f}, {r_stats['max']:.3f}]")
    print(f"  Median (IQR): {r_stats['median']:.3f} [{r_stats['q25']:.3f}, {r_stats['q75']:.3f}]")
    print()
    print("--- Black Swan Events ---")
    s_stats = stats["total_shocks"]
    print(f"  Mean ± Std : {s_stats['mean']:.1f} ± {s_stats['std']:.1f}")
    print(f"  Range      : [{s_stats['min']}, {s_stats['max']}]")
    print("="*70)

def save_results(all_results: List[Dict], stats: Dict):
    """保存结果到文件"""
    output = {
        "experiment_config": {
            "n_runs": N_RUNS,
            "seed_base": SEED_BASE,
            "sim_ticks": SIM_TICKS,
            "sample_interval": SAMPLE_INTERVAL,
            "sim_config": SIM_CONFIG
        },
        "summary_stats": stats,
        "individual_runs": all_results  # 保留原始数据用于后续分析
    }
    
    with open("output/mc_humanagent_results.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Full results saved to output/mc_humanagent_results.json")
    
    # 保存摘要（只保留统计量）
    summary = {
        "experiment_config": output["experiment_config"],
        "summary_stats": stats
    }
    with open("output/mc_humanagent_summary.json", "w", encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Summary saved to output/mc_humanagent_summary.json")

def plot_results(stats: Dict):
    """绘制轨迹图（均值 ± 1σ 带）"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        ticks = stats["trajectory"]["ticks"]
        mean_R = stats["trajectory"]["mean"]
        std_R = stats["trajectory"]["std"]
        q25 = stats["trajectory"]["q25"]
        q75 = stats["trajectory"]["q75"]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 均值线
        ax.plot(ticks, mean_R, 'b-', linewidth=2.5, label='Mean R')
        
        # 标准差带
        ax.fill_between(ticks,
                        [m - s for m, s in zip(mean_R, std_R)],
                        [m + s for m, s in zip(mean_R, std_R)],
                        color='blue', alpha=0.2, label='±1 Std')
        
        # 四分位距带
        ax.fill_between(ticks, q25, q75, color='blue', alpha=0.1, label='IQR (25-75%)')
        
        ax.set_xlabel("Simulation Day")
        ax.set_ylabel("Risk Awareness R")
        ax.set_title(f"HumanAgent Memory Retention: {N_RUNS} Monte Carlo Runs")
        ax.set_ylim(0, 1.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig("output/mc_humanagent_trajectory.png", dpi=150)
        print(f"[OK] Trajectory plot saved to output/mc_humanagent_trajectory.png")
        plt.close()
    except ImportError:
        print("[WARN] matplotlib not available, skipping plot")

def main():
    print("="*70)
    print("MONTE CARLO SIMULATION: HumanAgent Memory Engine")
    print(f"Runs: {N_RUNS} | Seeds: {SEED_BASE}–{SEED_BASE+N_RUNS-1}")
    print("="*70)
    
    all_results = []
    for run_id in range(N_RUNS):
        print(f"\r[Run {run_id+1:2d}/{N_RUNS}]  ", end="", flush=True)
        result = run_single_simulation(run_id)
        all_results.append(result)
        # 可选: 打印单次摘要
        # print(f"  Run {run_id+1}: final_R={result['final_R']:.3f}, shocks={result['total_shocks']}")
    
    print(f"\n[OK] All {N_RUNS} runs completed")
    
    # 统计分析
    stats = analyze_results(all_results)
    print_summary(stats)
    
    # 保存
    save_results(all_results, stats)
    
    # 绘图
    plot_results(stats)
    
    print("\n[Experiment complete]")
    return stats

if __name__ == "__main__":
    stats = main()