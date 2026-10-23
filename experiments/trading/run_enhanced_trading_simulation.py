"""
Enhanced Multi-Agent Trading Simulation v2.0

Features:
- Realistic limit order book (price-time priority)
- Per-market fee rates
- Matplotlib visualizations (equity curves, rankings, P&L distributions)
- 10 Agents: Human(FSRS) + 5 Retail + 2 Institution + 2 MM
"""

import random
import json
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

SEED = 20260418

# Local RNG for reproducible randomness
rng = random.Random(20260418)
rng.seed(SEED)
np.rng.seed(SEED)

# ========== 市场费用配置 ==========
FEE_RATES = {
    "BTC": 0.0015,   # 高波动，高手续费
    "ETH": 0.0012,
    "AAPL": 0.0005,  # 低波动，低手续费
    "SPY": 0.0005
}

# ========== 数据结构 ==========

@dataclass
class Trade:
    agent_id: str
    tick: int
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    fee: float
    timestamp: str

class Order:
    """限价单"""
    def __init__(self, agent_id: str, symbol: str, side: str, price: float, quantity: float, tick: int):
        self.agent_id = agent_id
        self.symbol = symbol
        self.side = side  # 'bid' | 'ask'
        self.price = price
        self.quantity = quantity
        self.tick = tick
        self.timestamp = tick  # 用于时间优先
    
    def __repr__(self):
        return f"<Order {self.side} {self.quantity:.4f}@{self.price:.2f} by {self.agent_id}>"

class Position:
    """持仓"""
    def __init__(self, symbol: str, size: float, avg_cost: float):
        self.symbol = symbol
        self.size = size
        self.avg_cost = avg_cost
        self.realized_pnl = 0.0
    
    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.avg_cost) * self.size

# ========== 订单簿 ==========

class OrderBook:
    """真实订单簿（价格优先、时间优先）"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: deque = deque()  # 买盘，按价格降序 [(price, total_qty, orders), ...]
        self.asks: deque = deque()  # 卖盘，按价格升序 [(price, total_qty, orders), ...]
    
    def add_order(self, order: Order):
        """添加订单（不立即撮合）"""
        if order.side == 'bid':
            # 插入买盘（价格降序）
            inserted = False
            for i, (price, total, orders) in enumerate(self.bids):
                if order.price > price:
                    self.bids.insert(i, (order.price, order.quantity, [order]))
                    inserted = True
                    break
                elif order.price == price:
                    # 同一价格，按时间追加
                    orders.append(order)
                    self.bids[i] = (price, total + order.quantity, orders)
                    inserted = True
                    break
            if not inserted:
                self.bids.append((order.price, order.quantity, [order]))
        else:  # ask
            # 插入卖盘（价格升序）
            inserted = False
            for i, (price, total, orders) in enumerate(self.asks):
                if order.price < price:
                    self.asks.insert(i, (order.price, order.quantity, [order]))
                    inserted = True
                    break
                elif order.price == price:
                    orders.append(order)
                    self.asks[i] = (price, total + order.quantity, orders)
                    inserted = True
                    break
            if not inserted:
                self.asks.append((order.price, order.quantity, [order]))
    
    def get_best_bid(self) -> Optional[Tuple[float, float]]:
        if self.bids:
            price, total, _ = self.bids[0]
            return price, total
        return None
    
    def get_best_ask(self) -> Optional[Tuple[float, float]]:
        if self.asks:
            price, total, _ = self.asks[0]
            return price, total
        return None
    
    def match_orders(self) -> List[Tuple[Order, Order, float, float]]:
        """
        撮合订单
        
        Returns:
            List of (buy_order, sell_order, trade_price, trade_quantity)
        """
        trades = []
        while self.bids and self.asks:
            bid_price, bid_total, bid_orders = self.bids[0]
            ask_price, ask_total, ask_orders = self.asks[0]
            
            if bid_price < ask_price:
                break  # 无法撮合
            
            # 成交价：通常为买价或卖价中间，这里用卖价（买方接受）
            trade_price = ask_price
            
            # 计算成交量
            trade_qty = min(bid_total, ask_total)
            
            # 分配成交量给订单（按时间优先）
            remaining = trade_qty
            filled_bids = []
            filled_asks = []
            
            # 从买盘开始
            for order in bid_orders:
                if remaining <= 0:
                    break
                fill = min(order.quantity, remaining)
                filled_bids.append((order, fill))
                remaining -= fill
            
            # 从卖盘开始
            remaining = trade_qty
            for order in ask_orders:
                if remaining <= 0:
                    break
                fill = min(order.quantity, remaining)
                filled_asks.append((order, fill))
                remaining -= fill
            
            # 记录成交
            for (buy_order, buy_qty) in filled_bids:
                for (sell_order, sell_qty) in filled_asks:
                    if buy_qty <= 0 or sell_qty <= 0:
                        continue
                    actual_qty = min(buy_qty, sell_qty)
                    trades.append((buy_order, sell_order, trade_price, actual_qty))
                    buy_qty -= actual_qty
                    sell_qty -= actual_qty
            
            # 更新订单簿
            self._update_after_match(trade_qty)
        
        return trades
    
    def _update_after_match(self, filled_qty: float):
        """撮合后更新订单簿（移除或减少订单）"""
        # 简化：直接移除已成交的价格档位（假设该档位全部成交）
        # 实际上应该按订单逐笔减少
        pass
    
    def clear(self):
        """每个 tick 结束时清空订单簿（简化）"""
        self.bids.clear()
        self.asks.clear()

# ========== Agent 包装器（增强版） ==========

class TradingAgentWrapper:
    """支持真实订单簿 + 费用 + 杠杆"""
    
    def __init__(self, agent, config: Dict):
        self.agent = agent
        self.agent_id = agent.agent_id
        self.config = config
        
        # 资金
        self.initial_balance = config.get("initial_balance", agent.balance if hasattr(agent, 'balance') else 100000)
        self.balance = self.initial_balance
        self.credit_line = config.get("credit_line", 0.0)  # 信贷额度（杠杆）
        
        # 持仓
        self.position: Dict[str, Position] = {}  # symbol -> Position
        
        # 统计
        self.trade_history: List[Trade] = []
        self.daily_values: List[float] = []
        self.peak_value = self.initial_balance
        self.max_drawdown = 0.0
        self.leverage_used = 0.0
    
    def get_position(self, symbol: str) -> Optional[Position]:
        return self.position.get(symbol)
    
    def act(self, world: WorldStateGraph, tick: int, order_books: Dict[str, OrderBook]) -> List[Trade]:
        """Agent 提交订单到订单簿"""
        perception = self.agent.perceive(world)
        decision = self.agent.decide(perception)
        
        action = decision.get("action")
        if action not in ["buy", "sell"]:
            return []
        
        symbol = decision.get("symbol", "BTC")
        qty_pct = decision.get("quantity", 0.05)
        order_type = decision.get("order_type", "market")  # market | limit
        
        ob = order_books.get(symbol)
        if not ob:
            return []
        
        # 计算数量
        if action == "buy":
            # 可用余额（包括信贷）
            available = self.balance + self.credit_line
            usd_amount = available * qty_pct
            
            # 获取当前价格（市价单用 ask，限价单用 bid）
            best_ask = ob.get_best_ask()
            if not best_ask:
                return []
            ref_price = best_ask[0]  # 卖一价
            
            price = ref_price
            if order_type == "limit":
                price = round(ref_price * 0.999, 2)  # 略低尝试捡便宜
            
            qty = usd_amount / price
            fee_rate = FEE_RATES.get(symbol, 0.001)
            fee = usd_amount * fee_rate
            total_cost = usd_amount + fee
            
            if self.balance + self.credit_line >= total_cost and usd_amount >= 100:
                # 创建订单
                order = Order(self.agent_id, symbol, 'bid', price, qty, tick)
                ob.add_order(order)
                return []  # 订单未立即成交，暂不返回 Trade
        
        else:  # sell
            pos = self.get_position(symbol)
            if not pos or pos.size <= 0:
                return []
            
            qty = pos.size * qty_pct
            if qty < 0.001:
                return []
            
            best_bid = ob.get_best_bid()
            if not best_bid:
                return []
            ref_price = best_bid[0]
            
            price = ref_price
            if order_type == "limit":
                price = round(ref_price * 1.001, 2)
            
            order = Order(self.agent_id, symbol, 'ask', price, qty, tick)
            ob.add_order(order)
            return []
        
        return []
    
    def process_fills(self, fills: List[Tuple[Order, Order, float, float]], tick: int):
        """处理成交"""
        for buy_order, sell_order, trade_price, trade_qty in fills:
            if buy_order.agent_id != self.agent_id and sell_order.agent_id != self.agent_id:
                continue  # 不相关
            
            fee_rate = FEE_RATES.get(buy_order.symbol, 0.001)
            fee = trade_price * trade_qty * fee_rate
            
            if buy_order.agent_id == self.agent_id:
                # 买入
                cost = trade_price * trade_qty + fee
                self.balance -= cost
                
                # 更新持仓
                pos = self.get_position(buy_order.symbol)
                if pos:
                    old_qty = pos.size
                    old_avg = pos.avg_cost
                    new_qty = old_qty + trade_qty
                    new_avg = (old_avg * old_qty + trade_price * trade_qty) / new_qty
                    pos.size = new_qty
                    pos.avg_cost = new_avg
                else:
                    self.position[buy_order.symbol] = Position(buy_order.symbol, trade_qty, trade_price)
                
                self.trade_history.append(Trade(
                    self.agent_id, tick, buy_order.symbol, "buy", trade_qty, trade_price, fee,
                    datetime.now(timezone.utc).isoformat()
                ))
            
            if sell_order.agent_id == self.agent_id:
                # 卖出
                proceeds = trade_price * trade_qty - fee
                self.balance += proceeds
                
                pos = self.get_position(sell_order.symbol)
                if pos:
                    realized = (trade_price - pos.avg_cost) * trade_qty
                    pos.realized_pnl += realized
                    pos.size -= trade_qty
                    if pos.size <= 0.0001:
                        del self.position[sell_order.symbol]
                
                self.trade_history.append(Trade(
                    self.agent_id, tick, sell_order.symbol, "sell", trade_qty, trade_price, fee,
                    datetime.now(timezone.utc).isoformat()
                ))
    
    def update_value(self, world: WorldStateGraph):
        total = self.balance
        for sym, pos in self.position.items():
            node = f"market:{sym}"
            if node in world.graph.nodes:
                price = world.graph.nodes[node]["price"]
                total += pos.size * price
        self.daily_values.append(total)
        if total > self.peak_value:
            self.peak_value = total
        dd = (self.peak_value - total) / self.peak_value if self.peak_value > 0 else 0
        if dd > self.max_drawdown:
            self.max_drawdown = dd

# ========== 市场模拟器（增强） ==========

class EnhancedMarketSimulator:
    """支持订单簿和费用梯度"""
    
    def __init__(self, world: WorldStateGraph, config: Dict):
        self.world = world
        self.config = config
        self.order_books: Dict[str, OrderBook] = {}
        self.trade_log: List[Trade] = []
    
    def initialize(self):
        for symbol in self.config["markets"]:
            self.order_books[symbol] = OrderBook(symbol)
    
    def update_prices(self):
        """价格演化（基于前一天的收盘价）"""
        for node_id, data in self.world.graph.nodes(data=True):
            if data.get("type") != "market":
                continue
            vol = data.get("volatility", 0.02)
            drift = 0.0002
            shock = rng.gauss(0, vol)
            change_pct = drift + shock
            new_price = max(0.01, data["price"] * (1 + change_pct))
            self.world.update_node(node_id, {
                "price": round(new_price, 2),
                "change": round(change_pct, 6),
                "bid": round(new_price * 0.999, 2),
                "ask": round(new_price * 1.001, 2)
            })
    
    def trigger_black_swan(self) -> Tuple[bool, str, float]:
        if rng.random() < self.config["shock_prob"]:
            markets = [n for n, d in self.world.graph.nodes(data=True) if d.get("type") == "market"]
            if markets:
                target = rng.choice(markets)
                data = self.world.nodes[target]
                severity = rng.uniform(0.15, 0.40)
                new_price = data["price"] * (1 - severity)
                self.world.update_node(target, {
                    "price": round(new_price, 2),
                    "change": -severity,
                    "bid": round(new_price * 0.999, 2),
                    "ask": round(new_price * 1.001, 2)
                })
                return True, data["symbol"], severity
        return False, None, 0.0
    
    def match_all(self, tick: int) -> List[Trade]:
        """所有市场的订单撮合"""
        all_fills = []
        for symbol, ob in self.order_books.items():
            fills = ob.match_orders()
            for buy_order, sell_order, price, qty in fills:
                fee_rate = FEE_RATES.get(symbol, 0.001)
                fee = price * qty * fee_rate
                trade = Trade(
                    agent_id=buy_order.agent_id,  # 买方
                    tick=tick,
                    symbol=symbol,
                    side="buy",
                    quantity=qty,
                    price=price,
                    fee=fee/2,  # 买卖各半（简化）
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.trade_log.append(trade)
                all_fills.append((buy_order, sell_order, price, qty))
        return all_fills
    
    def clear_books(self):
        for ob in self.order_books.values():
            ob.clear()

# ========== 主模拟器（增强） ==========

class EnhancedTradingSimulation:
    def __init__(self, config: Dict):
        self.config = config
        self.world = WorldStateGraph()
        self.market = EnhancedMarketSimulator(self.world, config)
        self.agents: List[TradingAgentWrapper] = []
        self.tick = 0
    
    def initialize(self):
        # 市场
        for symbol in self.config["markets"]:
            price = self.config["initial_prices"][symbol]
            vol = self.config["volatilities"][symbol]
            self.world.add_node(
                node_id=f"market:{symbol}",
                node_type="market",
                attributes={
                    "symbol": symbol,
                    "price": price,
                    "change": 0.0,
                    "bid": round(price * 0.999, 2),
                    "ask": round(price * 1.001, 2),
                    "volatility": vol,
                    "category": "crypto" if symbol in ["BTC", "ETH"] else "equity"
                }
            )
        self.market.initialize()
        print(f"[OK] {len(self.config['markets'])} markets + order books ready")
        
        # Agents
        self._create_agents()
        print(f"[OK] {len(self.agents)} agents ready")
    
    def _create_agents(self):
        # Human (FSRS)
        human = HumanAgent("AlphaTrader", config={"initial_balance": 250000}, rng=rng)
        self.agents.append(TradingAgentWrapper(human, {"initial_balance": 250000, "credit_line": 50000}))
        
        # Retail (5)
        for i in range(self.config.get("n_retail", 5)):
            retail = RetailAgent(f"Retail_{i+1:03d}", config={
                "initial_balance": rng.randint(30000, 80000, rng=rng)
            })
            self.agents.append(TradingAgentWrapper(retail, {"initial_balance": retail.config["initial_balance"]}))
        
        # Institution (2)
        for i in range(self.config.get("n_institution", 2)):
            inst = RetailAgent(f"Inst_{i+1:03d}", config={
                "initial_balance": rng.randint(500000, 2000000, rng=rng)
            })
            self.agents.append(TradingAgentWrapper(inst, {"initial_balance": inst.config["initial_balance"], "credit_line": 200000}))
        
        # MM (2)
        for i in range(self.config.get("n_mm", 2)):
            mm = RetailAgent(f"MM_{i+1:03d}", config={"initial_balance": 1000000}, rng=rng)
            self.agents.append(TradingAgentWrapper(mm, {"initial_balance": 1000000, "credit_line": 0}))
    
    def run(self):
        print("="*70)
        print(f"ENHANCED TRADING SIMULATION: {self.config['ticks']} ticks")
        print("="*70)
        
        shocks = 0
        human_wrapper = self.agents[0]
        
        for tick in range(self.config["ticks"]):
            self.tick = tick
            
            # 1. 黑天鹅 + HumanAgent 记忆更新
            shocked, symbol, severity = self.market.trigger_black_swan()
            if shocked:
                shocks += 1
                print(f"  Tick {tick:4d}: [BLACK SWAN] {symbol} -{severity*100:.1f}%")
                if human_wrapper.agent.use_fsrs:
                    grade = 2 if severity >= 0.5 else 3
                    res = human_wrapper.agent.process_market_shock(tick, shock_grade=grade)
                else:
                    quality = rng.randint(3, 5)
                    res = human_wrapper.agent.process_market_shock(tick, severity=severity, quality=quality)
                S_val = res.get('new_S', res.get('avg_S_after', '?'))
                print(f"    Human S -> {S_val}")
            
            # 2. 价格演化
            self.market.update_prices()
            
            # 3. Agent 提交订单
            for wrapper in self.agents:
                wrapper.act(self.world, tick, self.market.order_books)
            
            # 4. 订单撮合
            fills = self.market.match_all(tick)
            for wrapper in self.agents:
                wrapper.process_fills(fills, tick)
            
            # 5. 清空订单簿（每日重新开始）
            self.market.clear_books()
            
            # 6. 每日更新统计
            for wrapper in self.agents:
                wrapper.update_value(self.world)
            
            if tick % 20 == 0:
                self._print_ranking(tick)
        
        self._print_final(shocks)
        return self._collect()
    
    def _print_ranking(self, tick: int):
        ranking = []
        for w in self.agents:
            val = w.daily_values[-1] if w.daily_values else w.initial_balance
            ranking.append((w.agent_id, type(w.agent).__name__, val))
        ranking.sort(key=lambda x: x[2], reverse=True)
        print(f"\n  --- Leaderboard (tick {tick}) ---")
        for rank, (aid, atype, val) in enumerate(ranking[:5], 1):
            print(f"    {rank}. {aid:<15} {atype:<10} ${val:>12,.0f}")
    
    def _print_final(self, shocks: int):
        print("\n" + "="*70)
        print("SIMULATION COMPLETE")
        print("="*70)
        print(f"Total shocks: {shocks}")
        
        final = []
        for w in self.agents:
            val = w.daily_values[-1] if w.daily_values else w.initial_balance
            pnl = val - w.initial_balance
            final.append((w.agent_id, type(w.agent).__name__, val, pnl, w.max_drawdown, len(w.trade_history)))
        final.sort(key=lambda x: x[2], reverse=True)
        
        print("\n{'Rank':<5} {'Agent':<15} {'Type':<10} {'Portfolio':>15} {'P&L':>12} {'MaxDD':>8} {'Trades':>7}")
        print("-" * 80)
        for i, (aid, atype, val, pnl, dd, trades) in enumerate(final, 1):
            print(f"{i:<5} {aid:<15} {atype:<10} ${val:>14,.0f} {pnl:>+12,.0f} {dd*100:>7.1f}% {trades:>7}")
    
    def _collect(self) -> Dict:
        results = {"config": self.config, "agents": []}
        for w in self.agents:
            val = w.daily_values[-1] if w.daily_values else w.initial_balance
            results["agents"].append({
                "agent_id": w.agent_id,
                "type": type(w.agent).__name__,
                "engine": "FSRS" if isinstance(w.agent, HumanAgent) and w.agent.use_fsrs else "N/A",
                "initial_balance": w.initial_balance,
                "final_value": val,
                "pnl": val - w.initial_balance,
                "max_drawdown": w.max_drawdown,
                "total_trades": len(w.trade_history),
                "daily_values": w.daily_values,
                "final_positions": {k: {"size": v.size, "avg_cost": v.avg_cost, "realized_pnl": v.realized_pnl} 
                                    for k, v in w.position.items()}
            })
        return results

# ========== 可视化 ==========

def plot_results(results: Dict, output_prefix: str = "output/enhanced_sim"):
    """生成所有图表"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        agents_data = results["agents"]
        ticks = list(range(len(agents_data[0]["daily_values"])))
        
        # 1. 总资产曲线（所有 Agent）
        plt.figure(figsize=(14, 7))
        for agent in agents_data:
            label = f"{agent['agent_id']} ({agent['engine']})"
            plt.plot(ticks, agent["daily_values"], label=label, linewidth=1.5)
        plt.xlabel("Day")
        plt.ylabel("Portfolio Value ($)")
        plt.title("Agent Equity Curves")
        plt.legend(fontsize=8)
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_prefix}_equity.png", dpi=150, bbox_inches='tight')
        plt.close()
        print(f"[OK] Equity curves saved to {output_prefix}_equity.png")
        
        # 2. P&L 分布（柱状图）
        plt.figure(figsize=(10, 6))
        pnls = [a["pnl"] for a in agents_data]
        labels = [a["agent_id"] for a in agents_data]
        colors = ['green' if p >= 0 else 'red' for p in pnls]
        bars = plt.bar(range(len(pnls)), pnls, color=colors, alpha=0.7)
        plt.axhline(0, color='k', linewidth=0.8)
        plt.xlabel("Agent")
        plt.ylabel("P&L ($)")
        plt.title("Final P&L by Agent")
        plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
        # 标注数值
        for bar, pnl in zip(bars, pnls):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f"${pnl:,.0f}", ha='center', va='bottom' if pnl >= 0 else 'top', fontsize=8)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_pnl_distribution.png", dpi=150)
        plt.close()
        print(f"[OK] P&L distribution saved to {output_prefix}_pnl_distribution.png")
        
        # 3. 最大回撤对比
        plt.figure(figsize=(10, 6))
        max_dds = [a["max_drawdown"] * 100 for a in agents_data]
        plt.bar(range(len(max_dds)), max_dds, color='orange', alpha=0.7)
        plt.xlabel("Agent")
        plt.ylabel("Max Drawdown (%)")
        plt.title("Maximum Drawdown by Agent")
        plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_max_drawdown.png", dpi=150)
        plt.close()
        print(f"[OK] Max drawdown chart saved to {output_prefix}_max_drawdown.png")
        
        # 4. 交易频率（散点：交易次数 vs 最终收益）
        plt.figure(figsize=(10, 6))
        trades = [a["total_trades"] for a in agents_data]
        pnls = [a["pnl"] for a in agents_data]
        plt.scatter(trades, pnls, s=80, alpha=0.7)
        plt.xlabel("Number of Trades")
        plt.ylabel("P&L ($)")
        plt.title("Trading Activity vs Profit")
        plt.grid(True, alpha=0.3)
        # 标注 Agent
        for i, aid in enumerate(labels):
            plt.annotate(aid, (trades[i], pnls[i]), fontsize=8, alpha=0.7)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_trades_vs_pnl.png", dpi=150)
        plt.close()
        print(f"[OK] Trades vs P&L scatter saved to {output_prefix}_trades_vs_pnl.png")
        
    except ImportError:
        print("[WARN] matplotlib not available, skipping plots")

# ========== 主入口 ==========

def run_enhanced_simulation():
    config = {
        "ticks": 200,
        "markets": ["BTC", "ETH", "AAPL"],
        "initial_prices": {"BTC": 45000, "ETH": 3000, "AAPL": 175},
        "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015},
        "shock_prob": 0.03,
        "n_retail": 5,
        "n_institution": 2,
        "n_mm": 2
    }
    
    sim = EnhancedTradingSimulation(config)
    sim.initialize()
    results = sim.run()
    
    # 保存结果
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/enhanced_trading_simulation.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results saved to output/enhanced_trading_simulation.json")
    
    # 生成图表
    plot_results(results, output_prefix="output/enhanced_sim")
    
    return results

if __name__ == "__main__":
    run_enhanced_simulation()
    print("\n[DONE]")