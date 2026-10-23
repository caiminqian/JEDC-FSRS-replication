"""Risk Diffusion Engine - 风险扩散模型

基于 SIR (Susceptible-Infected-Recovered) 流行病学模型的
风险在金融系统网络中的扩散模拟。

节点状态:
  S (Susceptible): 易感 - 尚未感染风险
  I (Infected): 感染 - 携带风险，可传染给他人
  R (Recovered): 恢复/免疫 - 已摆脱风险或破产

扩散机制:
  风险通过资金流 (capital_flow) 和信息流 (info_flow) 边传播
  传播概率取决于:
    - 连接强度 (edge weight)
    - 目标节点脆弱性 (node vulnerability)
    - 全局风险水平 (systemic risk)

参考论文:
  - "Financial Contagion in Networks" (2010)
  - "Systemic Risk in Financial Networks" (2016)
"""

import random
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskState(Enum):
    """风险状态枚举"""
    SUSCEPTIBLE = "S"  # 易感
    INFECTED = "I"     # 感染（风险暴露）
    RECOVERED = "R"   # 恢复/已破产/免疫
    ACTIVE = "A"       # 正常运行（无风险）


@dataclass
class RiskEvent:
    """风险事件"""
    event_id: str
    source_agent_id: str
    target_agent_id: str
    risk_type: str          # "liquidity", "counterparty", "market", "operational"
    infection_probability: float
    timestamp: int
    magnitude: float = 1.0  # 风险强度 0-1
    metadata: Dict = field(default_factory=dict)


@dataclass
class RiskNode:
    """风险节点属性"""
    agent_id: str
    state: RiskState = RiskState.ACTIVE
    risk_level: float = 0.0          # 当前风险值 0-1
    vulnerability: float = 0.5       # 脆弱性 0-1 (资产/杠杆)
    resilience: float = 0.3          # 恢复力 0-1
    infection_time: Optional[int] = None
    recovery_time: Optional[int] = None


class RiskDiffusionEngine:
    """
    风险扩散引擎
    
    每个 tick 执行:
    1. 计算所有节点的风险暴露
    2. 沿图边传播风险
    3. 更新节点状态（感染/恢复/破产）
    4. 记录传播路径用于事后分析
    """

    def __init__(self, world_graph, config: Dict = None, rng: random.Random = None):
        """
        初始化风险扩散引擎

        Args:
            world_graph: WorldStateGraph 实例
            config: 配置参数
        """
        self.world = world_graph
        self.config = config or {}
        self.risk_nodes: Dict[str, RiskNode] = {}  # agent_id -> RiskNode
        self.risk_history: List[Dict] = []          # 每 tick 的系统性风险记录
        self.events: List[RiskEvent] = []           # 风险事件日志
        
        # 参数
        self.base_infection_rate = self.config.get("base_infection_rate", 0.05)  # 基础感染率
        # RNG for stochastic events
        import random
        self.rng = rng or random
        self.recovery_rate = self.config.get("recovery_rate", 0.1)              # 自然恢复率
        self.bankruptcy_threshold = self.config.get("bankruptcy_threshold", 0.9)  # 破产风险阈值
        self.intervention_threshold = self.config.get("intervention_threshold", 0.7)  # 干预阈值
        
        logger.info("🦠 Risk Diffusion Engine initialized")

    def initialize_agents(self, agents: List):
        """
        为所有 Agent 初始化风险节点

        Args:
            agents: Agent 对象列表
        """
        for agent in agents:
            vulnerability = self._calculate_vulnerability(agent)
            resilience = self._calculate_resilience(agent)
            
            node = RiskNode(
                agent_id=agent.agent_id,
                state=RiskState.ACTIVE,
                risk_level=0.0,
                vulnerability=vulnerability,
                resilience=resilience
            )
            self.risk_nodes[agent.agent_id] = node
        
        logger.info(f"✅ Initialized risk nodes for {len(self.risk_nodes)} agents")

    def _calculate_vulnerability(self, agent) -> float:
        """
        计算 Agent 脆弱性
        
        脆弱性高的 Agent:
        - 高杠杆 (高负债/低资本)
        - 高集中度 (单一持仓占比高)
        - 低流动性资产
        """
        vulnerability = 0.5  # 默认中等
        
        # 基于余额/负债（如果有负债数据）
        balance = getattr(agent, 'balance', 10000)
        if balance < 1000:
            vulnerability += 0.3
        elif balance > 100000:
            vulnerability -= 0.2
        
        # 基于持仓集中度
        position = getattr(agent, 'position', {})
        if position:
            max_position_pct = max(position.values()) / sum(position.values()) if sum(position.values()) > 0 else 0
            vulnerability += max_position_pct * 0.5
        
        # 基于风险偏好配置
        risk_profile = getattr(agent, 'risk_profile', 'medium')
        profile_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        vulnerability = vulnerability * 0.5 + profile_map.get(risk_profile, 0.5) * 0.5
        
        return min(1.0, max(0.0, vulnerability))

    def _calculate_resilience(self, agent) -> float:
        """
        计算 Agent 恢复力
        
        恢复力强的 Agent:
        - 高资本
        - 多样化持仓
        - 低杠杆
        """
        resilience = 0.5
        
        balance = getattr(agent, 'balance', 10000)
        if balance > 100000:
            resilience += 0.3
        elif balance < 5000:
            resilience -= 0.3
        
        # 多样化持仓提高恢复力
        position = getattr(agent, 'position', {})
        if len(position) >= 5:
            resilience += 0.2
        elif len(position) <= 1:
            resilience -= 0.2
        
        return min(1.0, max(0.0, resilience))

    def tick(self, world, tick: int) -> Dict:
        """Execute one tick of risk diffusion (supports WorldStateGraph or dict)"""
        # 兼容性：支持传入 WorldStateGraph 或 dict
        if hasattr(world, 'to_dict'):
            world_state = world.to_dict()
            world_graph = world.graph
        else:
            world_state = world
            world_graph = None

        summary = {
            "tick": tick,
            "new_infections": 0,
            "new_recoveries": 0,
            "bankruptcies": 0,
            "systemic_risk_index": 0.0,
            "intervention_triggered": False,
            "susceptible": 0,
            "infected": 0,
            "recovered": 0,
            "active": 0
        }

        # 1. 更新风险暴露
        self._update_risk_exposure(world_state)

        # 2. 风险传播（使用图结构或 world_state 中的边）
        new_infections = 0
        if world_graph is not None:
            # 直接使用图遍历（高效）
            for u, v, data in world_graph.edges(data=True):
                if data.get("type") not in ["capital_flow", "info_flow"]:
                    continue
                source_node = self.risk_nodes.get(u)
                target_node = self.risk_nodes.get(v)
                if not source_node or not target_node:
                    continue
                if source_node.state in [RiskState.INFECTED, RiskState.ACTIVE] and source_node.risk_level > 0.3:
                    edge_weight = data.get("weight", 1.0)
                    infection_prob = self.base_infection_rate * source_node.risk_level * (1 - target_node.vulnerability) * edge_weight
                    if self.rng.random() < infection_prob and target_node.state == RiskState.ACTIVE:
                        target_node.state = RiskState.INFECTED
                        target_node.infection_time = tick
                        target_node.risk_level = max(target_node.risk_level, source_node.risk_level * 0.8)
                        new_infections += 1
        else:
            # 回退：从 world_state dict 提取（较慢）
            agents_data = {n[0]: n[1] for n in world_state.get("nodes", []) if isinstance(n, tuple) and n[1].get('type') == 'agent'}
            # 简化：不进行图遍历（仅占位）
            pass

        # 3. 状态更新
        recoveries, bankruptcies = self._update_states(tick)

        # 4. 系统性风险
        systemic_risk = self._calculate_systemic_risk()
        if systemic_risk > self.intervention_threshold:
            summary["intervention_triggered"] = True

        # 5. 统计
        for node in self.risk_nodes.values():
            if node.state == RiskState.SUSCEPTIBLE:
                summary["susceptible"] += 1
            elif node.state == RiskState.INFECTED:
                summary["infected"] += 1
            elif node.state == RiskState.RECOVERED:
                summary["recovered"] += 1
            elif node.state == RiskState.ACTIVE:
                summary["active"] += 1

        summary["new_infections"] = new_infections
        summary["new_recoveries"] = recoveries
        summary["bankruptcies"] = bankruptcies
        summary["systemic_risk_index"] = systemic_risk

        self.risk_history.append(summary)
        return summary

    def _update_risk_exposure(self, world_state: Dict):
        """
        根据市场波动更新 Agent 风险暴露
        
        逻辑: 如果 Agent 的持仓市值下跌超过阈值，则风险水平上升
        """
        agents_data = {n[0]: n[1] for n in world_state.get("nodes", []) if isinstance(n, tuple) and n[1].get('type') == 'agent'}

        for agent_id, node_data in agents_data.items():
            risk_node = self.risk_nodes.get(agent_id)
            if not risk_node or risk_node.state != RiskState.ACTIVE:
                continue

            # 获取 Agent 的 PnL
            pnl = node_data.get("stats", {}).get("rewards", 0)
            balance = node_data.get("balance", 10000)
            
            # 计算亏损比例
            if balance > 0:
                loss_ratio = max(0, -pnl) / balance if pnl < 0 else 0
                # 亏损越大，风险水平越高
                risk_node.risk_level = min(1.0, loss_ratio * 2)  # 亏损50%即风险1.0

    def _spread_risk(self, tick: int) -> int:
        """
        风险传播（沿资金流和信息流边）
        
        Returns:
            新感染的 Agent 数量
        """
        new_infections = 0
        
        # 遍历图中的边，寻找 capital_flow 和 info_flow 类型
        for u, v, key, data in self.world.graph.edges(keys=True, data=True):
            edge_type = data.get("type", "")
            if edge_type not in ["capital_flow", "info_flow"]:
                continue

            source_node = self.risk_nodes.get(u)
            target_node = self.risk_nodes.get(v)
            
            if not source_node or not target_node:
                continue

            # 只有已感染或高风险的源节点可以传播风险
            source_risk = source_node.risk_level
            if source_node.state in [RiskState.INFECTED, RiskState.ACTIVE] and source_risk > 0.3:
                # 传播概率 = 基础感染率 × 源风险 × (1 - 目标脆弱性) × 边权重
                edge_weight = data.get("weight", 1.0)
                infection_prob = self.base_infection_rate * source_risk * (1 - target_node.vulnerability) * edge_weight
                
                if self.rng.random() < infection_prob and target_node.state == RiskState.ACTIVE:
                    target_node.state = RiskState.INFECTED
                    target_node.infection_time = tick
                    target_node.risk_level = max(target_node.risk_level, source_risk * 0.8)
                    new_infections += 1

                    # 记录风险事件
                    event = RiskEvent(
                        event_id=f"RISK_{tick}_{len(self.events)}",
                        source_agent_id=u,
                        target_agent_id=v,
                        risk_type="contagion",
                        infection_probability=infection_prob,
                        timestamp=tick,
                        magnitude=source_risk
                    )
                    self.events.append(event)
                    logger.debug(f"  [Risk] {v} infected by {u} (prob={infection_prob:.3f})")

        return new_infections

    def _update_states(self, tick: int) -> Tuple[int, int]:
        """
        更新 Agent 状态
        
        Returns:
            (恢复数, 破产数)
        """
        recoveries = 0
        bankruptcies = 0

        for agent_id, node in self.risk_nodes.items():
            if node.state == RiskState.INFECTED:
                # 感染持续时间
                infected_duration = tick - (node.infection_time or tick)

                # 尝试恢复: 概率 = 恢复力 / (1 + 风险水平)
                recovery_prob = node.resilience / (1 + node.risk_level)
                if self.rng.random() < recovery_prob:
                    node.state = RiskState.RECOVERED
                    node.recovery_time = tick
                    node.risk_level = 0.0
                    recoveries += 1
                    logger.debug(f"  [Risk] {agent_id} recovered (tick {tick})")

                # 检查破产：风险水平超过阈值且脆弱性高
                if node.risk_level > self.bankruptcy_threshold and node.vulnerability > 0.7:
                    node.state = RiskState.RECOVERED  # 实际上已破产，视为退出
                    node.risk_level = 1.0
                    bankruptcies += 1
                    logger.warning(f"  [Risk] {agent_id} BANKRUPT (risk={node.risk_level:.2f})")

        return recoveries, bankruptcies

    def _calculate_systemic_risk(self) -> float:
        """
        计算系统性风险指数 (0-1)
        
        公式: 感染比例 × 平均风险水平 × 网络集中度
        """
        if not self.risk_nodes:
            return 0.0

        total = len(self.risk_nodes)
        infected_count = sum(1 for n in self.risk_nodes.values() if n.state == RiskState.INFECTED)
        infected_ratio = infected_count / total

        avg_risk = np.mean([n.risk_level for n in self.risk_nodes.values()])

        # 网络集中度: 连接度最高的节点占比
        degrees = [self.world.graph.degree(n) for n in self.world.graph.nodes()]
        max_degree = max(degrees) if degrees else 0
        concentration = max_degree / sum(degrees) if sum(degrees) > 0 else 0

        systemic_risk = infected_ratio * avg_risk * (1 + concentration)
        return min(1.0, systemic_risk)

    def get_infection_path(self) -> List[Tuple[str, str, int]]:
        """
        获取风险传播路径列表
        
        Returns:
            [(source, target, tick), ...]
        """
        paths = [(e.source_agent_id, e.target_agent_id, e.timestamp) for e in self.events]
        return paths

    def get_metrics(self) -> Dict:
        """获取风险指标"""
        if not self.risk_history:
            return {"status": "no_data"}

        latest = self.risk_history[-1]
        return {
            "tick": latest["tick"],
            "systemic_risk": latest["systemic_risk_index"],
            "infected_agents": latest["infected"],
            "active_agents": latest["active"],
            "recovered_agents": latest["recovered"],
            "total_events": len(self.events),
            "intervention_needed": latest["intervention_triggered"]
        }

    def reset(self):
        """重置风险扩散引擎（用于新模拟）"""
        self.risk_nodes.clear()
        self.risk_history.clear()
        self.events.clear()
        logger.info("🔄 Risk Diffusion Engine reset")
