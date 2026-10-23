"""Institution Agent - 机构 Agent（理性、大额、低频）"""

import random
import logging
from typing import Dict, List
from .base_trader import BaseTraderAgent, TradingSignal

logger = logging.getLogger(__name__)


class InstitutionAgent(BaseTraderAgent):
    """
    机构 Agent - 理性交易

    行为特征:
    - 大额交易（影响市场）
    - 低频（基本面驱动）
    - 分散投资
    - 严格止损
    - 信息优势（更早获取市场信息）
    """

    def __init__(self, name: str = None, config: Dict = None, rng: random.Random = None, **kwargs):
        super().__init__(name=name, config=config or {}, **kwargs)
        # RNG for reproducible randomness
        import random
        self.rng = rng or random
        self.balance = self.config.get("initial_balance", 1_000_000)
        self.available_capital = self.balance
        self.strategy = self.config.get("strategy", "value_investing")
        self.max_position_size = self.config.get("max_position_size", 0.1)
        self.stop_loss_pct = self.config.get("stop_loss", 0.05)
        self.take_profit_pct = self.config.get("take_profit", 0.20)
        self.min_confidence = self.config.get("min_confidence", 0.7)
        self.research_depth = self.config.get("research_depth", 10)
        self.analysis_cache = {}
        self.trade_cooldown = {}

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 深度市场分析"""
        perception = super().perceive(world)

        # 复用 BaseTraderAgent 已提取的 markets 作为 market_data
        perception["market_data"] = perception["markets"]

        # 基本面分析（模拟）
        perception["fundamentals"] = self._analyze_fundamentals(perception["market_data"])

        # 市场情绪
        perception["sentiment"] = self._measure_sentiment()

        return perception

    def decide(self, perception: Dict) -> Dict:
        """决策 - 基本面 + 技术面 + 风险管理"""
        signals = []
        fundamentals = perception.get("fundamentals", {})
        sentiment = perception.get("sentiment", 0)

        for symbol, analysis in fundamentals.items():
            if not analysis.get("buyable", False):
                continue

            confidence = analysis.get("confidence", 0)
            fair_value = analysis.get("fair_value", 0)
            current_price = perception["market_data"][symbol]["price"]

            # 安全边际：价格低于估值 20% 才买入
            margin = (fair_value - current_price) / fair_value

            if confidence >= self.min_confidence and margin >= 0.2:
                # 计算仓位（凯利公式简化）
                position_pct = min(
                    self.max_position_size,
                    margin * confidence * (1 - sentiment)  # 市场恐慌时加大仓位
                )

                size = (self.balance * position_pct) / current_price

                signals.append({
                    "symbol": symbol,
                    "direction": "buy",
                    "size": round(size, 4),
                    "price": current_price,
                    "stop_loss": round(current_price * (1 - self.stop_loss_pct), 2),
                    "take_profit": round(current_price * (1 + self.take_profit_pct), 2),
                    "confidence": confidence,
                    "reason": f"Value buy: margin={margin*100:.1f}%, confidence={confidence:.2f}"
                })

        # 止损/止盈卖出
        for symbol, pos in self.position.items():
            current_price = perception["market_data"].get(symbol, {}).get("price", 0)
            if current_price == 0:
                continue

            # 检查止损
            avg_cost = self.config.get("cost_basis", {}).get(symbol, current_price)
            pnl_pct = (current_price - avg_cost) / avg_cost

            if pnl_pct <= -self.stop_loss_pct:
                signals.append({
                    "symbol": symbol,
                    "direction": "sell",
                    "size": pos,
                    "reason": f"Stop loss triggered ({pnl_pct*100:.1f}%)"
                })
            elif pnl_pct >= self.take_profit_pct:
                signals.append({
                    "symbol": symbol,
                    "direction": "sell",
                    "size": pos,
                    "reason": f"Take profit ({pnl_pct*100:.1f}%)"
                })

        return {"signals": signals, "strategy": self.strategy}

    def _analyze_fundamentals(self, market_data: Dict) -> Dict[str, Dict]:
        """基本面分析（模拟）"""
        analysis = {}
        for symbol, data in market_data.items():
            # 模拟基本面评分（实际应接入财报、链上数据等）
            price = data["price"]
            volume = data["volume"]

            # 随机生成"基本面"（演示用）
            fair_value = price * self.rng.uniform(1.2, 1.5)  # 估值溢价 20-50%
            confidence = self.rng.uniform(0.6, 0.95)

            analysis[symbol] = {
                "fair_value": fair_value,
                "confidence": confidence,
                "buyable": price < fair_value and confidence > 0.7,
                "metrics": {
                    "volume_score": min(1.0, volume / 1e9),
                    "liquidity_score": data.get("liquidity", 1.0)
                }
            }

        return analysis

    def _measure_sentiment(self) -> float:
        """测量市场情绪（-1 到 1）"""
        return self.rng.uniform(-0.5, 0.5)  # 模拟

    def learn(self, experience: Dict):
        """学习 - 更新基本面分析模型"""
        super().learn(experience)
        # TODO: 调整估值模型参数

    def get_info(self) -> Dict:
        info = super().get_info()
        info.update({
            "strategy": self.strategy,
            "balance": self.balance,
            "available_capital": self.available_capital,
            "positions_count": len(self.position),
            "max_position_size": self.max_position_size
        })
        return info