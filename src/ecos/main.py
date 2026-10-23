"""ECOS - Economic Civilization OS
主入口点（集成三省六部治理）"""

import asyncio
import argparse
import json
import random
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path

# 状态检查点持久化 (fail-closed 友好: 读路径永不抛异常)
from ecos.core.persistence import (
    load_checkpoint,
    save_checkpoint,
    extract_world_snapshot,
    DEFAULT_CHECKPOINT_PATH,
)

# Metrics
from ecos.core.metrics import (
    start_metrics_server,
    update_world_metrics,
    update_agent_metrics,
    update_risk_metrics,
    update_systemic_risk,
    record_trade,
    AGENTS_CREATED_TOTAL,
    TRADES_TOTAL,
    TREASURY_BALANCE,
    TAX_COLLECTED_TOTAL,
    INTERVENTIONS_TOTAL
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO"):
    """配置日志级别"""
    logging.getLogger().setLevel(getattr(logging, level.upper()))


async def run_simulation(config: Dict, checkpoint_interval: int = 100):
    """运行模拟模式（含治理层） - 编排: 构建世界 / 运行循环 / 汇总

    Args:
        config: 模拟配置字典
        checkpoint_interval: 每隔多少 tick 持久化一次世界状态快照到
            ``output/checkpoint.json``（默认 100）。设为 0/负数则关闭检查点。
    """
    ctx = _build_world(config)
    governance_summaries = _run_simulation_loop(config, ctx, checkpoint_interval)
    return _summarize_simulation(config, ctx, governance_summaries)


def _init_distributed_mode(config: Dict):
    """初始化分布式模式(Redis);失败则降级为单机并关闭该标志"""
    redis_client = None
    if config.get("enable_distributed", False):
        try:
            import redis
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            redis_client.ping()
            logger.info("🔄 Distributed mode enabled (Redis connected)")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None
            config["enable_distributed"] = False
    return redis_client


def _init_core_components(config: Dict):
    """初始化 WorldStateGraph / EventBus / SimClock"""
    from ecos.core.world_state import WorldStateGraph
    from ecos.core.event_bus import EventBus
    from ecos.core.clock import SimClock
    world = WorldStateGraph(name="Simulation World")
    event_bus = EventBus(redis_url=config.get("redis_url", "redis://localhost:6379/0"))
    clock = SimClock(speed=config.get("speed", 1.0))
    return world, event_bus, clock


def _load_market_config(config: Dict):
    """加载市场配置(JSON);缺失则回退默认"""
    market_config_path = config.get("market_config", "config/markets.json")
    try:
        with open(market_config_path, 'r') as f:
            market_config = json.load(f)
        logger.info(f"✅ Loaded market config from {market_config_path}")
        # 统计各类资产数量
        for category, data in market_config.get("markets", {}).items():
            symbols = list(data.get("base_prices", {}).keys())
            logger.info(f"   {category.capitalize()}: {len(symbols)} assets")
    except FileNotFoundError:
        logger.warning(f"⚠️  Market config not found, using defaults")
        market_config = None
    return market_config


def _create_market_nodes(world, market_config):
    """从市场配置创建所有市场节点,返回 (symbols, created_markets)"""
    symbols = []
    if market_config:
        for category, data in market_config.get("markets", {}).items():
            symbols.extend(list(data.get("base_prices", {}).keys()))
    else:
        symbols = ["BTC", "ETH", "XMR"]

    created_markets = 0
    for symbol in symbols:
        # 确定资产类别和参数
        if market_config:
            price = 1000
            volatility = 0.01
            category = "unknown"
            for cat, data in market_config.get("markets", {}).items():
                if symbol in data.get("base_prices", {}):
                    price = data["base_prices"][symbol]
                    volatility = data.get("volatility", 0.01)
                    category = cat
                    break
        else:
            price = random.uniform(100, 1000)
            volatility = 0.02
            category = "crypto"

        world.add_node(
            node_id=f"market:{symbol}",
            node_type="market",
            attributes={
                "symbol": symbol,
                "price": round(price * random.uniform(0.9, 1.1), 2),
                "change": 0.0,
                "volume": random.uniform(1e6, 1e7) if category == "crypto" else random.uniform(1e5, 1e6),
                "liquidity": random.uniform(0.6, 1.0),
                "bid": round(price * 0.999, 2),
                "ask": round(price * 1.001, 2),
                "category": category,
                "volatility": volatility
            }
        )
        created_markets += 1

    logger.info(f"✅ Created {created_markets} market nodes across {len(set(symbols))} symbols")
    return symbols, created_markets


def _create_agents(config: Dict):
    """按 agent_distribution 创建 Retail / Institution / MarketMaker 三类 Agent"""
    agents = []
    agent_distribution = config.get("agent_distribution", {
        "retail": 0.6,
        "institution": 0.3,
        "market_maker": 0.1
    })

    counts = {k: int(config.get("agents", 10) * v) for k, v in agent_distribution.items()}
    remainder = config.get("agents", 10) - sum(counts.values())
    if remainder > 0:
        counts["retail"] += remainder

    # Retail Agents
    for i in range(counts.get("retail", 0)):
        agent = RetailAgent(
            name=f"Retail_{i+1:04d}",
            config={
                "initial_balance": 50000,  # 增加初始资金以支持高价股
                "fomo_factor": 0.8,  # 追涨系数（从 0.5 提升）
                "panic_factor": 0.8,
                "position_size_pct": 0.05,  # 单仓比例（从 2% 提升至 5% 以增加交易量）
                "buy_threshold": 0.001,
                "panic_threshold": -0.05,
                "random_noise": 0.2
            }
        )
        agents.append(agent)

    # Institution Agents
    for i in range(counts.get("institution", 0)):
        agent = InstitutionAgent(
            name=f"Inst_{i+1:04d}",
            config={"initial_balance": 1_000_000, "position_size_pct": 0.01}
        )
        agents.append(agent)

    # Market Maker Agents
    for i in range(counts.get("market_maker", 0)):
        agent = MarketMakerAgent(
            name=f"MM_{i+1:04d}",
            config={"initial_balance": 500_000, "order_size": 10, "position_size_pct": 0.05}
        )
        agents.append(agent)

    logger.info(f"✅ Created {len(agents)} agents (R:{counts.get('retail',0)}, I:{counts.get('institution',0)}, MM:{counts.get('market_maker',0)})")
    return agents


def _start_metrics_and_recorders(config: Dict, world, agents):
    """启动 Prometheus 指标服务器并初始化世界/Agent 指标记录器"""
    # 启动 Prometheus metrics 服务器 (端口 9090)
    if config.get("enable_metrics", True):
        metrics_port = config.get("metrics_port", 9090)
        start_metrics_server(metrics_port)
        logger.info(f"📊 Metrics server started on :{metrics_port}")

    # 初始化指标记录器
    update_world_metrics(world)
    update_agent_metrics(agents)


def _init_neo4j(config: Dict):
    """初始化 Neo4j 驱动(可选);失败则跳过持久化"""
    # 注意: 既有实现在此处将注入的 neo4j_driver 显式置空后按需重建, 行为予以保留
    neo4j_driver = None
    if config.get("enable_neo4j", False):
        try:
            from neo4j import GraphDatabase
            neo4j_uri = "bolt://localhost:7687"  # 从环境变量读取
            neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "ecos123"))
            logger.info("🗄️  Neo4j persistence enabled (bolt://localhost:7687)")
        except ImportError:
            logger.warning("neo4j driver not installed, skipping persistence")
            neo4j_driver = None
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            neo4j_driver = None
    return neo4j_driver


def _init_governance(config, world, agents):
    """初始化治理层(三省六部);可关闭"""
    governance_enabled = config.get("enable_governance", True)
    governance_manager = None
    if governance_enabled:
        from ecos.governance.governance_manager import GovernanceManager
        governance_manager = GovernanceManager(world=world, agents=agents)
        logger.info("🏛️  Governance Layer activated (三省六部)")
    return governance_manager


def _build_world(config: Dict) -> Dict:
    """构建模拟世界: 分布式 / 核心组件 / 市场 / Agent / 指标 / Neo4j / 治理层"""
    _init_distributed_mode(config)
    world, event_bus, clock = _init_core_components(config)
    market_config = _load_market_config(config)
    symbols, created_markets = _create_market_nodes(world, market_config)
    agents = _create_agents(config)
    _start_metrics_and_recorders(config, world, agents)
    neo4j_driver = _init_neo4j(config)
    governance_manager = _init_governance(config, world, agents)

    # 最佳努力从最近的检查点恢复世界状态 (fail-closed 友好: 失败则保留新世界)
    try:
        _restore_world_from_checkpoint(world)
    except Exception as e:
        logger.warning(f"⚠️  Checkpoint restore skipped, starting fresh: {e}")

    return {
        "world": world,
        "clock": clock,
        "agents": agents,
        "neo4j_driver": neo4j_driver,
        "governance_manager": governance_manager,
        "created_markets": created_markets,
    }


def _restore_world_from_checkpoint(world):
    """从 ``output/checkpoint.json`` 最佳努力恢复世界图与 current_tick。

    任何失败都只记录警告并保留刚构建的新世界,确保模拟仍可运行。
    不会抛出异常;读取路径由 persistence.load_checkpoint 保证永不抛错。
    """
    try:
        snapshot = load_checkpoint(DEFAULT_CHECKPOINT_PATH)
        if not snapshot:
            return
        nodes = snapshot.get("nodes") or []
        edges = snapshot.get("edges") or []
        if not nodes:
            logger.info("♻️  Checkpoint empty, starting fresh")
            return

        # 用检查点内容替换刚构建的世界
        world.clear()
        for n in nodes:
            nid = n.get("id")
            if nid is None:
                continue
            node_type = n.get("type", "unknown")
            attrs = dict(n.get("attrs") or {})
            attrs["type"] = node_type
            try:
                world.add_node(nid, node_type, attrs)
            except Exception as e:
                logger.warning(f"Failed to restore node {nid}: {e}")

        for e in edges:
            source = e.get("source")
            target = e.get("target")
            if source is None or target is None:
                continue
            attrs = dict(e.get("attrs") or {})
            edge_type = attrs.pop("type", "unknown")
            try:
                world.add_edge(source, target, edge_type, **attrs)
            except Exception as exc:
                logger.warning(f"Failed to restore edge {source}->{target}: {exc}")

        restored_tick = int(snapshot.get("current_tick", 0) or 0)
        world.current_tick = restored_tick
        logger.info(
            f"♻️  Restored checkpoint: {len(nodes)} nodes, {len(edges)} edges, tick {restored_tick}"
        )
    except Exception as e:
        logger.warning(f"⚠️  Checkpoint restore failed, starting fresh: {e}")


def _update_market_prices(world):
    """基于波动率批量更新所有市场价格,缓存仅重建一次"""
    world._invalidate_market_cache()  # 手动失效
    for node_id, data in world.graph.nodes(data=True):
        if data.get("type") == "market":
            volatility = data.get("volatility", 0.02)
            change_pct = random.uniform(-volatility, volatility)
            old_price = data["price"]
            new_price = old_price * (1 + change_pct)
            world.update_node(node_id, {
                "price": round(new_price, 2),
                "change": change_pct
            }, invalidate_cache=False)  # 不触发中间失效


def _step_agents(agents, world, tick):
    """Agent 感知-决策-行动循环,返回 (total_pnl, active_agents)"""
    total_pnl = 0
    active_agents = 0
    for agent in agents:
        if not getattr(agent, 'active', True):
            continue
        active_agents += 1

        # Set simulation tick for tick-based memory engines
        agent.sim_tick = tick

        try:
            perception = agent.perceive(world)  # 直接传递 WorldStateGraph，避免 to_dict() 序列化开销
            decision = agent.decide(perception)
            result = agent.act(decision, world)
            total_pnl += result.get("total_pnl", 0)

            # 记录交易指标
            for trade in result.get("trades", []):
                symbol = trade.get("symbol", "UNKNOWN")
                direction = trade.get("direction", "unknown")
                size = trade.get("size", 0)
                price = trade.get("price", 0)
                volume = size * price
                record_trade(symbol, direction, volume)

            agent.learn({
                "perception": perception,
                "decision": decision,
                "result": result
            })
        except Exception as e:
            logger.error(f"❌ Agent {agent.name} error: {e}")
            agent.stats["errors"] = agent.stats.get("errors", 0) + 1
    return total_pnl, active_agents


def _run_governance_tick(config, governance_manager, tick, governance_summaries):
    """执行治理层 tick 并记录摘要"""
    governance_interval = config.get("governance_interval", 1)
    if governance_manager and (tick + 1) % governance_interval == 0:
        gov_summary = governance_manager.tick(tick + 1)
        governance_summaries.append(gov_summary)

        treasury = gov_summary.get("budget_changes", {}).get("treasury_balance", 0)
        interventions = len(gov_summary.get("interventions", []))
        anomalies = gov_summary.get("anomalies", 0)  # int count
        logger.info(f"  [🏛️ Gov] Treasury: ${treasury:,.0f} | Interventions: {interventions} | Anomalies: {anomalies}")


def _update_prometheus_metrics(config, world, agents, governance_manager):
    """每 tick 更新 Prometheus 指标(世界 / Agent / 风险 / 国库 / 系统性)"""
    update_world_metrics(world)
    update_agent_metrics(agents)
    # Risk metrics (if available)
    if governance_manager and hasattr(governance_manager, 'risk_engine'):
        update_risk_metrics(governance_manager.risk_engine)
    # Treasury & tax
    if governance_manager:
        treasury = governance_manager.treasury.balance if hasattr(governance_manager, 'treasury') else 0
        TREASURY_BALANCE.set(treasury)
        TAX_COLLECTED_TOTAL.inc(governance_manager.treasury.total_taxes_collected if hasattr(governance_manager, 'treasury') else 0)
    # Systemic risk (if available)
    if governance_manager and hasattr(governance_manager, 'risk_monitor'):
        risk_score = governance_manager.risk_monitor.metrics_history[-1].overall_risk if governance_manager.risk_monitor.metrics_history else 0
        update_systemic_risk(risk_score)


def _run_simulation_loop(config, ctx, checkpoint_interval: int = 100):
    """运行主模拟循环(tick 迭代)"""
    world = ctx["world"]
    clock = ctx["clock"]
    agents = ctx["agents"]
    neo4j_driver = ctx["neo4j_driver"]
    governance_manager = ctx["governance_manager"]

    # 运行模拟
    ticks = config.get("ticks", 100)
    governance_summaries = []

    for tick in range(ticks):
        logger.info(f"\n{'='*60}")
        logger.info(f"Tick {tick+1}/{ticks}")

        # 1. 更新市场价格（基于波动率）
        _update_market_prices(world)

        # 2. Agent 感知-决策-行动
        total_pnl, active_agents = _step_agents(agents, world, tick)

        # 3. 治理层执行（每 tick 或间隔）
        _run_governance_tick(config, governance_manager, tick, governance_summaries)

        # 4. 统计输出
        avg_balance = sum(a.balance for a in agents) / len(agents) if agents else 0
        logger.info(f"  📊 Summary: Active={active_agents}/{len(agents)} | AvgBal=${avg_balance:,.2f} | PnL=${total_pnl:,.2f}")

        # 5. 更新 Prometheus 指标
        _update_prometheus_metrics(config, world, agents, governance_manager)

        # 推进时钟
        clock.tick()

        # Neo4j 持久化（每 100 ticks）
        if config.get("enable_neo4j", False) and neo4j_driver and (tick + 1) % 100 == 0:
            try:
                world.persist_to_neo4j(neo4j_driver)
            except Exception as e:
                logger.error(f"Neo4j persistence failed: {e}")

        # Neo4j 持久化（每 100 ticks）
        if neo4j_driver and (tick + 1) % 100 == 0:
            try:
                world.persist_to_neo4j(neo4j_driver)
            except Exception as e:
                logger.error(f"Neo4j persistence failed: {e}")

        # 检查点持久化 (每隔 checkpoint_interval 个 tick; 失败绝不中断模拟)
        if checkpoint_interval and (tick + 1) % checkpoint_interval == 0:
            try:
                world.current_tick = tick
                save_checkpoint(
                    extract_world_snapshot(world),
                    DEFAULT_CHECKPOINT_PATH,
                )
                logger.info(f"  💾 Checkpoint saved (tick {tick + 1}) -> {DEFAULT_CHECKPOINT_PATH}")
            except Exception as e:
                logger.error(f"Checkpoint save failed: {e}")

    return governance_summaries


def _summarize_simulation(config, ctx, governance_summaries):
    """最终报告 + 保存世界/治理状态,返回结果字典"""
    world = ctx["world"]
    agents = ctx["agents"]
    governance_manager = ctx["governance_manager"]
    created_markets = ctx["created_markets"]

    # 最终报告
    logger.info("\n" + "="*60)
    logger.info("SIMULATION COMPLETE")
    logger.info("="*60)
    for agent in agents:
        info = agent.get_info()
        logger.info(f"  {agent.name}: balance=${info['balance']:,.2f}, positions={len(info['position'])}, avg_reward={info.get('avg_reward',0):.2f}")

    # 保存世界状态
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    world.save(output_dir / "world_final.json")
    logger.info("✅ World state saved to output/world_final.json")

    # 保存治理报告
    if governance_manager:
        governance_report = governance_manager.get_performance_report()
        with open(output_dir / "governance_report.json", 'w') as f:
            json.dump(governance_report, f, indent=2)
        logger.info("✅ Governance report saved to output/governance_report.json")

    governance_enabled = config.get("enable_governance", True)
    return {
        "ticks": config.get("ticks", 100),
        "agents": len(agents),
        "world_nodes": world.graph.number_of_nodes(),
        "world_edges": world.graph.number_of_edges(),
        "markets_created": created_markets,
        "governance_enabled": governance_enabled,
        "governance_decisions": len(governance_summaries)
    }


def run_api(config: Dict):
    """运行 API 模式（FastAPI）"""
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI(title="ECOS API", version="0.1.0-alpha")

    @app.get("/")
    def root():
        return {"message": "ECOS API", "status": "running"}

    @app.get("/health")
    def health():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/world/stats")
    def world_stats():
        # TODO: 返回实时世界状态统计
        return {"nodes": 0, "edges": 0, "agents": 0}

    logger.info("🚀 Starting ECOS API server on :8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="ECOS - Economic Civilization OS")
    parser.add_argument("--mode", choices=["simulation", "api", "interactive"],
                       default="simulation", help="运行模式")
    parser.add_argument("--ticks", type=int, default=100, help="模拟周期数")
    parser.add_argument("--agents", type=int, default=10, help="Agent 数量")
    parser.add_argument("--speed", type=float, default=1.0, help="时间流速倍率")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0", help="Redis 地址")
    parser.add_argument("--market-config", default="config/markets.json", help="Market config path")
    parser.add_argument("--no-governance", action="store_true", help="Disable governance layer")
    parser.add_argument("--distributed", action="store_true", help="Enable distributed Agent Worker mode")
    parser.add_argument("--neo4j", action="store_true", help="Enable Neo4j persistence")
    parser.add_argument("--log-level", default="INFO", help="日志级别")

    args = parser.parse_args()

    # 构建配置
    config = {
        "mode": args.mode,
        "ticks": args.ticks,
        "agents": args.agents,
        "speed": args.speed,
        "redis_url": args.redis_url,
        "market_config": args.market_config,
        "enable_governance": not args.no_governance,
        "governance_interval": 1,
        "enable_distributed": args.distributed,
        "enable_neo4j": args.neo4j,
        "agent_distribution": {
            "retail": 0.6,
            "institution": 0.3,
            "market_maker": 0.1
        }
    }

    setup_logging(args.log_level)

    try:
        if args.mode == "simulation":
            logger.info("="*60)
            logger.info("ECOS SIMULATION CONFIG")
            logger.info("="*60)
            logger.info(f"Agents     : {args.agents}")
            logger.info(f"Ticks      : {args.ticks}")
            logger.info(f"Governance : {'ENABLED' if config['enable_governance'] else 'DISABLED'}")
            logger.info(f"Market Config: {args.market_config}")
            logger.info("="*60)

            # 初始化 Neo4j driver（如果启用）
            neo4j_driver = None
            if config["enable_neo4j"]:
                try:
                    from neo4j import GraphDatabase
                    neo4j_uri = "bolt://localhost:7687"
                    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "ecos123"))
                    config["neo4j_driver"] = neo4j_driver
                    logger.info("🗄️  Neo4j persistence enabled (bolt://localhost:7687)")
                except ImportError:
                    logger.warning("neo4j driver not installed, skipping persistence")
                    config["neo4j_driver"] = None
                except Exception as e:
                    logger.error(f"Failed to connect to Neo4j: {e}")
                    config["neo4j_driver"] = None

            result = asyncio.run(run_simulation(config))
            
            # 清理 Neo4j 连接
            if neo4j_driver:
                try:
                    neo4j_driver.close()
                except:
                    pass
            print(f"\nSimulation complete: {json.dumps(result, indent=2)}")
            return 0
        elif args.mode == "api":
            run_api(config)
        elif args.mode == "interactive":
            logger.info("Interactive mode - not implemented yet")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
