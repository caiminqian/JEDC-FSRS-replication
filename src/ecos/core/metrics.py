"""Prometheus metrics exporter for ECOS.

Exposes key simulation metrics for VictoriaMetrics/Grafana scraping.
Usage:
    from ecos.core.metrics import METRICS, expose_metrics
    METRICS['ecos_agents_total'].set(len(agents))
    expose_metrics(port=8000)  # starts HTTP server
"""

from prometheus_client import Gauge, Counter, Histogram, start_http_server, Enum
from typing import Dict

# System metrics
AGENTS_TOTAL = Gauge('ecos_agents_total', 'Total number of agents registered')
AGENTS_ACTIVE = Gauge('ecos_agents_active', 'Number of currently active agents')
AGENTS_BY_TYPE = Gauge('ecos_agents_by_type', 'Agent count by type', ['agent_type'])
AGENTS_CREATED_TOTAL = Counter('ecos_agents_created_total', 'Total agents created')
CURRENT_TICK = Gauge('ecos_current_tick', 'Current simulation tick')

# Memory metrics
MEMORY_AVG_R = Gauge('ecos_memory_avg_r', 'Average retrievability R across all agents')
MEMORY_AVG_R_FSRS = Gauge('ecos_memory_avg_r_fsrs', 'Average R for FSRS agents')
MEMORY_AVG_R_EE = Gauge('ecos_memory_avg_r_ee', 'Average R for EE agents')
MEMORY_STABILITY_HIST = Histogram('ecos_memory_stability', 'FSRS stability S distribution',
                                  buckets=[1, 5, 10, 20, 50, 100, 500, 1000, 5000, float('inf')])
MEMORY_CRITICAL_COUNT = Gauge('ecos_memory_critical_count', 'Agents with R < 0.3 (critical)')

# Market metrics
MARKET_PRICE = Gauge('ecos_market_price', 'Market price', ['symbol'])
MARKET_VOLATILITY = Gauge('ecos_market_volatility', 'Market volatility', ['symbol'])
MARKET_LIQUIDITY = Gauge('ecos_market_liquidity', 'Market liquidity', ['symbol'])
MARKET_VOLUME = Gauge('ecos_market_volume', 'Market volume', ['symbol'])

# Risk diffusion metrics (SIR)
RISK_SUSCEPTIBLE = Gauge('ecos_risk_susceptible', 'Agents in Susceptible state')
RISK_INFECTED = Gauge('ecos_risk_infected', 'Agents in Infected state')
RISK_RECOVERED = Gauge('ecos_risk_recovered', 'Agents in Recovered/Bankrupt state')
RISK_ACTIVE = Gauge('ecos_risk_active', 'Agents in Active (no risk) state')
RISK_SYSTEMIC_INDEX = Gauge('ecos_risk_systemic_index', 'Systemic risk index 0-1')
RISK_EVENTS_TOTAL = Counter('ecos_risk_events_total', 'Total risk events', ['risk_type', 'source', 'target'])

# Governance metrics
GOV_INTERVENTIONS_TOTAL = Counter('ecos_governance_interventions_total', 'Total interventions')
GOV_COGNITIVE_INTERVENTIONS = Counter('ecos_governance_cognitive_interventions', 'Cognitive interventions (memory-based)')
GOV_VETO_RATE = Gauge('ecos_governance_veto_rate', 'Veto rate 0-1')
GOV_DECISIONS_TOTAL = Counter('ecos_governance_decisions_total', 'Total governance decisions', ['ministry'])
TREASURY_BALANCE = Gauge('ecos_treasury_balance', 'Treasury balance (户部)')
TREASURY_NETFLOW = Gauge('ecos_treasury_netflow', 'Treasury net flow per tick')
TAX_COLLECTED_TOTAL = Counter('ecos_tax_collected_total', 'Total taxes collected')
INTERVENTIONS_TOTAL = Counter('ecos_interventions_total', 'Total market interventions')

# Trade/experiment metrics
TRADES_TOTAL = Counter('ecos_trades_total', 'Total trades executed')
EXPERIMENT_FINAL_R = Gauge('ecos_experiment_final_r', 'Final retrievability R', ['engine', 'experiment'])
EXPERIMENT_PNL = Gauge('ecos_experiment_pnl', 'Final P&L', ['engine', 'experiment'])
EXPERIMENT_MAX_DD = Gauge('ecos_experiment_max_drawdown', 'Max drawdown', ['engine', 'experiment'])
EXPERIMENT_TRADES = Gauge('ecos_experiment_trades', 'Total trades', ['engine', 'experiment'])
EXPERIMENT_SHOCKS = Gauge('ecos_experiment_shocks', 'Total shocks experienced', ['engine', 'experiment'])

# Event metrics
SHOCK_EVENTS_TOTAL = Counter('ecos_shock_events', 'Market shock events', ['severity', 'symbol'])

# Collect all metrics for easy iteration
METRICS: Dict[str, object] = {
    # System
    'ecos_agents_total': AGENTS_TOTAL,
    'ecos_agents_active': AGENTS_ACTIVE,
    'ecos_agents_by_type': AGENTS_BY_TYPE,
    'ecos_current_tick': CURRENT_TICK,
    # Memory
    'ecos_memory_avg_r': MEMORY_AVG_R,
    'ecos_memory_avg_r_fsrs': MEMORY_AVG_R_FSRS,
    'ecos_memory_avg_r_ee': MEMORY_AVG_R_EE,
    'ecos_memory_stability_hist': MEMORY_STABILITY_HIST,
    'ecos_memory_critical_count': MEMORY_CRITICAL_COUNT,
    # Markets
    'ecos_market_price': MARKET_PRICE,
    'ecos_market_volatility': MARKET_VOLATILITY,
    'ecos_market_liquidity': MARKET_LIQUIDITY,
    'ecos_market_volume': MARKET_VOLUME,
    # Risk
    'ecos_risk_susceptible': RISK_SUSCEPTIBLE,
    'ecos_risk_infected': RISK_INFECTED,
    'ecos_risk_recovered': RISK_RECOVERED,
    'ecos_risk_active': RISK_ACTIVE,
    'ecos_risk_systemic_index': RISK_SYSTEMIC_INDEX,
    'ecos_risk_events_total': RISK_EVENTS_TOTAL,
    # Governance
    'ecos_governance_interventions_total': GOV_INTERVENTIONS_TOTAL,
    'ecos_governance_cognitive_interventions': GOV_COGNITIVE_INTERVENTIONS,
    'ecos_governance_veto_rate': GOV_VETO_RATE,
    'ecos_governance_decisions_total': GOV_DECISIONS_TOTAL,
    'ecos_treasury_balance': TREASURY_BALANCE,
    'ecos_treasury_netflow': TREASURY_NETFLOW,
    # Experiments
    'ecos_experiment_final_r': EXPERIMENT_FINAL_R,
    'ecos_experiment_pnl': EXPERIMENT_PNL,
    'ecos_experiment_max_drawdown': EXPERIMENT_MAX_DD,
    'ecos_experiment_trades': EXPERIMENT_TRADES,
    'ecos_experiment_shocks': EXPERIMENT_SHOCKS,
    # Events
    'ecos_shock_events': SHOCK_EVENTS_TOTAL,
}


# Global server reference to prevent garbage collection
_METRICS_SERVER = None
_METRICS_THREAD = None

def expose_metrics(port: int = 8000, addr: str = '0.0.0.0'):
    """Start Prometheus HTTP server on specified port.

    Args:
        port: Port to bind (default 8000).
        addr: Address to bind. Use '0.0.0.0' for IPv4 (recommended for Windows compatibility).
              Default is '0.0.0.0'.
    """
    global _METRICS_SERVER, _METRICS_THREAD
    try:
        _METRICS_SERVER, _METRICS_THREAD = start_http_server(port, addr=addr)
        import socket
        # Verify binding by attempting a connection
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            s.connect(('127.0.0.1', port))
            print(f"[Metrics] Successfully bound to {addr}:{port} (verified)")
        except Exception as e:
            print(f"[Metrics] Bound to {addr}:{port} but cannot self-connect: {e}")
        finally:
            s.close()
    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).error(f"Failed to start metrics server: {e}\n{traceback.format_exc()}")
        raise
    print(f"[Metrics] Prometheus endpoint listening on :{port}/metrics")


# ========== Helper functions for main.py ==========

def start_metrics_server(port: int = 9090):
    """Start metrics server (alias for expose_metrics).

    This is the function name expected by main.py.
    """
    expose_metrics(port)


def update_world_metrics(world) -> None:
    """Update all world-related metrics.

    Extracts market data from WorldStateGraph and updates:
    - MARKET_PRICE (per symbol)
    - MARKET_VOLATILITY (per symbol)
    - MARKET_LIQUIDITY (per symbol)
    - MARKET_VOLUME (per symbol)
    """
    try:
        market_data = world.get_market_data()  # Dict[symbol, Dict]
        for symbol, data in market_data.items():
            price = data.get('price', 0.0)
            volatility = data.get('volatility', 0.0)
            liquidity = data.get('liquidity', 1.0)
            volume = data.get('volume', 0.0)

            MARKET_PRICE.labels(symbol=symbol).set(price)
            MARKET_VOLATILITY.labels(symbol=symbol).set(volatility)
            MARKET_LIQUIDITY.labels(symbol=symbol).set(liquidity)
            MARKET_VOLUME.labels(symbol=symbol).set(volume)
    except Exception as e:
        # Log but don't crash - metrics should be best-effort
        import logging
        logging.getLogger(__name__).warning(f"Failed to update world metrics: {e}")


def update_agent_metrics(agents) -> None:
    """Update all agent-related metrics.

    Computes:
    - AGENTS_TOTAL: total agent count
    - AGENTS_ACTIVE: count of agents with active=True
    - AGENTS_BY_TYPE: breakdown by agent_type label
    - MEMORY_AVG_R: average overall_R across all cognitive agents
    - MEMORY_AVG_R_FSRS: average R for FSRS agents only
    - MEMORY_AVG_R_EE: average R for EE agents only
    - MEMORY_CRITICAL_COUNT: agents with R < 0.3
    """
    if not agents:
        return

    total = len(agents)
    active = sum(1 for a in agents if getattr(a, 'active', True))
    AGENTS_TOTAL.set(total)
    AGENTS_ACTIVE.set(active)

    # Count by type
    type_counts: Dict[str, int] = {}
    for agent in agents:
        atype = getattr(agent, 'agent_type', type(agent).__name__)
        type_counts[atype] = type_counts.get(atype, 0) + 1
    for atype, count in type_counts.items():
        AGENTS_BY_TYPE.labels(agent_type=atype).set(count)

    # Memory R collection (dual-engine aware)
    r_ee = []
    r_fsrs = []

    for agent in agents:
        # FSRS engine
        if hasattr(agent, 'use_fsrs') and agent.use_fsrs and hasattr(agent, 'memory_fsrs'):
            try:
                awareness = agent.memory_fsrs.get_risk_awareness(current_tick=getattr(agent, 'sim_tick', 0))
                R = awareness.get('overall_R', 0.0)
                r_fsrs.append(R)
            except Exception:
                pass
        # EE engine
        elif hasattr(agent, 'cognitive_memory'):
            try:
                from datetime import datetime, timezone, timedelta
                sim_time = datetime.now(timezone.utc) + timedelta(days=getattr(agent, 'sim_tick', 0))
                awareness = agent.cognitive_memory.get_risk_awareness(current_time=sim_time)
                R = awareness.get('overall_R', 0.0)
                r_ee.append(R)
            except Exception:
                pass

    all_R = r_fsrs + r_ee
    if all_R:
        MEMORY_AVG_R.set(sum(all_R) / len(all_R))
    if r_fsrs:
        MEMORY_AVG_R_FSRS.set(sum(r_fsrs) / len(r_fsrs))
    if r_ee:
        MEMORY_AVG_R_EE.set(sum(r_ee) / len(r_ee))

    critical = sum(1 for R in all_R if R < 0.3)
    MEMORY_CRITICAL_COUNT.set(critical)

    # Update stability histogram for FSRS agents
    for agent in agents:
        if hasattr(agent, 'use_fsrs') and agent.use_fsrs and hasattr(agent, 'memory_fsrs'):
            try:
                # FSRS memory stores stability S per memory item
                # Collect all stability values from agent's memories
                if hasattr(agent.memory_fsrs, 'memories'):
                    for mem in agent.memory_fsrs.memories.values():
                        S = getattr(mem, 'stability', 0.0)
                        MEMORY_STABILITY_HIST.observe(S)
            except Exception:
                pass


def update_risk_metrics(risk_engine) -> None:
    """Update risk diffusion metrics from RiskDiffusionEngine.

    Sets:
    - RISK_SUSCEPTIBLE
    - RISK_INFECTED
    - RISK_RECOVERED
    - RISK_ACTIVE
    - RISK_SYSTEMIC_INDEX
    """
    try:
        metrics = risk_engine.get_metrics() if hasattr(risk_engine, 'get_metrics') else {}
        RISK_SUSCEPTIBLE.set(metrics.get('susceptible', 0))
        RISK_INFECTED.set(metrics.get('infected', 0))
        RISK_RECOVERED.set(metrics.get('recovered', 0))
        RISK_ACTIVE.set(metrics.get('active', 0))
        RISK_SYSTEMIC_INDEX.set(metrics.get('systemic_risk_index', 0.0))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to update risk metrics: {e}")


def update_systemic_risk(risk_score: float) -> None:
    """Update systemic risk score (alias for direct metric set).

    Args:
        risk_score: float between 0-1 representing overall systemic risk.
    """
    try:
        RISK_SYSTEMIC_INDEX.set(max(0.0, min(1.0, risk_score)))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to set systemic risk: {e}")


def record_trade(symbol: str, direction: str, volume: float) -> None:
    """Record a completed trade.

    Args:
        symbol: Trading symbol (e.g., "BTC", "AAPL")
        direction: "buy" or "sell"
        volume: Trade volume in quote currency (size * price)
    """
    try:
        TRADES_TOTAL.inc()
        # Could also record per-symbol metrics in the future
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to record trade: {e}")

