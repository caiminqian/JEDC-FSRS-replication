"""Analyst Agent - 分析员 Agent（基本面分析 + 投资评级）"""

import random
from typing import Dict, List, Optional
from datetime import datetime
from .base_trader import BaseTraderAgent, TradingSignal


class AnalystAgent(BaseTraderAgent):
    """
    分析员 Agent

    职责:
    1. 分析项目基本面（白皮书、团队、链上数据、社区活跃度）
    2. 生成投资评级（Strong Buy / Buy / Hold / Sell / Strong Sell）
    3. 发布研究报告
    4. 基于分析生成交易信号
    """
    
    def __init__(self, name: str, config: dict = None):
        default_config = {
            "analysis_interval": 10,
            "confidence_threshold": 0.60,
            "technical_weight": 0.30,
            "fundamental_weight": 0.40,
            "onchain_weight": 0.20,
            "sentiment_weight": 0.10,
        }
        if config:
            default_config.update(config)
        super().__init__(name=name, config=default_config)
        self.agent_type = "AnalystAgent"
        self.tick_counter = 0
        self.last_analysis = {}
        self.research_reports = []
        self.ratings = {}

    def perceive(self, world: "WorldStateGraph") -> Dict:
        perception = super().perceive(world)

        onchain_data = {}
        for symbol in perception["markets"]:
            onchain_data[symbol] = {
                "active_addresses": random.randint(1000, 100000),
                "exchange_netflow": random.uniform(-1000, 1000),
                "transactions_count": random.randint(5000, 50000),
            }

        sentiment_data = {}
        for symbol in perception["markets"]:
            sentiment_data[symbol] = {
                "twitter_sentiment": random.uniform(-1, 1),
                "github_commits_30d": random.randint(0, 200),
            }

        perception["onchain"] = onchain_data
        perception["sentiment"] = sentiment_data
        return perception

    def decide(self, perception: Dict) -> Dict:
        signals = []
        self.tick_counter += 1

        for symbol, market_data in perception["markets"].items():
            tech_score = self._analyze_technical(market_data)
            fundamental_score = self._analyze_fundamental(symbol, market_data)
            onchain_score = self._analyze_onchain(perception["onchain"].get(symbol, {}))
            sentiment_score = self._analyze_sentiment(perception["sentiment"].get(symbol, {}))

            weights = {
                "technical": self.config["technical_weight"],
                "fundamental": self.config["fundamental_weight"],
                "onchain": self.config["onchain_weight"],
                "sentiment": self.config["sentiment_weight"],
            }

            composite_score = (
                tech_score * weights["technical"] +
                fundamental_score * weights["fundamental"] +
                onchain_score * weights["onchain"] +
                sentiment_score * weights["sentiment"]
            )

            rating = self._score_to_rating(composite_score)
            self.ratings[symbol] = rating

            if abs(composite_score) > self.config["confidence_threshold"]:
                action = "BUY" if composite_score > 0 else "SELL"
                strength = abs(composite_score)
                signals.append({
                    "symbol": symbol,
                    "action": action,
                    "quantity": None,
                    "confidence": strength,
                    "rating": rating,
                    "reason": f"Rating: {rating} (score={composite_score:.2f})"
                })

                if self.tick_counter - self.last_analysis.get(symbol, 0) >= self.config["analysis_interval"]:
                    self._save_report(symbol, rating, composite_score, perception)
                    self.last_analysis[symbol] = self.tick_counter

        return {"signals": signals, "ratings": self.ratings, "strategy": "fundamental_analysis"}

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行交易"""
        results = []
        total_pnl = 0

        for signal in decision.get("signals", []):
            symbol = signal["symbol"]
            action = signal["action"]
            quantity = signal.get("quantity")

            price = self._get_market_price(symbol, world)
            if price <= 0:
                continue

            if quantity is None:
                quantity = (self.available_capital * 0.1) / price if action == "BUY" else \
                           self.position.get(symbol, {}).get("quantity", 0) * 0.2

            if action == "BUY":
                cost = quantity * price
                if self.available_capital >= cost:
                    self.buy(symbol, quantity, price, world, signal.get("reason", ""))
                    total_pnl -= cost
                    results.append({"symbol": symbol, "action": "BUY", "quantity": quantity, "price": price, "reason": signal.get("reason", ""), "rating": signal.get("rating", "")})
            elif action == "SELL":
                if symbol in self.position and self.position[symbol]["quantity"] > 0:
                    sell_qty = min(quantity, self.position[symbol]["quantity"])
                    revenue = sell_qty * price
                    self.sell(symbol, sell_qty, price, world, signal.get("reason", ""))
                    total_pnl += revenue
                    results.append({"symbol": symbol, "action": "SELL", "quantity": sell_qty, "price": price, "reason": signal.get("reason", ""), "rating": signal.get("rating", "")})

        return {"actions": results, "total_pnl": total_pnl, "ratings": self.ratings, "strategy": "fundamental_analysis"}

    # 辅助方法
    def _analyze_technical(self, market: Dict) -> float:
        change = market.get("change", 0)
        if change > 0.05: return -0.3
        elif change < -0.05: return 0.3
        elif change > 0.01: return 0.1
        elif change < -0.01: return -0.1
        else: return random.uniform(-0.2, 0.2)

    def _analyze_fundamental(self, symbol: str, market: Dict) -> float:
        volume = market.get("volume", 0)
        liquidity = market.get("liquidity", 0.5)
        score = (liquidity - 0.5) * 2 + min(1.0, volume / 1e7 - 0.5) * 0.5
        base_scores = {"BTC": 0.3, "ETH": 0.2, "XMR": -0.1, "FIL": -0.2, "STORJ": -0.2, "GLD": 0.1}
        score += base_scores.get(symbol, 0)
        return max(-1, min(1, score + random.uniform(-0.2, 0.2)))

    def _analyze_onchain(self, onchain: Dict) -> float:
        if not onchain:
            return 0
        netflow = onchain.get("exchange_netflow", 0)
        score = 0.4 if netflow < -500 else -0.3 if netflow > 500 else 0
        if onchain.get("active_addresses", 0) > 50000:
            score += 0.3
        return max(-1, min(1, score))

    def _analyze_sentiment(self, sentiment: Dict) -> float:
        if not sentiment:
            return 0
        twitter = sentiment.get("twitter_sentiment", 0)
        return max(-1, min(1, twitter))

    def _score_to_rating(self, score: float) -> str:
        if score >= 0.8: return "Strong Buy"
        elif score >= 0.4: return "Buy"
        elif score >= -0.4: return "Hold"
        elif score >= -0.8: return "Sell"
        else: return "Strong Sell"

    def _save_report(self, symbol: str, rating: str, score: float, perception: Dict):
        report = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "rating": rating,
            "score": round(score, 3),
            "price": perception["markets"][symbol]["price"],
        }
        self.research_reports.append(report)
        if len(self.research_reports) > 100:
            self.research_reports = self.research_reports[-100:]

    def get_info(self) -> Dict:
        info = super().get_info()
        info["agent_type"] = "AnalystAgent"
        info["ratings"] = self.ratings
        info["reports_count"] = len(self.research_reports)
        info["recent_reports"] = self.research_reports[-5:]
        return info
