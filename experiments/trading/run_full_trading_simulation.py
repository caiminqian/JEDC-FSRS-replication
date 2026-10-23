"""
Full Multi-Agent Trading Simulation (Final)

Corrected for BaseTraderAgent position format and FSRS return structure.
"""

import random
import json
from datetime import datetime, timezone
from typing import Dict, List
from dataclasses import dataclass

from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.human_agent import HumanAgent
from ecos.agents.trader.retail_agent import RetailAgent

SEED = 20260418

# Local RNG for reproducible randomness
rng = random.Random(20260418)
rng.seed(SEED)

@dataclass
class Trade:
    agent_id: str
    tick: int
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    timestamp: str

class TradingAgentWrapper:
    def __init__(self, agent):
        self.agent = agent
        self.agent_id = agent.agent_id
        self.initial_balance = agent.balance
        self.trade_history: List[Trade] = []
        self.daily_values: List[float] = []
        self.peak_value = self.initial_balance
        self.max_drawdown = 0.0
    
    def _get_pos(self, symbol: str) -> Dict:
        if hasattr(self.agent, 'position') and symbol in self.agent.position:
            return self.agent.position[symbol]
        return None
    
    def _set_pos(self, symbol: str, size: float, avg_cost: float):
        if not hasattr(self.agent, 'position'):
            self.agent.position = {}
        self.agent.position[symbol] = {
            'size': size,
            'avg_cost': avg_cost,
            'realized_pnl': 0.0
        }
    
    def act(self, world: WorldStateGraph, tick: int) -> List[Trade]:
        trades = []
        perception = self.agent.perceive(world)
        decision = self.agent.decide(perception)
        
        action = decision.get("action")
        if action not in ["buy", "sell"]:
            return trades
        
        symbol = decision.get("symbol", "BTC")
        qty_pct = decision.get("quantity", 0.05)
        node_id = f"market:{symbol}"
        if node_id not in world.graph.nodes:
            return trades
        market = world.graph.nodes[node_id]
        
        if action == "buy":
            price = round(market["bid"] * 1.001, 2)
            usd_amount = self.agent.balance * qty_pct
            fee = usd_amount * 0.001
            total = usd_amount + fee
            if self.agent.balance >= total and usd_amount >= 100:
                qty = usd_amount / price
                trade = self._exec(tick, symbol, "buy", qty, price)
                if trade:
                    trades.append(trade)
        else:
            price = round(market["ask"] * 0.999, 2)
            pos = self._get_pos(symbol)
            if not pos or pos['size'] <= 0:
                return trades
            qty = pos['size'] * qty_pct
            if qty < 0.001:
                return trades
            trade = self._exec(tick, symbol, "sell", qty, price)
            if trade:
                trades.append(trade)
        
        return trades
    
    def _exec(self, tick: int, symbol: str, side: str, qty: float, price: float) -> Trade:
        fee = price * qty * 0.001
        trade = Trade(
            agent_id=self.agent_id,
            tick=tick,
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            fee=fee,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.trade_history.append(trade)
        
        if side == "buy":
            cost = price * qty
            self.agent.balance -= (cost + fee)
            pos = self._get_pos(symbol)
            if pos:
                old_qty = pos['size']
                old_avg = pos['avg_cost']
                new_qty = old_qty + qty
                new_avg = (old_avg * old_qty + price * qty) / new_qty
                self._set_pos(symbol, new_qty, new_avg)
            else:
                self._set_pos(symbol, qty, price)
        else:
            proceeds = price * qty
            self.agent.balance += (proceeds - fee)
            pos = self._get_pos(symbol)
            if pos:
                realized = (price - pos['avg_cost']) * qty
                pos['realized_pnl'] = pos.get('realized_pnl', 0) + realized
                pos['size'] -= qty
                if pos['size'] <= 0.0001:
                    del self.agent.position[symbol]
        
        return trade
    
    def update_value(self, world: WorldStateGraph):
        total = self.agent.balance
        if hasattr(self.agent, 'position'):
            for sym, pos in self.agent.position.items():
                node = f"market:{sym}"
                if node in world.graph.nodes:
                    price = world.graph.nodes[node]["price"]
                    total += pos['size'] * price
        self.daily_values.append(total)
        if total > self.peak_value:
            self.peak_value = total
        dd = (self.peak_value - total) / self.peak_value if self.peak_value > 0 else 0
        if dd > self.max_drawdown:
            self.max_drawdown = dd

class MarketSimulator:
    def __init__(self, world: WorldStateGraph, config: Dict):
        self.world = world
        self.config = config
    
    def update_prices(self):
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
    
    def trigger_black_swan(self):
        if rng.random() < self.config["shock_prob"]:
            markets = [n for n, d in self.world.graph.nodes(data=True) if d.get("type") == "market"]
            if markets:
                target = rng.choice(markets)
                data = self.world.graph.nodes[target]
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

class FullTradingSimulation:
    def __init__(self, config: Dict):
        self.config = config
        self.world = WorldStateGraph()
        self.market = MarketSimulator(self.world, config)
        self.agents: List[TradingAgentWrapper] = []
        self.tick = 0
    
    def initialize(self):
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
        print(f"[OK] {len(self.config['markets'])} markets initialized")
        self._create_agents()
        print(f"[OK] {len(self.agents)} agents created")
    
    def _create_agents(self):
        # Human (FSRS default)
        human = HumanAgent("AlphaTrader", config={"initial_balance": 250000}, rng=rng)
        self.agents.append(TradingAgentWrapper(human))
        
        # Retail
        for i in range(self.config.get("n_retail", 5)):
            retail = RetailAgent(f"Retail_{i+1:03d}", config={
                "initial_balance": rng.randint(30000, 80000, rng=rng)
            })
            self.agents.append(TradingAgentWrapper(retail))
        
        # Institution
        for i in range(self.config.get("n_institution", 2)):
            inst = RetailAgent(f"Inst_{i+1:03d}", config={
                "initial_balance": rng.randint(500000, 2000000, rng=rng)
            })
            self.agents.append(TradingAgentWrapper(inst))
        
        # MM
        for i in range(self.config.get("n_mm", 2)):
            mm = RetailAgent(f"MM_{i+1:03d}", config={"initial_balance": 1000000}, rng=rng)
            self.agents.append(TradingAgentWrapper(mm))
    
    def run(self):
        print("="*70)
        print(f"FULL TRADING SIMULATION: {self.config['ticks']} days")
        print("="*70)
        
        shocks = 0
        human_wrapper = self.agents[0]
        
        for tick in range(self.config["ticks"]):
            self.tick = tick
            
            # 1. Black swan
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
                # FSRS returns avg_S_after, EE returns new_S
                S_val = res.get('new_S', res.get('avg_S_after', '?'))
                print(f"    Human (FSRS={human_wrapper.agent.use_fsrs}): S -> {S_val}")
            
            # 2. Price update
            self.market.update_prices()
            
            # 3. Agents trade
            for wrapper in self.agents:
                wrapper.act(self.world, tick)
            
            # 4. Every 20 days: update stats & ranking
            if tick % 20 == 0:
                for wrapper in self.agents:
                    wrapper.update_value(self.world)
                self._print_ranking(tick)
        
        # Final
        for wrapper in self.agents:
            wrapper.update_value(self.world)
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
        print(f"Total black swans: {shocks}")
        
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
                "final_positions": self._get_pos(w.agent)
            })
        return results
    
    def _get_pos(self, agent) -> Dict:
        if hasattr(agent, 'position'):
            return {k: {"size": v.get("size", 0), "avg_cost": v.get("avg_cost", 0), 
                       "realized_pnl": v.get("realized_pnl", 0)} 
                    for k, v in agent.position.items()}
        return {}

def run_full_sim():
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
    sim = FullTradingSimulation(config)
    sim.initialize()
    results = sim.run()
    
    import os
    os.makedirs("output", exist_ok=True)
    with open("output/full_trading_simulation.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results saved to output/full_trading_simulation.json")
    return results

if __name__ == "__main__":
    run_full_sim()
    print("\n[DONE]")