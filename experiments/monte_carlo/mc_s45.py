"""
FSRS vs EE+SM-2 Head-to-Head Monte Carlo Comparison

并排运行两种记忆引擎，在完全相同的随机环境下对比性能
"""

import random
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

# 实验配置
N_RUNS = 30  # 独立模拟次数
SEED_BASE = 0
SIM_TICKS = 250
SAMPLE_INTERVAL = 10

# 固定模拟参数
SIM_CONFIG = {
    "markets": ["BTC", "ETH", "AAPL", "SPY"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175, "SPY": 440},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015, "SPY": 0.012},
    "shock_prob": 0.02,
    "shock_severity_range": (0.15, 0.40),
}

def create_world(seed: int) -> WorldStateGraph:
    """创建确定性市场世界（使用固定种子）"""
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
    """价格随机游走（全局随机）"""
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
    """黑天鹅事件（全局随机）"""
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
    """创建指定类型的 HumanAgent"""
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
    """
    单次运行：两个 Agent 共享同一世界状态和冲击序列
    
    流程:
      1. 固定随机种子（seed = SEED_BASE + run_id）
      2. 创建世界 + 两个 Agent（EE & FSRS）
      3. 同步 tick 循环：
         - 触发黑天鹅（两 Agent 同时学习）
         - 价格更新
         - 记录两个 Agent 的 R(t)
      4. 返回完整历史
    """
    seed = SEED_BASE + run_id
    rng = random.Random(seed)
    # 创建共享世界
    world = create_world(seed)
    
    # 创建两个 Agent（相同 ID 前缀，区分后缀）
    agent_ee = create_agent("ee", f"EE_{run_id:03d}", rng=rng)
    agent_fsrs = create_agent("fsrs", f"FSRS_{run_id:03d}", rng=rng)
    # S=45 audit override (v49): every FSRS lesson starts at S=45, not the 5/3/2 defaults.
    for _m in agent_fsrs.memory_fsrs.memories.values():
        _m.S = 45.0
    
    # 历史记录
    history_ee = []
    history_fsrs = []
    shock_log = []
    
    for tick in range(SIM_TICKS):
        # 1. 黑天鹅（两 Agent 同时受影响）
        shock_occurred, symbol, severity = trigger_black_swan(world, rng)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            quality = rng.randint(3, 5)
            # EE 学习
            agent_ee.process_market_shock(shock_tick=tick, severity=severity, quality=quality)
            # FSRS 学习 (severity -> grade)
            grade = 2 if severity >= 0.5 else 3
            agent_fsrs.process_market_shock(shock_tick=tick, shock_grade=grade)
        
        # 2. 价格演化
        update_prices(world, rng)
        
        # 3. 采样 R(t)
        if tick % SAMPLE_INTERVAL == 0:
            sim_time = datetime.now(timezone.utc) + timedelta(days=tick)
            
            # EE R
            R_ee = agent_ee.cognitive_memory.get_risk_awareness(current_time=sim_time)["overall_R"]
            history_ee.append({"tick": tick, "R": R_ee})
            
            # FSRS R
            R_fsrs = agent_fsrs.memory_fsrs.get_risk_awareness(current_tick=tick)["overall_R"]
            history_fsrs.append({"tick": tick, "R": R_fsrs})
    
    # 最终状态
    final_time = datetime.now(timezone.utc) + timedelta(days=SIM_TICKS)
    final_R_ee = agent_ee.cognitive_memory.get_risk_awareness(current_time=final_time)["overall_R"]
    final_R_fsrs = agent_fsrs.memory_fsrs.get_risk_awareness(current_tick=SIM_TICKS)["overall_R"]
    
    # 记忆详情
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
        "R_delta": final_R_fsrs - final_R_ee,  # 正值表示 FSRS 更高
        "history_ee": history_ee,
        "history_fsrs": history_fsrs,
        "total_shocks": len(shock_log),
        "shocks": shock_log,
        "memories_ee": memories_ee,
        "memories_fsrs": memories_fsrs
    }

def analyze_dual_results(all_results: List[Dict]) -> Dict:
    """统计分析双引擎对比"""
    n_runs = len(all_results)
    
    # 提取最终 R
    R_ee_all = [r["final_R_ee"] for r in all_results]
    R_fsrs_all = [r["final_R_fsrs"] for r in all_results]
    R_delta_all = [r["R_delta"] for r in all_results]
    shocks_all = [r["total_shocks"] for r in all_results]
    
    # 轨迹矩阵
    n_points = len(all_results[0]["history_ee"])
    traj_ee = np.zeros((n_runs, n_points))
    traj_fsrs = np.zeros((n_runs, n_points))
    for i, res in enumerate(all_results):
        for j, pt in enumerate(res["history_ee"]):
            traj_ee[i, j] = pt["R"]
        for j, pt in enumerate(res["history_fsrs"]):
            traj_fsrs[i, j] = pt["R"]
    
    # 统计
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
        "ticks": all_results[0]["history_ee"][0]["tick"] if all_results[0]["history_ee"] else None,
        "sample_interval": SAMPLE_INTERVAL
    }
    return stats

def print_comparison_table(stats: Dict):
    """打印对比表"""
    print("\n" + "="*80)
    print("FSRS vs EE+SM-2 HEAD-TO-HEAD COMPARISON")
    print(f"  {stats['n_runs']} independent runs | {SIM_TICKS} ticks per run | shock_prob={SIM_CONFIG['shock_prob']:.1%}")
    print("="*80)
    
    ee = stats["ee"]["final_R"]
    fsrs = stats["fsrs"]["final_R"]
    comp = stats["comparison"]
    
    print(f"\n{'Metric':<25} {'EE+SM-2':>18} {'FSRS':>18} {'Diff':>12}")
    print("-" * 80)
    print(f"{'Final R(250) Mean':<25} {ee['mean']:>18.3f} {fsrs['mean']:>18.3f} {comp['delta_mean']:>+12.3f}")
    print(f"{'Final R Std':<25} {ee['std']:>18.3f} {fsrs['std']:>18.3f} {'':>12}")
    print(f"{'Median (IQR)':<25} {ee['median']:>18.3f} {fsrs['median']:>18.3f} {'':>12}")
    print(f"{'Range':<25} [{ee['min']:.3f}, {ee['max']:.3f}]  [{fsrs['min']:.3f}, {fsrs['max']:.3f}] {'':>12}")
    print(f"\n{'Win Rate':<25} {'':>18} {comp['wins_fsrs']}/{stats['n_runs']} (FSRS better) {'':>12}")
    print(f"{'Tie Rate':<25} {'':>18} {comp['ties']}/{stats['n_runs']} {'':>12}")
    print(f"{'Black Swans (mean)':<25} {stats['shocks']['mean']:>18.1f} ± {stats['shocks']['std']:>5.1f} {'':>12}")
    print("="*80)

def plot_comparison(stats: Dict):
    """绘制对比图（2x2 子图）"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        ticks = list(range(0, SIM_TICKS + 1, SAMPLE_INTERVAL))
        if len(ticks) != len(stats["ee"]["trajectory"]["mean"]):
            ticks = list(range(len(stats["ee"]["trajectory"]["mean"])))
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"FSRS vs EE+SM-2: {stats['n_runs']} Monte Carlo Runs", fontsize=14)
        
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
        ax2.boxplot(data, labels=['EE+SM-2', 'FSRS'])
        ax2.set_ylabel("Final R(250)")
        ax2.set_title("Distribution of Final Retention")
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. 每 run 的 delta 分布
        ax3 = axes[1, 0]
        deltas = [r["R_delta"] for r in all_results] if 'all_results' in locals() else stats["comparison"].get("delta_raw", [])
        if deltas:
            ax3.hist(deltas, bins=15, edgecolor='black', alpha=0.7)
            ax3.axvline(0, color='k', linestyle='--', linewidth=1)
            ax3.set_xlabel("FSRS R - EE R")
            ax3.set_ylabel("Count")
            ax3.set_title("Performance Difference (positive = FSRS better)")
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 黑天鹅次数 vs 最终 R 散点
        ax4 = axes[1, 1]
        shocks_ee = stats["shocks"]["raw"]
        R_ee = stats["ee"]["final_R"]["raw"]
        R_fsrs = stats["fsrs"]["final_R"]["raw"]
        ax4.scatter(shocks_ee, R_ee, alpha=0.6, label='EE', color='blue')
        ax4.scatter(shocks_ee, R_fsrs, alpha=0.6, label='FSRS', color='red')
        ax4.set_xlabel("Number of Black Swan Events")
        ax4.set_ylabel("Final R")
        ax4.set_title("Retention vs Shock Frequency")
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig("output/fsrs_vs_ee_comparison.png", dpi=150)
        print(f"[OK] Comparison plot saved to output/fsrs_vs_ee_comparison.png")
        plt.close()
    except ImportError:
        print("[WARN] matplotlib not available, skipping plot")

def main():
    print("="*70)
    print("FSRS vs EE+SM-2 HEAD-TO-HEAD MONTE CARLO")
    print(f"Runs: {N_RUNS} | Seeds: {SEED_BASE}–{SEED_BASE+N_RUNS-1}")
    print("="*70)
    
    all_results = []
    for run_id in range(N_RUNS):
        print(f"\r[Run {run_id+1:2d}/{N_RUNS}]  ", end="", flush=True)
        result = run_dual_engine_simulation(run_id)
        all_results.append(result)
    
    print(f"\n[OK] All {N_RUNS} dual runs completed")
    
    # 统计分析
    stats = analyze_dual_results(all_results)
    print_comparison_table(stats)
    
    # 保存
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
    with open("output/fsrs_vs_ee_monte_carlo.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"[OK] Full results saved to output/fsrs_vs_ee_monte_carlo.json")
    
    # 绘图
    plot_comparison(stats)
    
    print("\n[Experiment complete]")
    return stats

if __name__ == "__main__":
    stats = main()