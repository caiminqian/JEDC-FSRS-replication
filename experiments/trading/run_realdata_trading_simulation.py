"""
Full Multi-Agent Trading Simulation (Final)

Corrected for BaseTraderAgent position format and FSRS return structure.

v2 (sim_tick fix, user-approved 2026-10-26): identical to phase2_trading_sim.py (v1)
except the sim_tick sync block in run() step 2b. No other semantic change.
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
    """Real prices (Phase 2): each tick sets all markets to that trading day's real closes.
    No synthetic noise, no synthetic price shocks: real prices already contain the crashes."""

    def __init__(self, world: WorldStateGraph, config: Dict):
        self.world = world
        self.config = config
        self.days = config["days"]        # list of date strings, tick t <-> days[t]
        self.prices = config["prices"]    # {symbol: {date: adjclose}}

    def set_day_prices(self, tick: int):
        day = self.days[tick]
        for node_id, data in self.world.graph.nodes(data=True):
            if data.get("type") != "market":
                continue
            symbol = data["symbol"]
            new_price = self.prices[symbol][day]
            prev = data["price"]
            change_pct = (new_price / prev - 1.0) if prev else 0.0
            self.world.update_node(node_id, {
                "price": round(new_price, 2),
                "change": round(change_pct, 6),
                "bid": round(new_price * 0.999, 2),
                "ask": round(new_price * 1.001, 2)
            })

class FullTradingSimulation:
    def __init__(self, config: Dict):
        self.config = config
        self.world = WorldStateGraph()
        self.market = MarketSimulator(self.world, config)
        self.agents: List[TradingAgentWrapper] = []
        self.tick = 0
        self.shock_days = config["shock_days"]  # {tick: VIX grade}

    def _ee_severity(self, tick: int) -> float:
        """EE-branch severity (pre-registered): |equal-weight portfolio daily return|, capped 0.40.
        Tick 0 has no in-window previous day; falls back to 0.0 (never fires in W1/W2)."""
        if tick == 0:
            print("    WARNING: tick-0 EE shock, severity fallback 0.0")
            return 0.0
        rets = []
        for symbol in self.config["markets"]:
            p = self.config["prices"][symbol]
            rets.append(p[self.config["days"][tick]] / p[self.config["days"][tick - 1]] - 1.0)
        return min(0.40, abs(sum(rets) / len(rets)))
    
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
        # Human (engine selected by config; construction otherwise identical to E2E)
        hcfg = {"initial_balance": 250000}
        if not self.config.get("use_fsrs", True):
            hcfg["use_fsrs"] = False
        human = HumanAgent("AlphaTrader", config=hcfg, rng=rng)
        # Frozen v55 kernel + bank assertions (module defaults must equal the J2-landed values)
        from ecos.agents.fsrs_memory import FSRS_DEFAULT_PARAMS, FSRSMemoryBank
        assert FSRS_DEFAULT_PARAMS == {"w17": 0.6096, "w18": 0.0496, "w19": 0.1841, "w20": 0.4}, FSRS_DEFAULT_PARAMS
        assert FSRSMemoryBank.LESSONS["leverage_risk"]["initial_S"] == 0.75
        assert FSRSMemoryBank.LESSONS["liquidity_crisis"]["initial_S"] == 0.45
        assert FSRSMemoryBank.LESSONS["bull_market_complacency"]["initial_S"] == 0.30
        assert human.use_fsrs == self.config.get("use_fsrs", True)
        self.agents.append(TradingAgentWrapper(human))
        
        # Retail
        for i in range(self.config.get("n_retail", 5)):
            retail = RetailAgent(f"Retail_{i+1:03d}", config={
                "initial_balance": rng.randint(30000, 80000)
            })
            self.agents.append(TradingAgentWrapper(retail))
        
        # Institution
        for i in range(self.config.get("n_institution", 2)):
            inst = RetailAgent(f"Inst_{i+1:03d}", config={
                "initial_balance": rng.randint(500000, 2000000)
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
            
            # 1. Real VIX grade-change shock (memory only; prices are real, never shocked)
            grade = self.shock_days.get(tick)
            if grade is not None:
                shocks += 1
                print(f"  Tick {tick:4d}: [VIX SHOCK] grade G{grade} ({self.market.days[tick]})")
                if human_wrapper.agent.use_fsrs:
                    res = human_wrapper.agent.process_market_shock(tick, shock_grade=grade)
                else:
                    severity = self._ee_severity(tick)
                    res = human_wrapper.agent.process_market_shock(tick, severity=severity, quality=4)
                # FSRS returns avg_S_after, EE returns new_S
                S_val = res.get('new_S', res.get('avg_S_after', '?'))
                print(f"    Human (FSRS={human_wrapper.agent.use_fsrs}): S -> {S_val}")

            # 2. Real prices for this trading day
            self.market.set_day_prices(tick)

            # 2b. Sync agent's sim_tick for memory decay (ecos_env.py:144)
            # Without this, HumanAgent.decide() evaluates memory at tick 0 and
            # risk_R is pinned at 1.0 (get_retrievability returns 1.0 for t <= 0).
            for wrapper in self.agents:
                wrapper.agent.sim_tick = tick

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
                "final_positions": self._get_pos(w.agent),
                # Output-only: trade tape for post-hoc Sharpe (excludes wall-clock timestamps).
                # Appended after the loop; cannot affect decisions, PnL, or DD.
                "trade_history": [{"tick": t.tick, "symbol": t.symbol, "side": t.side,
                                   "quantity": t.quantity, "price": t.price, "fee": t.fee}
                                  for t in w.trade_history]
            })
        return results
    
    def _get_pos(self, agent) -> Dict:
        if hasattr(agent, 'position'):
            return {k: {"size": v.get("size", 0), "avg_cost": v.get("avg_cost", 0), 
                       "realized_pnl": v.get("realized_pnl", 0)} 
                    for k, v in agent.position.items()}
        return {}

def run_variant(window: str, engine: str, data_path: str, out_path: str):
    with open(data_path) as f:
        all_data = json.load(f)
    w = all_data[window]
    days = w["days"]
    prices = w["prices"]
    shock_days = {days.index(d): g for d, g in w["shock_days"]}
    config = {
        "ticks": len(days),
        "markets": ["BTC", "ETH", "AAPL"],
        "initial_prices": {s: prices[s][days[0]] for s in ["BTC", "ETH", "AAPL"]},
        "volatilities": {"BTC": 0.03, "ETH": 0.035, "AAPL": 0.015},
        "days": days,
        "prices": prices,
        "shock_days": shock_days,
        "window": window,
        "engine": engine,
        "use_fsrs": engine == "FSRS",
        "source": "Yahoo Finance chart API (adjclose)",
    }
    sim = FullTradingSimulation(config)
    sim.initialize()
    results = sim.run()
    results["shock_days"] = [{"tick": t, "date": days[t], "grade": g} for t, g in sorted(shock_days.items())]
    import os
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results saved to {out_path}")
    return results

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", required=True, choices=["W1", "W2"])
    ap.add_argument("--engine", required=True, choices=["FSRS", "EE"])
    ap.add_argument("--data", default="phase2_prices.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run_variant(a.window, a.engine, a.data, a.out)
