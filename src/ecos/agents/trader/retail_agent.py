"""Retail Agent - 散户 Agent（简单跟随策略）"""

import random
from typing import Dict, List, Optional
from .base_trader import BaseTraderAgent, TradingSignal


class RetailAgent(BaseTraderAgent):
    """
    散户 Agent - 模仿简单策略

    行为特征:
    - FOMO (Fear Of Missing Out) - 追涨
    - 恐慌抛售 - 杀跌
    - 仓位分散 - 持有多个币种
    - 反应滞后 - 看到价格上涨后才买入
    """

    def __init__(self, name: str = None, config: Dict = None, rng: 'random.Random' = None, **kwargs):
        super().__init__(name=name, config=config or {}, **kwargs)
        # RNG for reproducible randomness
        import random
        self.rng = rng or random
        self.fomo_factor = self.config.get("fomo_factor", 0.8)
        self.panic_factor = self.config.get("panic_factor", 0.5)
        self.max_positions = self.config.get("max_positions", 5)
        self.position_size_pct = self.config.get("position_size_pct", 0.2)

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 关注价格变化和自身盈亏"""
        perception = super().perceive(world)

        # 计算每个持仓的盈亏
        perception["pnl"] = {}
        for symbol, size in self.position.items():
            current_price = perception["markets"].get(symbol, {}).get("price", 0)
            # TODO: 记录持仓成本
            avg_cost = self.config.get("cost_basis", {}).get(symbol, current_price)
            pnl = (current_price - avg_cost) * size
            perception["pnl"][symbol] = pnl

        # 检测市场趋势（简单：过去 N 个 tick 的平均涨跌幅）
        perception["market_trend"] = self._detect_trend(perception["markets"])

        return perception

    def decide(self, perception: Dict) -> Dict:
        """决策 - FOMO + 恐慌逻辑"""
        signals = []

        markets = perception["markets"]
        trend = perception.get("market_trend", {})

        # 1. 追涨逻辑（看到上涨 → 买入）
        for symbol, data in markets.items():
            change = data.get("change", 0)
            price = data.get("price", 0)

            # 使用配置阈值
            buy_threshold = self.config.get("buy_threshold", 0.001)  # 默认 0.1%
            if change > buy_threshold:
                # FOMO: 上涨越多，买入意愿越强
                buy_probability = min(0.8, self.fomo_factor * change * 1000)  # *1000 放大
                if self.rng.random() < buy_probability:
                    current_pos = self.position.get(symbol, 0)
                    if current_pos == 0 and len(self.position) < self.max_positions:
                        size = (self.balance * self.position_size_pct) / price
                        signals.append({
                            "symbol": symbol,
                            "direction": "buy",
                            "size": round(size, 4),
                            "price": price,
                            "reason": f"FOMO on +{change*100:.1f}%"
                        })

        # 2. 恐慌抛售逻辑（持仓亏损 >5% → 卖出）
        for symbol, pnl in perception.get("pnl", {}).items():
            panic_threshold = self.config.get("panic_threshold", -0.05)  # 默认 -5%
            if pnl < panic_threshold:
                sell_probability = min(0.9, self.panic_factor * abs(pnl))
                if self.rng.random() < sell_probability:
                    size = self.position.get(symbol, 0) * 0.5  # 卖出一半
                    if size > 0:
                        signals.append({
                            "symbol": symbol,
                            "direction": "sell",
                            "size": round(size, 4),
                            "reason": "panic sell"
                        })

        # 3. 随机交易（模拟散户不确定性）
        random_noise = self.config.get("random_noise", 0.2)  # 默认 20%
        if self.rng.random() < random_noise:
            if markets and self.balance > 100:
                symbol = self.rng.choice(list(markets.keys()))
                price = markets[symbol]["price"]
                if price > 0:
                    signals.append({
                        "symbol": symbol,
                        "direction": self.rng.choice(["buy", "sell"]),
                        "size": round(self.balance * 0.05 / price, 4),
                        "reason": "random noise"
                    })

        return {"signals": signals, "strategy": "retail_fomo"}

    def _detect_trend(self, markets: Dict) -> Dict[str, float]:
        """检测市场趋势（简化）"""
        # TODO: 基于历史数据计算真实趋势
        # 当前仅返回随机趋势（演示用）
        return {sym: self.rng.uniform(-1, 1) for sym in markets}

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行交易"""
        result = super().act(decision, world)
        self.stats["decisions"] += 1
        return result

    def learn(self, experience: Dict):
        """学习 - 散户学习能力较弱（仅记录，不调整策略）"""
        super().learn(experience)
        # TODO: 可添加简单记忆（如某币种总是不赚钱 → 避免交易）

    def get_info(self) -> Dict:
        info = super().get_info()
        info.update({
            "strategy": "retail_fomo",
            "fomo_factor": self.fomo_factor,
            "panic_factor": self.panic_factor
        })
        return info