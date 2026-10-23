"""Regulator Agent - 监管机构 Agent（监控异常 + 执行规则）"""

import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from .base_trader import BaseTraderAgent, TradingSignal


class RegulatorAgent(BaseTraderAgent):
    """
    监管机构 Agent

    职责:
    1. 监控市场异常波动（拉盘、砸盘、洗盘）
    2. 检测潜在市场操纵（对敲、虚假交易、幌骗）
    3. 执行熔断机制（暂停交易）
    4. 审查大额交易合规性
    5. 发布监管警示

    监管规则:
    - 单笔交易 > 市场平均成交量 10% → 审查
    - 5 分钟内价格变动 > 20% → 临时熔断
    - 检测到对敲（同一对手方反复交易）→ 标记异常
    - 同一地址短时间大量交易 → 调查
    """
    
    def __init__(self, name: str, config: dict = None):
        default_config = {
            "price_spike_threshold": 0.20,          # 价格剧烈波动阈值 20%
            "spike_window_ticks": 5,                # 检测窗口（5 ticks）
            "large_trade_multiple": 0.10,           # 大额交易 = 平均成交量 10%
            "circuit_breaker_duration": 10,         # 熔断持续 ticks
            "min_volume_for_review": 1e5,           # 最小审查成交量
            "inspection_interval": 15,              # 审查间隔
            "warning_threshold": 3,                 # 触发警告次数阈值
        }
        if config:
            default_config.update(config)
        super().__init__(name=name, config=default_config)
        self.agent_type = "RegulatorAgent"
        self.tick_counter = 0
        self.monitored_markets = {}
        self.price_history = defaultdict(list)
        self.trade_history = []  # 所有交易记录
        self.violations = defaultdict(list)  # 违规记录 {symbol: [violation]}
        self.active_circuit_breakers = {}  # 活跃熔断 {symbol: expiry_tick}
        self.warnings_issued = defaultdict(int)  # 警告次数

    def perceive(self, world: "WorldStateGraph") -> Dict:
        """感知 - 收集所有市场数据 + 交易流"""
        perception = super().perceive(world)

        # 更新价格历史
        for symbol, data in perception["markets"].items():
            self.price_history[symbol].append({
                "price": data["price"],
                "volume": data.get("volume", 0),
                "tick": self.tick_counter
            })
            if len(self.price_history[symbol]) > self.config["spike_window_ticks"] * 2:
                self.price_history[symbol] = self.price_history[symbol][-self.config["spike_window_ticks"]*2:]

        perception["price_history"] = dict(self.price_history)
        perception["active_circuit_breakers"] = self.active_circuit_breakers.copy()
        perception["violations_summary"] = {
            s: len(v) for s, v in self.violations.items()
        }

        return perception

    def decide(self, perception: Dict) -> Dict:
        """决策 - 检测违规 + 执行监管措施"""
        self.tick_counter += 1
        decisions = []
        violations_detected = []

        # 1. 检查熔断状态
        expired_breakers = []
        for symbol, expiry in self.active_circuit_breakers.items():
            if self.tick_counter >= expiry:
                expired_breakers.append(symbol)
        for symbol in expired_breakers:
            del self.active_circuit_breakers[symbol]
            decisions.append({
                "action": "CIRCUIT_BREAKER_END",
                "symbol": symbol,
                "reason": "熔断期结束，恢复交易"
            })

        # 2. 检测价格 spike
        for symbol, history in self.price_history.items():
            if len(history) >= self.config["spike_window_ticks"]:
                recent = history[-self.config["spike_window_ticks"]:]
                start_price = recent[0]["price"]
                end_price = recent[-1]["price"]
                pct_change = abs((end_price - start_price) / start_price)

                if pct_change > self.config["price_spike_threshold"]:
                    violation = {
                        "type": "price_spike",
                        "symbol": symbol,
                        "pct_change": pct_change,
                        "tick": self.tick_counter,
                        "severity": "HIGH" if pct_change > 0.3 else "MEDIUM"
                    }
                    violations_detected.append(violation)
                    self.violations[symbol].append(violation)

                    # 触发熔断
                    if symbol not in self.active_circuit_breakers:
                        expiry = self.tick_counter + self.config["circuit_breaker_duration"]
                        self.active_circuit_breakers[symbol] = expiry
                        decisions.append({
                            "action": "CIRCUIT_BREAKER_START",
                            "symbol": symbol,
                            "duration": self.config["circuit_breaker_duration"],
                            "reason": f"Price spike {pct_change*100:.1f}% in {self.config['spike_window_ticks']} ticks"
                        })

        # 3. 检测大额交易
        avg_volumes = {}
        for symbol, history in self.price_history.items():
            if history:
                avg_vol = sum(h["volume"] for h in history[-10:]) / min(10, len(history))
                avg_volumes[symbol] = avg_vol

        for symbol, avg_vol in avg_volumes.items():
            current_vol = perception["markets"][symbol].get("volume", 0)
            if current_vol > avg_vol * 3:  # 成交量是平均 3 倍
                violation = {
                    "type": "unusual_volume",
                    "symbol": symbol,
                    "volume_multiple": current_vol / avg_vol,
                    "tick": self.tick_counter,
                    "severity": "MEDIUM"
                }
                violations_detected.append(violation)
                self.violations[symbol].append(violation)

                # 增加违规计数
                self.warnings_issued[symbol] += 1
                if self.warnings_issued[symbol] >= self.config["warning_threshold"]:
                    decisions.append({
                        "action": "ISSUE_WARNING",
                        "symbol": symbol,
                        "reason": f"Repeated volume anomalies ({self.warnings_issued[symbol]} times)"
                    })

        # 4. 检测操纵模式（对敲检测）
        if len(self.trade_history) > 10:
            recent_trades = self.trade_history[-20:]
            counterparty_counts = defaultdict(int)
            for trade in recent_trades:
                counterparty = trade.get("counterparty", "unknown")
                counterparty_counts[counterparty] += 1

            # 如果某个对手方交易过于频繁
            for cp, count in counterparty_counts.items():
                if count > 10:
                    violation = {
                        "type": "wash_trading",
                        "counterparty": cp,
                        "trade_count": count,
                        "tick": self.tick_counter,
                        "severity": "HIGH"
                    }
                    violations_detected.append(violation)
                    decisions.append({
                        "action": "INVESTIGATE",
                        "target": cp,
                        "reason": f"Suspicious wash trading: {count} trades in recent window"
                    })

        # 5. 发布监管报告
        if violations_detected:
            report = {
                "tick": self.tick_counter,
                "violations": violations_detected,
                "active_circuit_breakers": list(self.active_circuit_breakers.keys())
            }
            decisions.append({
                "action": "PUBLISH_REPORT",
                "report": report,
                "reason": "Regulatory compliance update"
            })

        return {
            "decisions": decisions,
            "violations": violations_detected,
            "circuit_breakers_active": list(self.active_circuit_breakers.keys()),
            "strategy": "regulation_enforcement"
        }

    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """执行 - 执行监管措施（不直接交易，只发布规则）"""
        results = []

        for dec in decision.get("decisions", []):
            action = dec["action"]

            if action == "CIRCUIT_BREAKER_START":
                # 熔断：标记该市场暂停交易
                symbol = dec["symbol"]
                results.append({
                    "action": "CIRCUIT_BREAKER_START",
                    "symbol": symbol,
                    "duration": dec["duration"],
                    "effective": True
                })

            elif action == "CIRCUIT_BREAKER_END":
                results.append({
                    "action": "CIRCUIT_BREAKER_END",
                    "symbol": dec["symbol"],
                    "effective": True
                })

            elif action == "ISSUE_WARNING":
                results.append({
                    "action": "WARNING",
                    "target": dec["symbol"],
                    "reason": dec["reason"]
                })

            elif action == "INVESTIGATE":
                results.append({
                    "action": "INVESTIGATION",
                    "target": dec["target"],
                    "reason": dec["reason"]
                })

            elif action == "PUBLISH_REPORT":
                results.append({
                    "action": "REPORT",
                    "report": dec["report"]
                })

        return {
            "actions": results,
            "total_pnl": 0,  # Regulator 不交易
            "regulatory_status": {
                "active_breakers": len(self.active_circuit_breakers),
                "total_violations": sum(len(v) for v in self.violations.values()),
                "warnings_issued": dict(self.warnings_issued)
            },
            "strategy": "regulation_enforcement"
        }

    def record_trade(self, trade: Dict):
        """记录交易（供其他 Agent 调用的钩子）"""
        self.trade_history.append(trade)
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]

    def get_info(self) -> Dict:
        info = super().get_info()
        info["agent_type"] = "RegulatorAgent"
        info["regulatory_status"] = {
            "active_circuit_breakers": len(self.active_circuit_breakers),
            "total_violations": sum(len(v) for v in self.violations.values()),
            "warnings_issued": dict(self.warnings_issued),
            "monitored_markets": list(self.price_history.keys())
        }
        info["recent_violations"] = {
            s: v[-5:] for s, v in self.violations.items()
        }
        return info
