"""Market Maker Agent - 做市商 Agent（提供流动性）"""

import random
from datetime import datetime
from typing import Dict, List, Optional
from .base_trader import BaseTraderAgent, TradingSignal


class MarketMakerAgent(BaseTraderAgent):
    """
    做市商 Agent - 持续挂单提供流动性

    行为特征:
    - 同时挂买单和卖单
    - 薄利快进快出
    - 高频（在 tick 级别）
    - 低风险偏好
    - 依赖价差盈利
    """

    def __init__(self, name: str = None, config: Dict = None, rng: random.Random = None, **kwargs):
        super().__init__(name=name, config=config or {}, **kwargs)
        # RNG for reproducible randomness
        import random
        self.rng = rng or random
        self.spread = self.config.get("spread", 0.002)  # 价差 0.2%
        self.order_size = self.config.get("order_size", 1000)  # 每单数量
        self.max_orders = self.config.get("max_orders", 20)  # 最大挂单数
        self.cancel_probability = self.config.get("cancel_prob", 0.3)  # 撤单概率
        self.active_orders: Dict[str, Dict] = {}  # order_id -> order

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 关注市场价格和订单簿"""
        perception = super().perceive(world)

        # 从 market_data 构建 order_book
        perception["order_book"] = {}
        for symbol, data in perception["markets"].items():
            perception["order_book"][symbol] = {
                "bid": data.get("bid", data["price"] * 0.999),
                "ask": data.get("ask", data["price"] * 1.001),
                "bid_size": data.get("bid_size", 1000),
                "ask_size": data.get("ask_size", 1000)
            }

        return perception

    def decide(self, perception: Dict) -> Dict:
        """决策 - 生成挂单"""
        signals = []
        markets = perception["markets"]
        order_book = perception.get("order_book", {})

        for symbol, data in markets.items():
            price = data["price"]
            if price <= 0:
                continue

            # 计算挂单价
            bid_price = round(price * (1 - self.spread / 2), 2)
            ask_price = round(price * (1 + self.spread / 2), 2)

            # 检查是否有冲突订单（已挂单）
            existing_bids = [o for o in self.active_orders.values()
                           if o.get("symbol") == symbol and o.get("direction") == "buy"]
            existing_asks = [o for o in self.active_orders.values()
                           if o.get("symbol") == symbol and o.get("direction") == "sell"]

            # 买单（仅当没有更低买单时）
            if not existing_bids and len(self.active_orders) < self.max_orders:
                buy_size = min(self.order_size, self.available_capital / bid_price)
                if buy_size > 0:
                    signals.append({
                        "symbol": symbol,
                        "direction": "buy",
                        "size": round(buy_size, 4),
                        "price": bid_price,
                        "order_type": "limit",
                        "reason": "MM bid"
                    })

            # 卖单（仅当没有更高卖单时）
            if not existing_asks and len(self.active_orders) < self.max_orders:
                held = self.position.get(symbol, 0)
                sell_size = min(self.order_size, held)
                if sell_size > 0:
                    signals.append({
                        "symbol": symbol,
                        "direction": "sell",
                        "size": round(sell_size, 4),
                        "price": ask_price,
                        "order_type": "limit",
                        "reason": "MM ask"
                    })

        # 随机撤单（模拟）
        if self.rng.random() < self.cancel_probability and self.active_orders:
            order_to_cancel = self.rng.choice(list(self.active_orders.keys()))
            signals.append({
                "action": "cancel",
                "order_id": order_to_cancel,
                "reason": "random cancel"
            })

        return {"signals": signals, "strategy": "market_maker"}

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行 - 处理挂单和撤单"""
        results = []
        signals = decision.get("signals", [])

        for sig in signals:
            if sig.get("action") == "cancel":
                order_id = sig["order_id"]
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
                    results.append({"status": "cancelled", "order_id": order_id})
                continue

            # 执行普通交易
            result = self._execute_trade(sig, world)
            if result.get("status") == "success":
                # 记录挂单
                order_id = f"order_{len(self.active_orders)}"
                self.active_orders[order_id] = {
                    "symbol": sig["symbol"],
                    "direction": sig["direction"],
                    "size": sig["size"],
                    "price": sig.get("price"),
                    "order_type": sig.get("order_type", "market"),
                    "timestamp": datetime.now().isoformat()
                }
                result["order_id"] = order_id

            results.append(result)
            self.stats["actions"] += 1

        return {"trades": results, "active_orders": len(self.active_orders)}

    def get_info(self) -> Dict:
        info = super().get_info()
        info.update({
            "strategy": "market_maker",
            "spread": self.spread,
            "active_orders": len(self.active_orders),
            "order_size": self.order_size
        })
        return info