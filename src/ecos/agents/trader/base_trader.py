"""Base Trader Agent - 交易智能体基类"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from ..base_agent import BaseAgent, AgentMemory

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """交易信号"""
    symbol: str
    direction: str  # "buy" / "sell"
    size: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.5  # 0-1
    reason: str = ""
    timestamp: str = ""


class BaseTraderAgent(BaseAgent):
    """交易智能体基类（扩展 BaseAgent）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trade_history: List[Dict] = []
        self.position_history: List[Dict] = []
        self.available_capital: float = self.balance

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """
        感知世界 - 提取市场数据 + 个人持仓

        子类可重写以添加自定义逻辑
        """
        perception = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.get_info(),
            "markets": world.get_market_data(),  # 使用缓存的市场数据
            "positions": self.position,  # 直接引用，避免拷贝
            "capital": self.available_capital
        }
        return perception

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """
        执行交易行动

        Args:
            decision: 包含 signals 列表的决策
            world: 世界状态图（可修改）

        Returns:
            执行结果（success, pnl, etc.）
        """
        results = []

        signals = decision.get("signals", [])
        for sig in signals:
            # 验证信号
            if not isinstance(sig, dict):
                continue

            symbol = sig.get("symbol")
            direction = sig.get("direction")
            size = sig.get("size", 0)

            # 检查资金
            cost = sig.get("price", 0) * size
            if direction == "buy" and cost > self.available_capital:
                logger.warning(f"Insufficient capital for {symbol}: need {cost}, have {self.available_capital}")
                continue

            # 执行交易（修改世界状态 + 更新自身状态）
            trade_result = self._execute_trade(sig, world)
            results.append(trade_result)

            # 记录
            self.trade_history.append(trade_result)
            # 限制历史长度以避免内存泄漏
            if len(self.trade_history) > 1000:
                self.trade_history.pop(0)
            self.stats["actions"] += 1

        # 计算总 PnL
        total_pnl = sum(r.get("pnl", 0) for r in results)
        self.stats["rewards"] += total_pnl

        return {
            "trades": results,
            "total_pnl": total_pnl,
            "balance_after": self.balance
        }

    def _execute_trade(self, signal: Dict, world: "WorldStateGraph") -> Dict:
        """执行单笔交易"""
        symbol = signal["symbol"]
        direction = signal["direction"]
        size = signal["size"]
        price = signal.get("price") or self._get_market_price(symbol, world)

        # 更新持仓
        if direction == "buy":
            cost = price * size
            if cost > self.available_capital:
                return {"symbol": symbol, "status": "failed", "reason": "insufficient_capital"}

            self.balance -= cost
            self.position[symbol] = self.position.get(symbol, 0) + size
            self.available_capital -= cost

            # 在世界图中添加资金流边
            world.add_edge(
                from_id=self.agent_id,
                to_id=f"market:{symbol}",
                edge_type="capital_flow",
                amount=cost,
                direction="buy",
                timestamp=datetime.now().isoformat()
            )

        elif direction == "sell":
            held = self.position.get(symbol, 0)
            if held < size:
                return {"symbol": symbol, "status": "failed", "reason": "insufficient_position"}

            proceeds = price * size
            self.balance += proceeds
            self.position[symbol] -= size
            if self.position[symbol] <= 0:
                del self.position[symbol]
            self.available_capital += proceeds

            # 计算 PnL（简化：假设持仓成本 = 上次买入价）
            pnl = self._calculate_pnl(symbol, size, price)
            self.stats["rewards"] += pnl

            world.add_edge(
                from_id=f"market:{symbol}",
                to_id=self.agent_id,
                edge_type="capital_flow",
                amount=proceeds,
                direction="sell",
                timestamp=datetime.now().isoformat()
            )

        return {
            "symbol": symbol,
            "direction": direction,
            "size": size,
            "price": price,
            "status": "success",
            "pnl": 0 if direction == "buy" else pnl,
            "timestamp": datetime.now().isoformat()
        }

    def _get_market_price(self, symbol: str, world: "WorldStateGraph") -> float:
        """获取市场价格（从世界图）"""
        for node_id, data in world.graph.nodes(data=True):
            if data.get("type") == "market" and data.get("symbol") == symbol:
                return data.get("price", 0.0)
        return 0.0

    def _calculate_pnl(self, symbol: str, size: float, sell_price: float) -> float:
        """计算盈亏（简化）"""
        # TODO: 跟踪持仓成本
        return 0.0

    def get_trade_history(self, last_n: int = 100) -> List[Dict]:
        """获取最近交易历史"""
        return self.trade_history[-last_n:]

    def get_position_value(self, world: "WorldStateGraph") -> float:
        """计算持仓市值"""
        total = 0.0
        for symbol, pos in self.position.items():
            price = self._get_market_price(symbol, world)
            size = pos["size"] if isinstance(pos, dict) else pos
            total += price * size
        return total

    def get_total_value(self, world: "WorldStateGraph") -> float:
        """总资产 = 现金 + 持仓市值"""
        return self.balance + self.get_position_value(world)

    def buy(self, symbol: str, quantity: float, price: float, world: "WorldStateGraph", reason: str = "") -> Dict:
        """买入资产"""
        signal = {
            "symbol": symbol,
            "direction": "buy",
            "size": quantity,
            "price": price,
            "reason": reason
        }
        result = self._execute_trade(signal, world)
        return result

    def sell(self, symbol: str, quantity: float, price: float, world: "WorldStateGraph", reason: str = "") -> Dict:
        """卖出资产"""
        signal = {
            "symbol": symbol,
            "direction": "sell",
            "size": quantity,
            "price": price,
            "reason": reason
        }
        result = self._execute_trade(signal, world)
        return result
