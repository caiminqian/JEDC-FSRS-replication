"""Risk Agent - 风险管理 Agent（监控风险 + 自动对冲）"""

import random
from typing import Dict, List, Optional
from .base_trader import BaseTraderAgent, TradingSignal


class RiskAgent(BaseTraderAgent):
    """
    风险管理 Agent

    职责:
    1. 监控投资组合风险（集中度、波动率、VaR）
    2. 自动生成对冲交易（期权、期货、稳定币）
    3. 检测异常波动并发出预警

    策略:
    - 单一资产仓位不超过 20%
    - 整体波动率 > 30% 时启动对冲
    - 检测到黑天鹅事件（价格变化 > 15%）立即减仓 50%
    """
    
    def __init__(self, name: str, config: dict = None):
        default_config = {
            "max_single_asset_ratio": 0.15,    # 单一资产最大仓位 15%（更严格）
            "volatility_threshold": 0.10,       # 波动率阈值 10%（更敏感）
            "black_swan_threshold": 0.08,       # 黑天鹅阈值 8%（更敏感）
            "hedge_ratio": 0.30,                # 黑天鹅时对冲比例 30%
            "risk_free_asset": "USDC",
            "min_hedge_position": 0.02,
            "rebalance_threshold": 0.05,        # 再平衡阈值 5%
        }
        if config:
            default_config.update(config)
        super().__init__(name=name, config=default_config)
        self.agent_type = "RiskAgent"
        self.volatility_window = 10  # 计算波动率的窗口
        self.price_history = {}      # 价格历史 {symbol: [prices]}

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 收集市场数据 + 个人持仓 + 历史价格"""
        perception = super().perceive(world)

        # 更新价格历史
        for symbol, data in perception["markets"].items():
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(data["price"])
            if len(self.price_history[symbol]) > self.volatility_window:
                self.price_history[symbol].pop(0)

        # 计算波动率
        volatility = {}
        for symbol, prices in self.price_history.items():
            if len(prices) >= 2:
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                mean_return = sum(returns) / len(returns)
                variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                volatility[symbol] = (variance ** 0.5) * (252 ** 0.5)  # 年化波动率

        perception["volatility"] = volatility
        perception["price_history"] = self.price_history

        return perception

    def decide(self, perception: Dict) -> Dict:
        """决策 - 风险分析 + 对冲建议"""
        # 1. 计算当前组合风险
        positions = perception["positions"]  # {symbol: quantity}
        total_value = perception["capital"]
        # 计算持仓市值
        position_values = {}
        for symbol, qty in positions.items():
            if symbol in perception["markets"]:
                price = perception["markets"][symbol].get("price", 0)
                value = qty * price
                position_values[symbol] = value
                total_value += value

        # 单一资产集中度风险
        concentration_risk = {}
        for symbol, value in position_values.items():
            ratio = value / total_value if total_value > 0 else 0
            concentration_risk[symbol] = ratio

        max_concentration = max(concentration_risk.values(), default=0)
        risky_assets = {s: r for s, r in concentration_risk.items() if r > self.config["max_single_asset_ratio"]}

        # 2. 检测黑天鹅事件（价格剧烈变动）
        black_swan_signals = []
        for symbol, data in perception["markets"].items():
            change = abs(data.get("change", 0))
            if change > self.config["black_swan_threshold"]:
                black_swan_signals.append({
                    "symbol": symbol,
                    "change": change,
                    "action": "SELL" if data.get("change", 0) > 0 else "BUY"  # 暴涨则卖出，暴跌则抄底
                })

        # 3. 计算组合整体波动率（加权平均）
        portfolio_volatility = 0
        if total_value > 0:
            weighted_vols = []
            for symbol, ratio in concentration_risk.items():
                vol = perception["volatility"].get(symbol, 0)
                weighted_vols.append(ratio * vol)
            portfolio_volatility = sum(weighted_vols)

        need_hedge = portfolio_volatility > self.config["volatility_threshold"]

        # 4. 生成决策
        decisions = []

        # 黑天鹅事件处理
        for signal in black_swan_signals:
            if signal["action"] == "SELL":
                # 暴涨 → 卖出部分仓位 + 买入无风险资产
                if signal["symbol"] in positions:
                    qty = positions[signal["symbol"]]
                    sell_qty = abs(qty) * self.config["hedge_ratio"]
                    decisions.append({
                        "symbol": signal["symbol"],
                        "action": "SELL",
                        "quantity": sell_qty,
                        "reason": f"Black swan: {signal['change']*100:.1f}% spike"
                    })
                    # 买入无风险资产对冲
                    decisions.append({
                        "symbol": self.config["risk_free_asset"],
                        "action": "BUY",
                        "quantity": sell_qty * perception["markets"][signal["symbol"]]["price"],
                        "reason": "Hedge black swan event"
                    })

        # 集中度风险处理
        for symbol, ratio in risky_assets.items():
            if symbol in positions:
                excess_ratio = ratio - self.config["max_single_asset_ratio"]
                qty = positions[symbol]
                reduce_qty = abs(qty) * (excess_ratio / ratio)
                decisions.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "quantity": reduce_qty,
                    "reason": f"Concentration risk: {ratio*100:.1f}% > {self.config['max_single_asset_ratio']*100:.0f}%"
                })

        # 整体波动率对冲
        if need_hedge:
            # 计算需要多少无风险资产来降低波动率
            target_ratio = 0.30  # 目标：30% 配置无风险资产
            current_cash = perception["capital"]
            current_ratio = current_cash / total_value
            if current_ratio < target_ratio:
                # 卖出高风险资产，买入稳定币
                sell_targets = sorted(risky_assets.items(), key=lambda x: -x[1])[:3]
                for symbol, ratio in sell_targets:
                    if symbol in positions:
                        sell_qty = abs(positions[symbol]["quantity"]) * 0.1  # 卖出 10%
                        decisions.append({
                            "symbol": symbol,
                            "action": "SELL",
                            "quantity": sell_qty,
                            "reason": f"Portfolio volatility {portfolio_volatility*100:.0f}% > threshold"
                        })
                        decisions.append({
                            "symbol": self.config["risk_free_asset"],
                            "action": "BUY",
                            "quantity": sell_qty * perception["markets"][symbol]["price"],
                            "reason": "Reduce portfolio volatility"
                        })

        return {
            "signals": decisions,
            "risk_metrics": {
                "portfolio_volatility": portfolio_volatility,
                "max_concentration": max_concentration,
                "concentration_risk": concentration_risk,
                "black_swan_count": len(black_swan_signals),
                "need_hedge": need_hedge
            },
            "strategy": "risk_management"
        }

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行 - 执行对冲交易"""
        results = []
        total_pnl = 0

        for signal in decision.get("signals", []):
            symbol = signal["symbol"]
            action = signal["action"]
            quantity = signal["quantity"]
            reason = signal.get("reason", "")

            # 跳过无风险资产买入（现金即无风险资产）
            if symbol == self.config["risk_free_asset"] and action == "BUY":
                # 买入现金等价物：无需操作，资金已保留在 balance 中
                results.append({
                    "symbol": symbol,
                    "action": "BUY",
                    "quantity": quantity,
                    "price": 1.0,
                    "reason": reason
                })
                continue

            # 获取市场价格（风险资产）
            price = self._get_market_price(symbol, world)
            if price <= 0:
                continue

            if action == "BUY":
                cost = quantity * price
                if self.available_capital >= cost:
                    self.buy(symbol, quantity, price, world, reason)
                    total_pnl -= cost
                    results.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": price,
                        "reason": reason
                    })
            elif action == "SELL":
                if symbol in self.position and self.position[symbol] > 0:
                    sell_qty = min(quantity, self.position[symbol])
                    revenue = sell_qty * price
                    self.sell(symbol, sell_qty, price, world, reason)
                    total_pnl += revenue
                    results.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": sell_qty,
                        "price": price,
                        "reason": reason
                    })

        return {
            "actions": results,
            "total_pnl": total_pnl,
            "risk_metrics": decision.get("risk_metrics", {}),
            "strategy": "risk_management"
        }

    def get_info(self) -> Dict:
        info = super().get_info()
        info["agent_type"] = "RiskAgent"
        info["risk_metrics"] = {
            "volatility_history": self.price_history,
        }
        return info
