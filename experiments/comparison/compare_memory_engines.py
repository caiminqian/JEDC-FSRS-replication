"""FSRS vs EE Dual-Engine Comparison Experiment

运行双引擎并行实验,对比幂律衰减 (FSRS) 与指数衰减 (EE) 的行为差异。

实验设计:
  - 100 个 Agent (50 Human + 50 Institutional)
  - 1000 ticks 模拟
  - 50% 使用 EE, 50% 使用 FSRS
  - 记录: avg_R 曲线、杠杆率、破产率、S 分布

输出:
  - results/fsrs_vs_ee.png (对比图表)
  - results/fsrs_vs_ee.json (原始数据)
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


from ecos.core.world_state import WorldStateGraph
from ecos.core.event_bus import EventBus
from ecos.core.clock import SimClock
from ecos.agents.trader.retail_agent import RetailAgent
from ecos.agents.trader.institution_agent import InstitutionAgent
from ecos.agents.trader.human_agent import HumanAgent
from ecos.governance.governance_manager import GovernanceManager
from ecos.agents.trader.human_agent import SIM_START as HA_SIM_START


async def run_dual_engine_simulation(ticks: int = 1000):
    """运行双引擎对比实验"""

    print("="*60)
    print("FSRS vs EE 双引擎对比实验")
    print("="*60)

    # 初始化世界
    world = WorldStateGraph(name="FSRS vs EE Experiment")

    # 创建市场 (BTC, ETH, AAPL)
    markets = [
        ("BTC", 50000, 0.05),
        ("ETH", 3000, 0.06),
        ("AAPL", 200, 0.02),
    ]
    for symbol, price, vol in markets:
        world.add_node(
            node_id=f"market:{symbol}",
            node_type="market",
            attributes={
                "symbol": symbol,
                "price": price,
                "change": 0.0,
                "volume": 1e6,
                "liquidity": 0.8,
                "bid": price * 0.999,
                "ask": price * 1.001,
                "category": "crypto" if symbol in ["BTC", "ETH"] else "stock",
                "volatility": vol
            }
        )
    print(f"[OK] Created {len(markets)} markets")

    # 创建 Agent 群组
    agents = []

    # Group 1: EE Human (50%)
    for i in range(25):
        agent = HumanAgent(
            name=f"EE_Human_{i+1:03d}",
            config={
                "initial_balance": 25000,
                "use_fsrs": False,  # 使用 EE
                "fomo_factor": 0.8,
                "panic_factor": 0.9,
                "trade_frequency": 0.7
            }
        )
        agents.append(agent)

    # Group 2: FSRS Retail Human (50%)
    for i in range(25):
        agent = HumanAgent(
            name=f"FSRS_Retail_{i+1:03d}",
            config={
                "initial_balance": 25000,
                "use_fsrs": True,  # 使用 FSRS
                "fsrs_agent_type": "retail",
                "fomo_factor": 0.8,
                "panic_factor": 0.9,
                "trade_frequency": 0.7
            }
        )
        agents.append(agent)

    # Group 3: Institutional (FSRS, 更稳定)
    for i in range(30):
        agent = HumanAgent(  # 复用 HumanAgent,但配置为机构类型
            name=f"FSRS_Inst_{i+1:03d}",
            config={
                "initial_balance": 1000000,
                "use_fsrs": True,
                "fsrs_agent_type": "institution",
                "fomo_factor": 0.3,  # 机构更理性
                "panic_factor": 0.5,
                "trade_frequency": 0.4
            }
        )
        agents.append(agent)

    # Group 4: Institutional (EE, 对比)
    for i in range(20):
        agent = HumanAgent(
            name=f"EE_Inst_{i+1:03d}",
            config={
                "initial_balance": 1000000,
                "use_fsrs": False,
                "fomo_factor": 0.3,
                "panic_factor": 0.5,
                "trade_frequency": 0.4
            }
        )
        agents.append(agent)

    print(f"[OK] Created {len(agents)} agents")

    # 统计分组
    fsrs_count = sum(1 for a in agents if hasattr(a, 'use_fsrs') and a.use_fsrs)
    ee_count = len(agents) - fsrs_count
    print(f"   FSRS Agents: {fsrs_count}")
    print(f"   EE Agents: {ee_count}")

    # 初始化治理层
    governance = GovernanceManager(world=world, agents=agents, dynamic_population=False)

    # 数据收集
    results = {
        "ticks": ticks,
        "agents_total": len(agents),
        "agents_by_engine": {
            "fsrs": fsrs_count,
            "ee": ee_count
        },
        "time_series": []
    }

    print(f"\n[ROCKET] 开始模拟 {ticks} ticks...")

    for tick in range(ticks):
        # 1. 更新市场价格
        for node_id, data in world.graph.nodes(data=True):
            if data.get("type") == "market":
                volatility = data.get("volatility", 0.02)
                change_pct = __import__('random').uniform(-volatility, volatility)
                old_price = data["price"]
                new_price = old_price * (1 + change_pct)
                world.update_node(node_id, {
                    "price": round(new_price, 2),
                    "change": change_pct
                }, invalidate_cache=False)

        # 2. Agent 决策
        for agent in agents:
            if not getattr(agent, 'active', True):
                continue

            # Set current tick for memory engines
            agent.sim_tick = tick

            try:
                perception = agent.perceive(world)
                decision = agent.decide(perception)
                result = agent.act(decision, world)
                agent.learn({
                    "perception": perception,
                    "decision": decision,
                    "result": result
                })
            except Exception as e:
                import traceback
                print(f"  [ERR] Agent {agent.name} error: {e}")
                traceback.print_exc()

        # 3. 治理层执行
        gov_summary = governance.tick(tick + 1)

        # 4. 收集状态 (每 10 ticks)
        if (tick + 1) % 10 == 0:
            # 分离双引擎数据
            fsrs_agents = [a for a in agents if hasattr(a, 'use_fsrs') and a.use_fsrs]
            ee_agents = [a for a in agents if not (hasattr(a, 'use_fsrs') and a.use_fsrs)]

            def collect_engine_stats(agent_group):
                if not agent_group:
                    return {"count": 0, "avg_R": 0, "avg_S": 0, "avg_leverage": 0, "active_count": 0}

                Rs = []
                Ss = []
                leverages = []
                active = 0

                for a in agent_group:
                    if hasattr(a, 'use_fsrs') and a.use_fsrs:
                        awareness = a.memory_fsrs.get_risk_awareness(current_tick=tick)
                        bias = a.memory_fsrs.get_behavioral_bias(current_tick=tick)
                        Rs.append(awareness["overall_R"])
                        Ss.extend(awareness.get("S_distribution", [a.memory_fsrs.memories[l].S for l in a.memory_fsrs.memories]))
                        leverages.append(bias["leverage_tendency"])
                    elif hasattr(a, 'cognitive_memory'):
                        sim_time = HA_SIM_START + timedelta(days=tick)
                        awareness = a.cognitive_memory.get_risk_awareness(current_time=sim_time)
                        bias = a.cognitive_memory.get_behavioral_bias(current_time=sim_time)
                        Rs.append(awareness["overall_R"])
                        Ss.extend([m.S for m in a.cognitive_memory.memories.values()])
                        leverages.append(bias["leverage_tendency"])

                    if getattr(a, 'active', True):
                        active += 1

                return {
                    "count": len(agent_group),
                    "avg_R": sum(Rs) / len(Rs) if Rs else 0,
                    "avg_S": sum(Ss) / len(Ss) if Ss else 0,
                    "avg_leverage": sum(leverages) / len(leverages) if leverages else 1.0,
                    "active_count": active
                }

            fsrs_stats = collect_engine_stats(fsrs_agents)
            ee_stats = collect_engine_stats(ee_agents)

            snapshot = {
                "tick": tick + 1,
                "fsrs": fsrs_stats,
                "ee": ee_stats,
                "treasury": gov_summary.get("budget_changes", {}).get("treasury", 0),
                "interventions": len(gov_summary.get("interventions", []))
            }
            results["time_series"].append(snapshot)

            # 实时输出
            print(f"  Tick {tick+1:4d}: "
                  f"FSRS R={fsrs_stats['avg_R']:.3f} S={fsrs_stats['avg_S']:.1f} "
                  f"| EE R={ee_stats['avg_R']:.3f} S={ee_stats['avg_S']:.1f} "
                  f"| Interventions: {snapshot['interventions']}")

    # 保存结果
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "fsrs_vs_ee.json", 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] 实验完成! 结果保存至 results/fsrs_vs_ee.json")
    return results


def generate_plots(results: dict):
    """生成对比图表 (需要 matplotlib)"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
        from pathlib import Path
        output_dir = Path('results')
        output_dir.mkdir(exist_ok=True)

        ts = [snap["tick"] for snap in results["time_series"]]

        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('FSRS vs EE: Memory Engine Comparison', fontsize=16)

        # 1. avg_R 对比
        ax = axes[0, 0]
        ax.plot(ts, [snap["fsrs"]["avg_R"] for snap in results["time_series"]], label='FSRS', color='blue')
        ax.plot(ts, [snap["ee"]["avg_R"] for snap in results["time_series"]], label='EE', color='red')
        ax.set_xlabel('Tick')
        ax.set_ylabel('Average R (Risk Awareness)')
        ax.set_title('Risk Awareness Decay')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. avg_S 对比
        ax = axes[0, 1]
        ax.plot(ts, [snap["fsrs"]["avg_S"] for snap in results["time_series"]], label='FSRS', color='blue')
        ax.plot(ts, [snap["ee"]["avg_S"] for snap in results["time_series"]], label='EE', color='red')
        ax.set_xlabel('Tick')
        ax.set_ylabel('Average S (Stability)')
        ax.set_title('Institutionalization Depth')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. avg_leverage 对比
        ax = axes[0, 2]
        ax.plot(ts, [snap["fsrs"]["avg_leverage"] for snap in results["time_series"]], label='FSRS', color='blue')
        ax.plot(ts, [snap["ee"]["avg_leverage"] for snap in results["time_series"]], label='EE', color='red')
        ax.set_xlabel('Tick')
        ax.set_ylabel('Average Leverage')
        ax.set_title('Leverage Tendency')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 4. R 分布直方图 (最后 100 ticks)
        ax = axes[1, 0]
        # TODO: 收集所有 Agent 的最终 R 值
        ax.set_title('Final R Distribution (Pending)')

        # 5. S 分布 (对数坐标)
        ax = axes[1, 1]
        # TODO: 收集 S 值
        ax.set_title('Final S Distribution (Pending)')

        # 6. 干预次数
        ax = axes[1, 2]
        interventions = [snap["interventions"] for snap in results["time_series"]]
        ax.plot(ts, interventions, color='green')
        ax.set_xlabel('Tick')
        ax.set_ylabel('Cumulative Interventions')
        ax.set_title('Governor Interventions')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_dir / "fsrs_vs_ee.png", dpi=150)
        print(f"[OK] 图表已保存至 results/fsrs_vs_ee.png")
        plt.close()

    except ImportError:
        print("[WARN]  matplotlib 未安装,跳过图表生成")
        print("   安装: pip install matplotlib")


if __name__ == "__main__":
    # 运行实验
    results = asyncio.run(run_dual_engine_simulation(ticks=500))  # 先用 500 ticks 快速验证

    # 生成图表
    generate_plots(results)

    # 打印摘要
    print("\n" + "="*60)
    print("实验摘要")
    print("="*60)

    final_fsrs = results["time_series"][-1]["fsrs"]
    final_ee = results["time_series"][-1]["ee"]

    print(f"\n最终状态 (tick {results['ticks']}):")
    print(f"  {'Metric':<20} {'FSRS':<15} {'EE':<15} {'差异':<10}")
    print(f"  {'-'*60}")
    print(f"  {'avg_R':<20} {final_fsrs['avg_R']:<15.3f} {final_ee['avg_R']:<15.3f} {final_fsrs['avg_R']-final_ee['avg_R']:+.3f}")
    print(f"  {'avg_S':<20} {final_fsrs['avg_S']:<15.1f} {final_ee['avg_S']:<15.1f} {final_fsrs['avg_S']-final_ee['avg_S']:+.1f}")
    print(f"  {'avg_leverage':<20} {final_fsrs['avg_leverage']:<15.2f} {final_ee['avg_leverage']:<15.2f} {final_fsrs['avg_leverage']-final_ee['avg_leverage']:+.2f}")

    print("\n[OK] Phase 1 验证完成!")
