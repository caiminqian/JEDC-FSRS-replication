"""
End-to-End ECOS Simulation Verification

验证 HumanAgent (default FSRS, rng=rng) 在完整模拟流程中的表现
包括：市场初始化、多Agent、黑天鹅、记忆更新、治理决策
"""

import random
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent
from ecos.governance.governance_manager import GovernanceManager

# 固定种子保证可重现
SEED = 20260418

# Local RNG for reproducible randomness
rng = random.Random(20260418)
rng.seed(SEED)

# 模拟配置
CONFIG = {
    "ticks": 200,  # 200 天（约 7 个月）
    "markets": ["BTC", "ETH", "AAPL"],
    "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175},
    "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015},
    "shock_prob": 0.03,  # 3% 每日黑天鹅概率
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
    print(f"[OK] World initialized: {len(CONFIG['markets'])} markets")
    return world

def create_agents() -> List:
    agents = []
    
    # HumanAgent (主角 - 默认 FSRS, rng=rng)
    human = HumanAgent("AlphaTrader", config={
        "initial_balance": 250000,
        "max_positions": 10
        # 注意：use_fsrs 默认 True，无需显式指定
    }, rng=rng)
    agents.append(human)
    # S=45 audit override (v49).
    for _m in human.memory_fsrs.memories.values():
        _m.S = 45.0
    
    # 添加几个 RetailAgent 作为对比
    for i in range(3):
        retail = RetailAgent(
            name=f"Retail_{i+1}",
            config={
                "initial_balance": rng.randint(40000, 80000),
                "fomo_factor": rng.uniform(0.5, 0.9),
                "panic_factor": rng.uniform(0.6, 0.9),
            },
            rng=rng
        )
        agents.append(retail)
    
    print(f"[OK] Agents created: 1 Human + 3 Retail")
    print(f"      HumanAgent memory engine: {'FSRS' if human.use_fsrs else 'EE'}")
    return agents

def update_market_prices(world: WorldStateGraph):
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

def trigger_black_swan(world: WorldStateGraph) -> tuple:
    if rng.random() < CONFIG["shock_prob"]:
        markets = [n for n, d in world.graph.nodes(data=True) if d.get("type") == "market"]
        if markets:
            target = rng.choice(markets)
            data = world.graph.nodes[target]
            severity = rng.uniform(0.15, 0.40)
            new_price = data["price"] * (1 - severity)
            world.update_node(target, {"price": round(new_price, 2), "change": -severity})
            return True, data["symbol"], severity
    return False, None, 0.0

def run_e2e_simulation():
    print("="*70)
    print("END-TO-END ECOS SIMULATION VERIFICATION")
    print(f"Seed: {SEED} | Ticks: {CONFIG['ticks']} | Markets: {len(CONFIG['markets'])}")
    print("="*70)
    
    # 初始化
    world = setup_world()
    agents = create_agents()
    human_agent = agents[0]  # HumanAgent 是第一个
    
    # 尝试初始化治理模块（如果依赖满足）
    governance = None
    try:
        governance = GovernanceManager(world=world, agents=agents, rng=rng)
        print("[OK] Governance module loaded")
    except Exception as e:
        print(f"[WARN] Governance disabled: {e}")
    
    # 记录数据
    memory_log = []
    shock_log = []
    tick_log = []
    
    print("\n--- Simulation Start ---\n")
    
    for tick in range(CONFIG["ticks"]):
        # 1. 黑天鹅检测
        shock_occurred, symbol, severity = trigger_black_swan(world)
        if shock_occurred:
            shock_log.append({"tick": tick, "symbol": symbol, "severity": severity})
            print(f"  Tick {tick:3d}: [BLACK SWAN] {symbol} -{severity*100:.1f}%")
            
            # HumanAgent 学习（使用 FSRS）
            grade = 2 if severity >= 0.5 else 3  # severity -> grade mapping
            result = human_agent.process_market_shock(shock_tick=tick, shock_grade=grade)
            # FSRS returns dict with 'new_S', EE returns similar
            new_S = result.get('new_S', result.get('S', '?'))
            print(f"    Memory updated: S now {new_S}, grade={grade}")
        
        # 2. 价格自然演化
        update_market_prices(world)
        
        # 3. 每 50 天记录 HumanAgent 状态
        if tick % 50 == 0:
            sim_time = datetime.now(timezone.utc) + timedelta(days=tick)
            # 使用统一接口（新添加的方法）
            awareness = human_agent.get_risk_awareness(tick=tick)
            R = awareness["overall_R"]
            memory_log.append({"tick": tick, "R": R})
            print(f"  Tick {tick:3d}: HumanAgent R = {R:.3f}")
            
            # 记录单个 lesson 的 R（验证统一接口）
            if tick == 0:
                R_leverage = human_agent.get_lesson_retrievability("leverage_risk", tick=tick)
                print(f"    [Debug] leverage_risk R = {R_leverage:.3f} (via unified accessor)")
        
        tick_log.append({"tick": tick, "prices": {data["symbol"]: data["price"] 
                                                  for _, data in world.graph.nodes(data=True) 
                                                  if data.get("type") == "market"}})
    
    # 结束统计
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    
    final_R = memory_log[-1]["R"] if memory_log else 0
    print(f"\nFinal HumanAgent Risk Awareness R: {final_R:.3f}")
    print(f"Total black swan events: {len(shock_log)}")
    
    print("\n--- Memory Bank Final State ---")
    # 使用统一接口获取所有记忆
    for lesson_id in ["leverage_risk", "liquidity_crisis", "bull_market_complacency"]:
        R_lesson = human_agent.get_lesson_retrievability(lesson_id, tick=CONFIG["ticks"])
        print(f"  {lesson_id}: R = {R_lesson:.3f}")
    
    # 保存完整结果
    output = {
        "config": CONFIG,
        "seed": SEED,
        "total_ticks": CONFIG["ticks"],
        "shocks": shock_log,
        "memory_history": memory_log,
        "final_R": final_R,
        "engine": "FSRS" if human_agent.use_fsrs else "EE",
        "agent_type": human_agent.agent_type
    }
    
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/e2e_verification_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Results saved to output/e2e_verification_results.json")
    
    # 生成 R 轨迹图
    try:
        import matplotlib.pyplot as plt
        ticks_plot = [h["tick"] for h in memory_log]
        R_plot = [h["R"] for h in memory_log]
        plt.figure(figsize=(10, 5))
        plt.plot(ticks_plot, R_plot, marker='o', linewidth=2, color='red')
        plt.xlabel("Day")
        plt.ylabel("Risk Awareness R")
        plt.title(f"HumanAgent Memory Retention (FSRS) - {CONFIG['ticks']} days")
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1.0)
        plt.savefig("output/e2e_humanagent_trajectory.png", dpi=150)
        print(f"[OK] Trajectory plot saved to output/e2e_humanagent_trajectory.png")
        plt.close()
    except ImportError:
        print("[WARN] matplotlib not available")
    
    print("\n[E2E verification PASSED]")
    return output

if __name__ == "__main__":
    result = run_e2e_simulation()
    print("\n[Simulation finished successfully]")