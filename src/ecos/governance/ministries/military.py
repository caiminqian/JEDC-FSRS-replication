"""兵部 (Military Ministry) - 市场干预与稳定
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random


@dataclass
class StabilizationOperation:
    """市场干预操作记录"""
    op_id: str
    tick: int
    target_market: str
    action: str          # "inject_liquidity", "buy_support", "sell_restrain"
    amount: float
    result: Optional[Dict] = None


class MilitaryMinistry:
    """
    兵部 - 平准司
    
    职责:
    1. 维护市场稳定（打击操纵、防止崩盘）
    2. 执行平准基金操作（低买高卖）
    3. 危机时刻救市
    4. 监测异常交易
    
    权力:
    - 可以临时暂停交易
    - 可以动用国库进行市场操作
    - 可以冻结 Agent 资产
    """
    
    def __init__(self, world):
        self.world = world
        self.stabilization_fund = 1e6  # 平准基金初始 100 万
        self.operations: List[StabilizationOperation] = []
        self.surveillance_targets = []  # 监控名单
        
    def stabilize_market(self, violation_reports: Optional[Dict] = None) -> Optional[StabilizationOperation]:
        """
        市场稳定操作（每 tick 调用）
        
        Args:
            violation_reports: 违规报告 {symbol: count}
            
        Returns:
            执行的操作，或 None
        """
        # 检查是否需要干预
        needs_intervention = False
        target_market = None
        
        if violation_reports:
            # 基于违规次数最多的市场
            most_violated = max(violation_reports, key=violation_reports.get)
            if violation_reports[most_violated] > 10:
                needs_intervention = True
                target_market = most_violated
        
        # 检查价格 spike
        for node_id, data in self.world.graph.nodes(data=True):
            if data.get("type") != "market":
                continue
            symbol = data.get("symbol")
            change = abs(data.get("change", 0))
            if change > 0.15:  # 单 tick 波动 > 15%
                needs_intervention = True
                target_market = symbol
                break
        
        if not needs_intervention:
            return None
        
        # 执行干预：注入流动性 + 买入支撑
        op = StabilizationOperation(
            op_id=f"OP_{len(self.operations):04d}",
            tick=0,  # TODO: get current tick
            target_market=target_market or "unknown",
            action="liquidity_injection",
            amount=5e5  # 每次干预 50 万
        )
        
        # 执行买入操作（使用平准基金）
        if self.stabilization_fund >= op.amount:
            self.stabilization_fund -= op.amount
            # TODO: 实际买入逻辑（需要市场节点）
            # self._execute_buy(target_market, op.amount)
            op.result = {"status": "success", "funds_used": op.amount}
            self.operations.append(op)
            print(f"  [兵部] 市场干预: {target_market} 投入 {op.amount:,.0f}")
        else:
            op.result = {"status": "failed", "reason": "insufficient_funds"}
        
        return op
    
    def inject_liquidity(self, amount: float, target_markets: List[str] = None) -> bool:
        """
        注入流动性
        
        Args:
            amount: 注入金额
            target_markets: 目标市场列表（None 表示全部）
        """
        if self.stabilization_fund < amount:
            return False
        
        self.stabilization_fund -= amount
        
        # 更新市场流动性属性
        markets = target_markets or [d.get("symbol") for n, d in self.world.graph.nodes(data=True) if d.get("type")=="market"]
        for market in markets:
            node_id = f"market:{market}"
            if self.world.graph.has_node(node_id):
                current = self.world.graph.nodes[node_id].get("liquidity", 1.0)
                self.world.update_node(node_id, {"liquidity": min(2.0, current + 0.2)})
        
        return True
    
    def monitor_for_manipulation(self) -> List[Dict]:
        """监控市场操纵行为"""
        suspicious = []
        
        # 检测异常交易量（比平均高 5 倍）
        for node_id, data in self.world.graph.nodes(data=True):
            if data.get("type") != "market":
                continue
            symbol = data.get("symbol")
            volume = data.get("volume", 0)
            
            # TODO: 计算历史平均
            if volume > 1e8:  #  Arbitrary threshold
                suspicious.append({
                    "symbol": symbol,
                    "type": "unusual_volume",
                    "volume": volume
                })
        
        return suspicious
    
    def get_fund_status(self) -> Dict:
        """平准基金状态"""
        return {
            "current_balance": self.stabilization_fund,
            "total_interventions": len(self.operations),
            "recent_operations": self.operations[-5:]
        }

    def get_performance_metrics(self) -> Dict:
        """兵部绩效指标（市场稳定效果）"""
        if not self.operations:
            return {"interventions": 0, "avg_impact": 0, "success_rate": 0}
        
        successful = sum(1 for op in self.operations if op.result and op.result.get("stabilized", False))
        impacts = [op.result.get("price_change", 0) for op in self.operations if op.result]
        avg_impact = sum(impacts) / len(impacts) if impacts else 0
        
        return {
            "interventions": len(self.operations),
            "success_rate": successful / len(self.operations),
            "avg_price_impact_pct": avg_impact,
            "fund_remaining": self.stabilization_fund
        }


__all__ = ["MilitaryMinistry", "StabilizationOperation"]
