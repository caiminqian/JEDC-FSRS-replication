"""
ECOS 完整模拟 - HumanAgent 记忆引擎实战

直接使用 WorldStateGraph，避免接口不匹配
"""

import random
import json
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

SEED = 42

# Local RNG for reproducible randomness
rng = random.Random(42)
rng.seed(SEED)

CONFIG = {
    "ticks": 250,
    "markets": ["BTC", "ETH", "AAPL", "SPY"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175, "SPY": 440},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015, "SPY": 0.012},
    "shock_prob": 0.02,
    "shock_severity_range": (0.15, 0.40),
}

def setup_world() -> WorldStateGraph:
    world = WorldStateGraph()
    for symbol in CONFIG["markets"]:
        price = CONFIG["initial_prices"][symbol]
        vol = CONFIG["volatilities"][symbol]
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
    print(f"[OK] WorldStateGraph initialized with {len(CONFIG['markets'])} markets")
    return world

def create_agents() -> List:
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
    for i in range(10):
        retail = RetailAgent(f"Retail_{i+1:03d}", config={
            "initial_balance": rng.randint(30000, 80000, rng=rng),
            "fomo_factor": rng.uniform(0.5, 0.9),
            "panic_factor": rng.uniform(0.6, 0.9)
        })
        agents.append(retail)
    
    # Institutions
    for i in range(3):
        inst = RetailAgent(f"Inst_{i+1:03d}", config={
            "initial_balance": rng.randint(500000, 2000000, rng=rng),
            "fomo_factor": rng.uniform(0.2, 0.5),
            "panic_factor": rng.uniform(0.3, 0.6)
        })
        agents.append(inst)
    
    # Market Makers
    for i in range(2):
        mm = RetailAgent(f"MM_{i+1:03d}", config={
            "initial_balance": 1000000,
            "fomo_factor": 0.1,
            "panic_factor": 0.1
        }, rng=rng)
        agents.append(mm)
    
    print(f"[OK] Created {len(agents)} agents: 1 Human, 10 Retail, 3 Inst, 2 MM")
    return agents

def update_market_prices(world: WorldStateGraph):
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
    if rng.random() < CONFIG["shock_prob"]:
        markets = [n for n, d in world.graph.nodes(data=True) if d.get("type") == "market"]
        if markets:
            target = rng.choice(markets)
            data = world.graph.nodes[target]
            severity = rng.uniform(*CONFIG["shock_severity_range"])
            new_price = data["price"] * (1 - severity)
            world.update_node(target, {
                "price": round(new_price, 2),
                "change": -severity
            })
            return True, data["symbol"], severity
    return False, None, 0.0

def run_simulation():
    print("="*70)
    print("ECOS Full Simulation - HumanAgent with EE+SM-2 Memory")
    print(f"Ticks: {CONFIG['ticks']} | Agents: 16 | Markets: {len(CONFIG['markets'])}")
    print("="*70)
    
    world = setup_world()
    agents = create_agents()
    human_agent = agents[0]  # HumanAgent 是第一个
    
    memory_log = []
    shock_log = []
    
    for tick in range(CONFIG["ticks"]):
        # 1. 黑天鹅检测
        shock_occurred, symbol, severity = trigger_black_swan(world)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            print(f"  Tick {tick:3d}: [BLACK SWAN] {symbol} -{severity*100:.1f}%")
            
            # HumanAgent 学习
            quality = rng.randint(3, 5)
            result = human_agent.process_market_shock(
                shock_tick=tick,
                severity=severity,
                quality=quality
            )
            print(f"    Memory updated: S+{result.get('total_S_change', 0):.0f}, q={quality}")
        
        # 2. 价格自然演化
        update_market_prices(world)
        
        # 3. 所有 Agent 交易决策（简化）
        for agent in agents[1:]:  # 跳过 HumanAgent（已在 shock 时处理）
            # 其他 agent 简单随机交易，不记录
            pass
        
        # 4. 定期记录 HumanAgent 状态
        if tick % 50 == 0:
            sim_time = datetime.now(timezone.utc) + timedelta(days=tick)
            R = human_agent.cognitive_memory.get_risk_awareness(current_time=sim_time)["overall_R"]
            memory_log.append({"tick": tick, "R": R})
            print(f"  Tick {tick:3d}: HumanAgent Risk Awareness R = {R:.3f}")
    
    # 结束
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    
    final_R = memory_log[-1]["R"] if memory_log else 0
    print(f"\nFinal HumanAgent R (retention): {final_R:.3f}")
    print(f"Total black swan events: {len(shock_log)}")
    
    print("\n--- Memory Bank Summary ---")
    for lesson_id, mem in human_agent.cognitive_memory.memories.items():
        print(f"\n{lesson_id}:")
        print(f"  Stability S       = {mem.S:.1f} days")
        print(f"  Easiness EF       = {mem.EF:.2f}")
        print(f"  Repetition count  = {mem.repetition_count}")
        print(f"  Next review after = {mem.interval_days} days")
        # 估计半衰期
        t_half = mem.S * 0.693
        print(f"  Half-life T1/2    ≈ {t_half:.1f} days")
    
    # 保存结果
    output = {
        "config": CONFIG,
        "shocks": shock_log,
        "memory_history": memory_log,
        "final_R": final_R,
        "final_memories": {
            k: {
                "S": round(m.S, 1),
                "EF": round(m.EF, 2),
                "repetitions": m.repetition_count,
                "interval_days": m.interval_days
            } for k, m in human_agent.cognitive_memory.memories.items()
        }
    }
    
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/humanagent_simulation_results.json", "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Results saved to output/humanagent_simulation_results.json")
    
    # 快速可视化
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 5))
        ticks_plot = [h["tick"] for h in memory_log]
        R_plot = [h["R"] for h in memory_log]
        plt.plot(ticks_plot, R_plot, marker='o', linewidth=2)
        plt.xlabel("Simulation Tick (Day)")
        plt.ylabel("Risk Awareness R")
        plt.title("HumanAgent Memory Retention Over Time")
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1.0)
        plt.savefig("output/humanagent_memory_trajectory.png", dpi=150)
        print(f"[OK] Trajectory plot saved to output/humanagent_memory_trajectory.png")
    except ImportError:
        print("[WARN] matplotlib not available, skipping plot")
    
    return output

if __name__ == "__main__":
    result = run_simulation()
    print("\n[Simulation complete]")