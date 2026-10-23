"""Liquidity Risk Analyzer - 流动性风险分析器

监测市场流动性状况，识别流动性枯竭风险。
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LiquidityMetrics:
    """流动性指标"""
    market_id: str
    bid_ask_spread: float           # 买卖价差 (百分比)
    depth: float                    # 市场深度 (订单簿厚度)
    volume_ratio: float             # 成交量/平均值
    volatility: float               # 价格波动率
    liquidity_score: float = 1.0    # 流动性评分 (0-1, 越高越好)
    timestamp: str = ""


class LiquidityRiskAnalyzer:
    """
    流动性风险分析器
    
    监控每个市场的流动性指标，预警流动性危机。
    流动性枯竭特征:
    - 价差急剧扩大
    - 深度骤降
    - 成交量萎缩
    - 价格波动率飙升
    """

    def __init__(self, world_graph, config: Dict = None):
        """
        初始化流动性分析器

        Args:
            world_graph: WorldStateGraph 实例
            config: 配置参数
        """
        self.world = world_graph
        self.config = config or {}
        self.metrics_history: Dict[str, List[LiquidityMetrics]] = {}  # market_id -> [metrics]
        self.warnings: List[Dict] = []
        
        # 阈值配置
        self.spread_threshold = self.config.get("spread_threshold", 0.05)      # 价差 > 5% 预警
        self.depth_threshold = self.config.get("depth_threshold", 0.2)        # 深度 < 20% 预警
        self.volume_drop_threshold = self.config.get("volume_drop_threshold", 0.5)  # 成交量下降 50% 预警
        self.volatility_spike_threshold = self.config.get("volatility_spike", 0.03) # 波动率 > 3% 预警
        
        # 历史基准
        self.baseline_metrics: Dict[str, LiquidityMetrics] = {}
        self.baseline_window = self.config.get("baseline_window", 50)  # 前50个tick作为基准
        
        logger.info("💧 Liquidity Risk Analyzer initialized")

    def analyze(self, tick: int, world_state: Dict) -> Dict:
        """
        分析当前所有市场的流动性风险

        Args:
            tick: 当前tick
            world_state: 世界状态

        Returns:
            流动性风险报告
        """
        report = {
            "tick": tick,
            "markets": {},
            "high_risk_markets": [],
            "overall_liquidity_score": 0.0,
            "warnings": []
        }

        total_score = 0.0
        market_count = 0

        # 遍历市场节点
        for node in world_state.get("nodes", []):
            if not isinstance(node, dict):
                continue
            if node.get("type") != "market":
                continue

            symbol = node.get("symbol", "UNKNOWN")
            liquidity_metrics = self._compute_market_metrics(symbol, node, tick)
            
            # 保存历史
            if symbol not in self.metrics_history:
                self.metrics_history[symbol] = []
            self.metrics_history[symbol].append(liquidity_metrics)

            # 计算流动性评分 (0-1, 1=最好)
            score = self._calculate_liquidity_score(liquidity_metrics)
            liquidity_metrics.liquidity_score = score
            total_score += score
            market_count += 1

            report["markets"][symbol] = {
                "bid_ask_spread_pct": round(liquidity_metrics.bid_ask_spread * 100, 2),
                "depth": round(liquidity_metrics.depth, 4),
                "volume_ratio": round(liquidity_metrics.volume_ratio, 2),
                "volatility": round(liquidity_metrics.volatility * 100, 2),
                "liquidity_score": round(score, 3)
            }

            # 检查高风险
            if score < 0.3:
                report["high_risk_markets"].append(symbol)
                warning_msg = f"Market {symbol} liquidity critical (score={score:.3f})"
                report["warnings"].append(warning_msg)
                logger.warning(f"  [Liquidity] {warning_msg}")

        # 计算整体流动性
        report["overall_liquidity_score"] = total_score / max(1, market_count)

        # 合并全局警告
        report["warnings"].extend(self._generate_global_warnings(report))

        return report

    def _compute_market_metrics(self, symbol: str, data: Dict, tick: int) -> LiquidityMetrics:
        """
        计算单个市场的流动性指标
        """
        # 从市场节点获取基础数据
        price = data.get("price", 100)
        bid = data.get("bid", price * 0.999)
        ask = data.get("ask", price * 1.001)
        volume = data.get("volume", 1e6)
        liquidity = data.get("liquidity", 1.0)  # 0-1

        # 计算价差百分比
        bid_ask_spread = (ask - bid) / price if price > 0 else 0

        # 深度 = liquidity 字段（近似）
        depth = liquidity

        # 成交量比率：当前成交量 / 历史平均
        history = self.metrics_history.get(symbol, [])
        if len(history) >= 10:
            avg_volume = np.mean([m.volume_ratio for m in history[-10:]])
            volume_ratio = volume / max(avg_volume, 1)
        else:
            volume_ratio = 1.0

        # 波动率：从历史价格变化估计
        # 这里简化，实际可以从 world graph 计算价格变化的标准差
        volatility = abs(data.get("change", 0))

        metrics = LiquidityMetrics(
            market_id=symbol,
            bid_ask_spread=bid_ask_spread,
            depth=depth,
            volume_ratio=volume_ratio,
            volatility=volatility,
            timestamp=datetime.now().isoformat()
        )

        return metrics

    def _calculate_liquidity_score(self, metrics: LiquidityMetrics) -> float:
        """
        计算流动性综合评分 (0-1)
        
        评分逻辑:
        - 价差越窄得分越高
        - 深度越大得分越高
        - 成交量稳定得分高
        - 波动率低得分高
        """
        # 价差得分: 价差 < 0.1% -> 1分; > 5% -> 0分
        spread_score = max(0, 1 - (metrics.bid_ask_spread / 0.05))

        # 深度得分: 深度本身就是 0-1
        depth_score = metrics.depth

        # 成交量得分: 比率在 0.5-2.0 之间给满分，越低或越高扣分
        if 0.5 <= metrics.volume_ratio <= 2.0:
            volume_score = 1.0
        else:
            volume_score = max(0, 1 - abs(metrics.volume_ratio - 1.0))

        # 波动率得分: 波动率 < 1% -> 1分; > 10% -> 0分
        volatility_score = max(0, 1 - (metrics.volatility / 0.10))

        # 加权综合
        weights = {"spread": 0.3, "depth": 0.3, "volume": 0.2, "vol": 0.2}
        final_score = (
            spread_score * weights["spread"] +
            depth_score * weights["depth"] +
            volume_score * weights["volume"] +
            volatility_score * weights["vol"]
        )

        return final_score

    def _generate_global_warnings(self, report: Dict) -> List[str]:
        """生成全局流动性警告"""
        warnings = []

        overall = report["overall_liquidity_score"]
        if overall < 0.5:
            warnings.append(f"System-wide liquidity stress (score={overall:.2f})")

        high_risk_count = len(report["high_risk_markets"])
        if high_risk_count > 3:
            warnings.append(f"Multiple markets ({high_risk_count}) show liquidity issues")

        return warnings

    def get_market_risk(self, symbol: str) -> Optional[Dict]:
        """
        获取指定市场的最新流动性风险
        
        Args:
            symbol: 市场符号
            
        Returns:
            最新指标或 None
        """
        history = self.metrics_history.get(symbol, [])
        if not history:
            return None
        latest = history[-1]
        return {
            "symbol": symbol,
            "liquidity_score": latest.liquidity_score,
            "spread": latest.bid_ask_spread,
            "depth": latest.depth,
            "timestamp": latest.timestamp
        }

    def reset(self):
        """重置分析器"""
        self.metrics_history.clear()
        self.warnings.clear()
        self.baseline_metrics.clear()
        logger.info("🔄 Liquidity Risk Analyzer reset")
