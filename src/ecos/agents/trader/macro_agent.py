"""Macro Agent - 宏观分析 Agent（趋势跟踪 + 周期判断）"""

import random
from typing import Dict, List, Optional
from datetime import datetime
from .base_trader import BaseTraderAgent, TradingSignal


class MacroAgent(BaseTraderAgent):
    """
    宏观分析 Agent

    职责:
    1. 跟踪宏观经济指标（通胀、利率、GDP、失业率）
    2. 判断经济周期（复苏/过热/滞胀/衰退）
    3. 根据周期调整资产配置
    4. 跟踪央行政策新闻

    策略:
    - 复苏期: 增持股票/加密货币
    - 过热期: 增持大宗商品
    - 滞胀期: 增持黄金 + 现金
    - 衰退期: 做空风险资产
    """
    
    def __init__(self, name: str, config: dict = None):
        default_config = {
            "economic_cycle": "expansion",          # 当前经济周期
            "inflation_rate": 0.03,                 # 通胀率 3%
            "interest_rate": 0.05,                  # 利率 5%
            "gdp_growth": 0.025,                    # GDP 增长 2.5%
            "unemployment_rate": 0.04,              # 失业率 4%
            "cycle_update_interval": 20,            # 周期判断间隔（ticks）
            "risk_appetite": 0.7,                   # 风险偏好 (0-1)
            "max_leverage": 2.0,                    # 最大杠杆
        }
        if config:
            default_config.update(config)
        super().__init__(name=name, config=default_config)
        self.agent_type = "MacroAgent"
        self.tick_counter = 0
        self.last_cycle_update = 0
        self.economic_indicators = {}
        self.news_flow = []  # 新闻流

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 收集市场数据 + 宏观经济指标"""
        perception = super().perceive(world)

        # 模拟宏观经济指标更新（每 20 ticks 更新一次）
        self.tick_counter += 1
        if self.tick_counter - self.last_cycle_update >= self.config["cycle_update_interval"]:
            self._update_economic_indicators()
            self.last_cycle_update = self.tick_counter

        perception["economic_indicators"] = self.economic_indicators
        perception["current_cycle"] = self.config["economic_cycle"]
        perception["news_flow"] = self.news_flow[-5:]  # 最近 5 条新闻

        return perception

    def _update_economic_indicators(self):
        """模拟宏观经济指标随机游走"""
        # 通胀率：正态分布，均值 3%，标准差 1%
        self.economic_indicators["inflation"] = max(0, min(0.10,
            self.economic_indicators.get("inflation", self.config["inflation_rate"])
            + random.uniform(-0.01, 0.01)
        ))

        # 利率：跟随通胀调整（带滞后）
        inflation = self.economic_indicators["inflation"]
        target_rate = max(0.01, min(0.15, inflation * 1.5))
        current_rate = self.economic_indicators.get("interest_rate", self.config["interest_rate"])
        self.economic_indicators["interest_rate"] = current_rate + (target_rate - current_rate) * 0.3

        # GDP 增长：均值 2.5%，标准差 2%
        self.economic_indicators["gdp_growth"] = max(-0.05, min(0.08,
            self.economic_indicators.get("gdp_growth", self.config["gdp_growth"])
            + random.uniform(-0.015, 0.015)
        ))

        # 失业率：与 GDP 负相关
        self.economic_indicators["unemployment"] = max(0.02, min(0.10,
            0.06 - self.economic_indicators["gdp_growth"] * 0.5
        ))

        # 判断经济周期
        self._determine_cycle()

        # 生成新闻
        self._generate_news()

    def _determine_cycle(self):
        """判断经济周期（四象限法）"""
        gdp = self.economic_indicators["gdp_growth"]
        inflation = self.economic_indicators["inflation"]

        if gdp > 0.02 and inflation < 0.04:
            cycle = "复苏"
        elif gdp > 0.02 and inflation >= 0.04:
            cycle = "过热"
        elif gdp <= 0.02 and inflation >= 0.04:
            cycle = "滞胀"
        else:  # gdp <= 0.02 and inflation < 0.04
            cycle = "衰退"

        old_cycle = self.config["economic_cycle"]
        self.config["economic_cycle"] = cycle

        if old_cycle != cycle:
            self.news_flow.append({
                "timestamp": datetime.now().isoformat(),
                "headline": f"Economic cycle shift: {old_cycle} → {cycle}",
                "type": "macro"
            })

    def _generate_news(self):
        """生成模拟新闻"""
        events = [
            ("Fed rate decision pending", "policy", random.choice([-1, 1])),
            ("Inflation data above expectations", "inflation", random.choice([-1, 1])),
            ("GDP growth beats forecasts", "growth", 1),
            ("Unemployment rises unexpectedly", "labor", -1),
            ("Geopolitical tensions escalate", "risk", -1),
            ("Tech sector rally continues", "sector", 1),
        ]

        if random.random() < 0.3:  # 30% 概率有新闻
            headline, category, sentiment = random.choice(events)
            self.news_flow.append({
                "timestamp": datetime.now().isoformat(),
                "headline": headline,
                "category": category,
                "sentiment": sentiment,
                "type": "news"
            })

    def decide(self, perception: Dict) -> Dict:
        """决策 - 根据经济周期调整仓位"""
        cycle = self.config["economic_cycle"]
        markets = perception["markets"]
        positions = perception["positions"]
        capital = perception["capital"]
        total_value = capital + sum(pos.get("value", 0) for pos in positions.values())

        signals = []

        # 周期配置表
        cycle_allocation = {
            "复苏": {
                "risk_assets": ["BTC", "ETH", "SOL", "AVAX", "LINK"],
                "safe_assets": ["USDC", "USDT"],
                "leverage": 1.5,
                "action": "BULLISH"
            },
            "过热": {
                "risk_assets": ["GLD", "OIL", "COPPER"],  # commodities
                "safe_assets": ["USDC"],
                "leverage": 1.0,
                "action": "NEUTRAL"
            },
            "滞胀": {
                "risk_assets": ["GLD", "BTC"],  # 黄金 + 比特币（抗通胀）
                "safe_assets": ["USDC", "CASH"],
                "leverage": 0.5,
                "action": "DEFENSIVE"
            },
            "衰退": {
                "risk_assets": [],
                "safe_assets": ["USDC", "GLD"],
                "leverage": 0.0,
                "action": "BEARISH"
            }
        }

        # 获取当前周期配置
        alloc = cycle_allocation.get(cycle, cycle_allocation["复苏"])

        # 1. 计算目标仓位
        risk_target = 0.7 * self.config["risk_appetite"] * alloc["leverage"]
        safe_target = 1.0 - risk_target

        # 2. 计算当前风险仓位占比
        risk_value = 0
        for symbol, pos in positions.items():
            if symbol in ["BTC", "ETH", "SOL", "AVAX", "LINK", "GLD", "OIL", "COPPER"]:
                risk_value += pos.get("value", 0)

        current_risk_ratio = risk_value / total_value if total_value > 0 else 0

        # 3. 调整仓位
        if current_risk_ratio < risk_target:
            # 需要增加风险仓位
            buy_amount = (risk_target - current_risk_ratio) * total_value
            # 按配置比例买入
            risk_assets = alloc["risk_assets"]
            if risk_assets:
                per_asset = buy_amount / len(risk_assets)
                for symbol in risk_assets:
                    if symbol in markets:
                        qty = per_asset / markets[symbol]["price"]
                        signals.append({
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": qty,
                            "reason": f"Cycle: {cycle}, target risk allocation {risk_target*100:.0f}%"
                        })

        if current_risk_ratio > risk_target:
            # 需要减少风险仓位
            sell_amount = (current_risk_ratio - risk_target) * total_value
            # 按比例卖出风险资产
            risk_positions = {s: p for s, p in positions.items()
                              if s in ["BTC", "ETH", "SOL", "AVAX", "LINK", "GLD", "OIL", "COPPER"]}
            total_risk_value = sum(p.get("value", 0) for p in risk_positions.values())
            if total_risk_value > 0:
                for symbol, pos in risk_positions.items():
                    ratio = pos.get("value", 0) / total_risk_value
                    sell_qty = (sell_amount * ratio) / markets.get(symbol, {}).get("price", 1)
                    signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": min(sell_qty, pos["quantity"]),
                        "reason": f"Reduce risk exposure from {current_risk_ratio*100:.0f}% to {risk_target*100:.0f}%"
                    })

        # 4. 新闻事件驱动交易
        for news in perception.get("news_flow", []):
            sentiment = news.get("sentiment", 0)
            if sentiment > 0 and cycle == "衰退":
                # 衰退中有利好新闻 → 抄底
                for symbol in ["BTC", "ETH"]:
                    if symbol in markets and capital > 1000:
                        signals.append({
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": capital * 0.1 / markets[symbol]["price"],
                            "reason": f"News-driven: {news['headline'][:40]}"
                        })
                        break
                break

        return {
            "signals": signals,
            "economic_indicators": self.economic_indicators,
            "current_cycle": cycle,
            "cycle_allocation": alloc,
            "strategy": "macro_trend_following"
        }

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行 - 执行宏观交易"""
        results = []
        total_pnl = 0

        for signal in decision.get("signals", []):
            symbol = signal["symbol"]
            action = signal["action"]
            quantity = signal["quantity"]

            price = self._get_market_price(symbol, world)
            if price <= 0:
                continue

            if action == "BUY":
                cost = quantity * price
                if self.available_capital >= cost:
                    self.buy(symbol, quantity, price, world, signal.get("reason", ""))
                    total_pnl -= cost
                    results.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": price,
                        "reason": signal.get("reason", "")
                    })
            elif action == "SELL":
                if symbol in self.position and self.position[symbol]["quantity"] > 0:
                    sell_qty = min(quantity, self.position[symbol]["quantity"])
                    revenue = sell_qty * price
                    self.sell(symbol, sell_qty, price, world, signal.get("reason", ""))
                    total_pnl += revenue
                    results.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": sell_qty,
                        "price": price,
                        "reason": signal.get("reason", "")
                    })

        return {
            "actions": results,
            "total_pnl": total_pnl,
            "economic_cycle": self.config["economic_cycle"],
            "strategy": "macro_trend_following"
        }

    def get_info(self) -> Dict:
        info = super().get_info()
        info["agent_type"] = "MacroAgent"
        info["economic_indicators"] = self.economic_indicators
        info["current_cycle"] = self.config["economic_cycle"]
        info["news_count"] = len(self.news_flow)
        return info
