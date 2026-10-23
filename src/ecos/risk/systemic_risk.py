"""Systemic Risk Monitor - 系统性风险监测

监测整个金融系统的稳定性，识别关键节点（Too Big To Fail）
计算网络级风险指标：集中度、关联性、脆弱性
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SystemicMetrics:
    """系统性风险指标快照"""
    tick: int
    timestamp: str
    connectivity: float           # 网络连接度 (0-1)
    concentration: float          # 中心性集中度 (0-1)
    cascade_potential: float      # 连锁反应潜力 (0-1)
    overall_risk: float           # 整体风险 (0-1)
    critical_nodes: List[str]     # 关键节点ID列表
    warnings: List[str] = field(default_factory=list)


class SystemicRiskMonitor:
    """
    系统性风险监测器
    
    功能:
    1. 识别系统关键节点（高连接、高杠杆）
    2. 计算网络级风险指标
    3. 评估传染路径（如果节点X失败，会影响谁）
    4. 触发宏观审慎干预建议
    """

    def __init__(self, world_graph, risk_engine=None):
        """
        初始化系统性风险监测器

        Args:
            world_graph: WorldStateGraph 实例
            risk_engine: RiskDiffusionEngine 实例（可选）
        """
        self.world = world_graph
        self.risk_engine = risk_engine
        self.metrics_history: List[SystemicMetrics] = []
        self.critical_nodes_cache: Dict[int, List[str]] = {}
        
        logger.info("📊 Systemic Risk Monitor initialized")

    def calculate_metrics(self, tick: int) -> SystemicMetrics:
        """
        计算当前 tick 的系统性风险指标

        Returns:
            SystemicMetrics 对象
        """
        from datetime import datetime
        
        # 1. 网络连接度 = 实际边数 / 最大可能边数
        n_nodes = self.world.graph.number_of_nodes()
        max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 1
        actual_edges = self.world.graph.number_of_edges()
        connectivity = actual_edges / max_edges if max_edges > 0 else 0

        # 2. 度中心性 (degree centrality) 计算集中度
        degrees = [self.world.graph.degree(n) for n in self.world.graph.nodes()]
        if degrees:
            max_degree = max(degrees)
            total_degree = sum(degrees)
            concentration = max_degree / total_degree if total_degree > 0 else 0
        else:
            concentration = 0

        # 3. 连锁潜力 = 平均邻居数 × 连通性
        avg_neighbors = np.mean(degrees) if degrees else 0
        cascade_potential = avg_neighbors * connectivity

        # 4. 整体风险 = max(浓度, 风险感染比例) × 连锁潜力
        if self.risk_engine:
            risk_summary = self.risk_engine.risk_history[-1] if self.risk_engine.risk_history else {}
            infected_ratio = risk_summary.get("infected", 0) / max(1, len(self.risk_engine.risk_nodes))
            overall_risk = max(concentration, infected_ratio) * (1 + cascade_potential)
        else:
            overall_risk = concentration * (1 + cascade_potential)

        overall_risk = min(1.0, overall_risk)

        # 5. 识别关键节点 (Too Big To Fail)
        critical_nodes = self._identify_critical_nodes()

        # 6. 生成警告
        warnings = self._generate_warnings(connectivity, concentration, overall_risk, critical_nodes)

        metrics = SystemicMetrics(
            tick=tick,
            timestamp=datetime.now().isoformat(),
            connectivity=connectivity,
            concentration=concentration,
            cascade_potential=cascade_potential,
            overall_risk=overall_risk,
            critical_nodes=critical_nodes,
            warnings=warnings
        )

        self.metrics_history.append(metrics)
        self.critical_nodes_cache[tick] = critical_nodes

        return metrics

    def _identify_critical_nodes(self, top_k: int = 5) -> List[str]:
        """
        识别系统中最关键的节点
        
        标准:
        - 度中心性最高（连接最多）
        - 持有最大资金/资产
        - 风险暴露最高
        """
        scores = {}

        for node_id, data in self.world.graph.nodes(data=True):
            if data.get("type") != "agent":
                continue

            score = 0

            # 1. 网络中心性 (度)
            degree = self.world.graph.degree(node_id)
            score += degree * 0.3

            # 2. 资金规模
            balance = data.get("balance", 0)
            score += (balance / 100000) * 0.4  # 标准化

            # 3. 风险水平（如果 risk_engine 可用）
            if self.risk_engine:
                risk_node = self.risk_engine.risk_nodes.get(node_id)
                if risk_node:
                    score += risk_node.risk_level * 0.3

            scores[node_id] = score

        # 返回 top_k 节点
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [node_id for node_id, score in sorted_nodes[:top_k]]

    def _generate_warnings(self, connectivity: float, concentration: float,
                          overall_risk: float, critical_nodes: List[str]) -> List[str]:
        """生成风险警告"""
        warnings = []

        if connectivity > 0.8:
            warnings.append("High network connectivity - contagion risk elevated")

        if concentration > 0.5:
            warnings.append(f"High concentration: top node controls {concentration*100:.1f}% of connections")

        if overall_risk > 0.7:
            warnings.append(f"CRITICAL: Systemic risk at {overall_risk:.2f}")

        if len(critical_nodes) > 0:
            warnings.append(f"Critical nodes identified: {', '.join(critical_nodes[:3])}")

        return warnings

    def get_cascade_impact(self, failed_node_id: str) -> Dict:
        """
        计算如果某个节点失败，会牵连多少其他节点
        
        Returns:
            {"direct": 直接受影响数量, "indirect": 间接影响, "total": 总计}
        """
        if failed_node_id not in self.world.graph:
            return {"direct": 0, "indirect": 0, "total": 0}

        # 直接邻居
        neighbors = list(self.world.graph.neighbors(failed_node_id))
        direct = len(neighbors)

        # 二层邻居（间接）
        indirect_set = set()
        for neighbor in neighbors:
            if neighbor in self.world.graph:
                second_neighbors = list(self.world.graph.neighbors(neighbor))
                indirect_set.update(second_neighbors)
        
        # 排除自身和直接邻居
        indirect_set.discard(failed_node_id)
        indirect_set = indirect_set - set(neighbors)
        indirect = len(indirect_set)

        return {
            "direct": direct,
            "indirect": indirect,
            "total": direct + indirect,
            "direct_list": neighbors,
            "indirect_list": list(indirect_set)
        }

    def get_topology_report(self) -> Dict:
        """
        生成网络拓扑报告（用于稳定性分析）
        """
        n_nodes = self.world.graph.number_of_nodes()
        n_edges = self.world.graph.number_of_edges()
        density = nx.density(self.world.graph) if n_nodes > 1 else 0

        # 计算平均聚类系数（三角关系比例）
        try:
            import networkx as nx
            clustering = nx.average_clustering(self.world.graph.to_undirected())
        except:
            clustering = 0

        # 识别连通分量
        try:
            import networkx as nx
            components = list(nx.connected_components(self.world.graph.to_undirected()))
            largest_component = max(components, key=len) if components else set()
            largest_pct = len(largest_component) / n_nodes if n_nodes > 0 else 0
        except:
            components = []
            largest_pct = 1.0

        return {
            "nodes": n_nodes,
            "edges": n_edges,
            "density": density,
            "clustering_coefficient": clustering,
            "connected_components": len(components),
            "largest_component_pct": largest_pct,
            "avg_degree": n_edges * 2 / n_nodes if n_nodes > 0 else 0
        }

    def reset(self):
        """重置监测器"""
        self.metrics_history.clear()
        self.critical_nodes_cache.clear()
        logger.info("🔄 Systemic Risk Monitor reset")
