"""Governance Manager - 协调六部 + 风险层 + Agent 生命周期(简化版)

直接调用六部职能,不经过三省流程(快速原型)。
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from ecos.core.world_state import WorldStateGraph
from ecos.governance.ministries import (
    FinanceMinistry, PersonnelMinistry, RitualMinistry,
    MilitaryMinistry, JusticeMinistry, WorksMinistry
)
from ecos.risk.diffusion import RiskDiffusionEngine
from ecos.risk.systemic_risk import SystemicRiskMonitor
from ecos.risk.liquidity_risk import LiquidityRiskAnalyzer
from ecos.agents.trader.retail_agent import RetailAgent

logger = logging.getLogger(__name__)


# Simulation start time (used for EE datetime conversion)
SIM_START = datetime.now(timezone.utc)

from ecos.core.metrics import METRICS, AGENTS_BY_TYPE, MARKET_PRICE, MARKET_VOLATILITY
class GovernanceManager:
    """治理协调器 - 每 tick 执行"""

    def __init__(self, world: WorldStateGraph, agents: List, dynamic_population: bool = True, rng: random.Random = None):
        self.world = world
        self.agents = agents
        self.dynamic_population = dynamic_population

        # 六部
        self.ministries = {
            "hubu": FinanceMinistry(agents=agents, initial_treasury=1e6),
            "libu_renshi": PersonnelMinistry(agents=agents),
            "libu_libian": RitualMinistry(),
            "bingbu": MilitaryMinistry(world=world),
            "xingbu": JusticeMinistry(),
            "gongbu": WorksMinistry(world=world)
        }

        # 风险层
        self.rng = rng or random
        self.risk_engine = RiskDiffusionEngine(world, rng=self.rng)
        self.systemic_monitor = SystemicRiskMonitor(world, risk_engine=self.risk_engine)
        self.liquidity_analyzer = LiquidityRiskAnalyzer(world)
        self.risk_engine.initialize_agents(agents)


        # EE 集体记忆监控(门下省宏观审慎)
        self.collective_memory_threshold = 0.25  # 平均 R 值警报阈值
        self.memory_monitoring_enabled = True
        self.memory_intervention_count = 0
        self.contagion_alpha = 0.6  # 传染系数 (校准后: 5-event grid → 0.6)
        self.last_memory_shock_time = None
        self.treasury_history: List[float] = []

        logger.info("🏛️ Governance Manager initialized (6 ministries + risk + lifecycle)")

    def tick(self, tick_number: int) -> Dict:
        """每 tick 治理流程"""
        self._current_tick = tick_number
        # ===== EE 集体记忆监控(门下省)=====
        if self.memory_monitoring_enabled:
            collective_state = self._assess_collective_memory(tick_number)
            if collective_state["intervention_needed"]:
                summary["interventions"].append({
                    "type": "cognitive_intervention",
                    "reason": "collective_memory_decay",
                    "avg_R": collective_state["avg_R"],
                    "action": "macroprudential_shock"
                })
                summary["risk"]["cognitive_intervention"] = True

        # 既有实现中该传染逻辑连续执行两次, 重构后通过同一辅助方法调用两次保持行为一致
        self._apply_info_flow_contagion()
        self._apply_info_flow_contagion()


        summary = {
            "tick": tick_number,
            "budget_changes": {},
            "interventions": [],
            "anomalies": 0,
            "maintenance": None,
            "agent_lifecycle": {},
            "risk": {},
            "liquidity": {}
        }

        world_state = self.world.to_dict()

        # 六部职能 + 风险层 + Agent 生命周期
        self._run_ministry_actions(tick_number, summary, world_state)

        # 记录国库
        self.treasury_history.append(self.ministries["hubu"].treasury)

        
        # --- Metrics Export (VictoriaMetrics / Grafana) ---
        self._export_tick_metrics(summary, tick_number)

        return summary

    def _apply_info_flow_contagion(self) -> None:
        """通过 info_flow 边传播风险警惕性 R, 更新每个 Agent 的感知 R(不修改实际记忆)"""
        perceived_R = self._compute_contagion_R(alpha=self.contagion_alpha)
        for agent in self.agents:
            if agent.agent_id in perceived_R:
                agent._perceived_R = perceived_R[agent.agent_id]

    def _run_ministry_actions(self, tick_number: int, summary: Dict, world_state: Dict) -> None:
        """六部职能调度 + 风险层 + Agent 生命周期(每 tick 治理的具体执行)"""
        # 1. 户部:税收
        tax = self.ministries["hubu"].collect_taxes()
        if tick_number == 1:
            self.ministries["hubu"].create_annual_budget()
        summary["budget_changes"] = {
            "tax_collected": tax,
            "treasury": self.ministries["hubu"].treasury
        }

        # 2. 兵部:市场稳定
        stab = self.ministries["bingbu"].stabilize_market()
        if stab:
            summary["interventions"].append({
                "market": stab.target_market,
                "action": stab.action,
                "amount": stab.amount
            })

        # 3. 吏部:考核(每100 ticks)
        if tick_number % 100 == 0:
            evals = self.ministries["libu_renshi"].evaluate_all_agents()
            summary["agent_evaluations"] = len(evals)

        # 4. 刑部:异常检测
        anomalies = self.ministries["xingbu"].detect_anomalies(world_state)
        if anomalies:
            for a in anomalies:
                self.ministries["xingbu"].enforce_penalty(a["agent_id"], a["violation"])
            summary["anomalies"] = len(anomalies)

        # 5. 工部:维护(每500 ticks)
        if tick_number % 500 == 0:
            summary["maintenance"] = self.ministries["gongbu"].perform_maintenance()

        # 6. 风险扩散
        risk_sum = self.risk_engine.tick(world_state, tick_number)
        summary["risk"] = {
            "systemic_index": risk_sum["systemic_risk_index"],
            "infected": risk_sum["infected"],
            "recovered": risk_sum["recovered"],
            "bankruptcies": risk_sum["bankruptcies"],
            "intervention_needed": risk_sum["intervention_triggered"]
        }

        # 7. 系统性风险监测
        systemic = self.systemic_monitor.calculate_metrics(tick_number)
        summary["risk"]["systemic"] = {
            "connectivity": systemic.connectivity,
            "concentration": systemic.concentration,
            "critical_nodes": systemic.critical_nodes[:5],
            "warnings": systemic.warnings
        }

        # 8. 流动性风险
        liquidity = self.liquidity_analyzer.analyze(tick_number, world_state)
        summary["liquidity"] = {
            "score": liquidity["overall_liquidity_score"],
            "high_risk": liquidity["high_risk_markets"]
        }

        # 9. Agent 生命周期(每100 ticks)
        if tick_number % 100 == 0:
            summary["agent_lifecycle"] = self._manage_agents(tick_number, world_state)

    def _export_tick_metrics(self, summary: Dict, tick_number: int) -> None:
        """将本 tick 治理结果导出到 Prometheus / VictoriaMetrics(异常不中断模拟)"""
        try:
            METRICS['ecos_current_tick'].set(tick_number)
            METRICS['ecos_agents_total'].set(len(self.agents))
            active_count = sum(1 for a in self.agents if getattr(a, 'is_active', True))
            METRICS['ecos_agents_active'].set(active_count)
            # Agents by type
            type_counts = {}
            for a in self.agents:
                atype = getattr(a, 'agent_type', type(a).__name__)
                type_counts[atype] = type_counts.get(atype, 0) + 1
            for atype, count in type_counts.items():
                AGENTS_BY_TYPE.labels(agent_type=atype).set(count)
            # Collective memory
            collective_state = self._assess_collective_memory(tick_number)
            if 'avg_R' in collective_state:
                METRICS['ecos_memory_avg_r'].set(collective_state['avg_R'])
            # Market data
            market_data = self.world.get_market_data()
            for symbol, data in market_data.items():
                MARKET_PRICE.labels(symbol=symbol).set(data.get('price', 0))
                MARKET_VOLATILITY.labels(symbol=symbol).set(data.get('volatility', 0))
                # Liquidity may be missing
                if 'liquidity' in data:
                    from ecos.core.metrics import METRICS as M
                    M['ecos_market_liquidity'].labels(symbol=symbol).set(data.get('liquidity', 0))
            # Risk summary
            risk_sum = self.risk_engine.get_risk_summary()
            METRICS['ecos_risk_susceptible'].set(risk_sum.get('susceptible', 0))
            METRICS['ecos_risk_infected'].set(risk_sum.get('infected', 0))
            METRICS['ecos_risk_recovered'].set(risk_sum.get('recovered', 0))
            METRICS['ecos_risk_active'].set(risk_sum.get('active', 0))
            METRICS['ecos_risk_systemic_index'].set(risk_sum.get('systemic_index', 0))
            # Treasury
            METRICS['ecos_treasury_balance'].set(summary.get('budget_changes', {}).get('total_treasury', 0))
            # Cognitive interventions
            if summary.get('risk', {}).get('cognitive_intervention'):
                METRICS['ecos_governance_cognitive_interventions'].inc()
            # Shock events (count shocks this tick from summary)
            shocks_this_tick = summary.get('shocks_this_tick', 0)
            if shocks_this_tick > 0:
                METRICS['ecos_shock_events'].labels(severity='medium', symbol='MARKET').inc(shocks_this_tick)
        except Exception:
            # Metrics should never break simulation
            pass

    def _manage_agents(self, tick: int, world_state: Dict) -> Dict:
        """Agent 出生/死亡/退休"""
        events = {"births": 0, "deaths": 0, "retirements": 0}
        to_remove = []

        for agent in self.agents:
            if getattr(agent, 'balance', 0) <= 0:
                to_remove.append(agent)
                events["deaths"] += 1
            elif getattr(agent, 'stats', {}).get('avg_reward', 0) < -500 and tick > 500:
                to_remove.append(agent)
                events["retirements"] += 1

        for agent in to_remove:
            if agent in self.agents:
                self.agents.remove(agent)
            if self.world.graph.has_node(agent.agent_id):
                self.world.remove_node(agent.agent_id)
            for m in self.ministries.values():
                if hasattr(m, 'agents') and agent in m.agents:
                    m.agents.remove(agent)

        # 新 Agent
        if self.agents:
            active_ratio = sum(1 for a in self.agents if getattr(a, 'active', True)) / len(self.agents)
        else:
            active_ratio = 0
        if self.dynamic_population and active_ratio > 0.7 and len(self.agents) < 200:
            new_count = max(1, (200 - len(self.agents)) // 50)
            for i in range(new_count):
                new_agent = RetailAgent(
                    name=f"Retail_NEW_{tick}_{i}",
                    config={"initial_balance": 10000, "fomo_factor": 0.3}
                )
                self.agents.append(new_agent)
                self.world.add_node(
                    node_id=new_agent.agent_id,
                    node_type="agent",
                    attributes={"name": new_agent.name, "balance": new_agent.balance}
                )
                for m in self.ministries.values():
                    if hasattr(m, 'agents'):
                        m.agents.append(new_agent)
                events["births"] += 1
                logger.info(f"  [Lifecycle] New agent: {new_agent.name}")

        return events

    def _assess_collective_memory(self, tick_number: int) -> Dict:
        """
        门下省: 评估全市场 Agent 集体记忆衰退程度 (tick-based, dual-engine)

        Returns:
            {avg_R, critical_agents, intervention_needed, trend, memory_engine}
        """
        if not self.memory_monitoring_enabled:
            return {"intervention_needed": False}

        Rs = []
        critical_agents = []
        memory_engine = "ee"

        for agent in self.agents:
            if hasattr(agent, 'use_fsrs') and agent.use_fsrs and hasattr(agent, 'memory_fsrs'):
                awareness = agent.memory_fsrs.get_risk_awareness(current_tick=tick_number)
                memory_engine = "fsrs"
            elif hasattr(agent, 'cognitive_memory'):
                sim_time = SIM_START + timedelta(days=tick_number)
                awareness = agent.cognitive_memory.get_risk_awareness(current_time=sim_time)
            else:
                continue

            R = awareness["overall_R"]
            Rs.append(R)
            if R < 0.2:
                critical_agents.append(agent.agent_id)

        if not Rs:
            return {"intervention_needed": False}

        avg_R = sum(Rs) / len(Rs)
        intervention_needed = avg_R < self.collective_memory_threshold

        trend = "stable"
        if hasattr(self, '_last_avg_R'):
            if avg_R < self._last_avg_R - 0.05:
                trend = "decaying"
            elif avg_R > self._last_avg_R + 0.05:
                trend = "recovering"
        self._last_avg_R = avg_R
        self._memory_trend = trend

        if intervention_needed:
            logger.warning(
                f"[门下省] 集体记忆衰退警报: avg_R={avg_R:.2f} "
                f"({len(critical_agents)} agents critically low). Triggering shock."
            )
            self._trigger_memory_shock(tick_number, critical_agents)

        return {
            "avg_R": avg_R,
            "critical_agents": critical_agents,
            "intervention_needed": intervention_needed,
            "trend": trend,
            "agent_count": len(Rs),
            "memory_engine": memory_engine
        }


    def _compute_global_shock_grade(self, tick_number: int) -> Optional[int]:
        """
        计算全局市场冲击等级 G (FSRS 模式)

        Args:
            tick_number: 当前 tick

        Returns:
            G ∈ {1,2,3,4} 或 None (无显著冲击)
                G=1: 系统性崩溃 (≥50% 平均跌幅)
                G=2: 深度股灾 (≥20% 平均跌幅)
                G=3: 标准熊市 (≥10% 平均跌幅)
                G=4: 轻微回调 (≥5% 平均跌幅)
        """
        # 获取所有市场节点的平均跌幅
        market_nodes = self.world.get_nodes_by_type('market')
        if not market_nodes:
            return None

        total_drawdown = 0
        count = 0
        for node_id in market_nodes:
            market_data = self.world.get_node(node_id)
            if market_data:
                change = market_data.get('change', 0)
                if change < 0:
                    total_drawdown += abs(change)
                count += 1

        avg_drawdown = total_drawdown / count if count > 0 else 0

        if avg_drawdown >= 0.5:
            return 1
        elif avg_drawdown >= 0.2:
            return 2
        elif avg_drawdown >= 0.1:
            return 3
        elif avg_drawdown >= 0.05:
            return 4
        else:
            return None

    def _trigger_memory_shock(self, tick_number: int, target_agents: Optional[List[str]] = None):
        self.memory_intervention_count += 1

        use_fsrs = False
        if self.agents:
            first = self.agents[0]
            if hasattr(first, 'use_fsrs') and first.use_fsrs:
                use_fsrs = True

        if use_fsrs:
            global_grade = self._compute_global_shock_grade(tick_number)
            if global_grade is None:
                logger.debug(f"[门下省] 第 {self.memory_intervention_count} 次检查: 无显著冲击")
                return 0
            grade_counts = {1:0,2:0,3:0,4:0}
            affected = 0
            for agent in self.agents:
                if target_agents is not None and agent.agent_id not in target_agents:
                    continue
                if hasattr(agent, 'memory_fsrs') and hasattr(agent, 'process_market_shock'):
                    agent.process_market_shock(shock_tick=tick_number, shock_grade=global_grade)
                    grade_counts[global_grade] += 1
                    affected += 1
            grade_dist = ", ".join([f"G{g}:{c}" for g,c in sorted(grade_counts.items()) if c>0])
            logger.info(
                f"[门下省] 第 {self.memory_intervention_count} 次认知干预 (FSRS): "
                f"对 {affected} 个 Agent 触发复习 (grade={global_grade}, dist=[{grade_dist}])"
            )
        else:
            shock_severity = 0.5
            import random
            affected = 0; quality_counts = {0:0,1:0,2:0,3:0,4:0,5:0}
            for agent in self.agents:
                if target_agents is not None and agent.agent_id not in target_agents:
                    continue
                if hasattr(agent, 'process_market_shock'):
                    base_q = int(shock_severity * 5)
                    if hasattr(agent, 'cognitive_memory'):
                        sim_time = SIM_START + timedelta(days=tick_number)
                        R = agent.cognitive_memory.get_risk_awareness(current_time=sim_time)['overall_R']
                        R_penalty = max(0, (0.3 - R) * 2)
                        base_q = max(0, min(5, base_q - R_penalty))
                    q = max(0, min(5, base_q + self.rng.uniform(-0.5, 0.5)))
                    q_rounded = int(round(q))
                    quality_counts[q_rounded] += 1
                    agent.process_market_shock(
                        shock_tick=tick_number,
                        severity=shock_severity,
                        quality=q_rounded
                    )
                    affected += 1
            quality_dist = ", ".join([f"q{q}:{c}" for q,c in sorted(quality_counts.items()) if c>0])
            logger.info(
                f"[门下省] 第 {self.memory_intervention_count} 次认知干预 (EE): "
                f"对 {affected} 个 Agent 触发复习 (severity={shock_severity}, quality=[{quality_dist}])"
            )
        self.last_memory_shock_time = tick_number
        return affected

    def get_collective_memory_stats(self) -> Dict:
        """获取集体记忆统计(用于监控面板)"""
        if not hasattr(self, '_last_avg_R'):
            return {"avg_R": None, "trend": "unknown", "interventions": 0}

        return {
            "avg_R": self._last_avg_R,
            "trend": getattr(self, '_memory_trend', 'stable'),
            "interventions": self.memory_intervention_count,
            "last_shock": self.last_memory_shock_time
        }


    def _compute_contagion_R(self, alpha: float = 0.6) -> Dict[str, float]:
        """
        计算通过 info_flow 边传染后的感知风险值 R_perceived (tick-based, dual-engine)
        """
        current_tick = getattr(self, '_current_tick', 0)

        true_R = {}
        for agent in self.agents:
            if hasattr(agent, 'use_fsrs') and agent.use_fsrs and hasattr(agent, 'memory_fsrs'):
                R = agent.memory_fsrs.get_risk_awareness(current_tick)['overall_R']
                true_R[agent.agent_id] = R
            elif hasattr(agent, 'cognitive_memory'):
                sim_time = SIM_START + timedelta(days=current_tick)
                R = agent.cognitive_memory.get_risk_awareness(current_time=sim_time)['overall_R']
                true_R[agent.agent_id] = R

        neighbors = {aid: [] for aid in true_R}
        for u, v, data in self.world.graph.edges(data=True):
            if data.get('type') != 'info_flow':
                continue
            uid = u.split(':', 1)[-1] if ':' in u else u
            vid = v.split(':', 1)[-1] if ':' in v else v
            if uid in true_R and vid in true_R:
                neighbors[uid].append(vid)
                neighbors[vid].append(uid)

        perceived_R = {}
        for agent_id, R_self in true_R.items():
            nbrs = neighbors[agent_id]
            if not nbrs:
                perceived_R[agent_id] = R_self
            else:
                R_nbr = sum(true_R[n] for n in nbrs) / len(nbrs)
                perceived_R[agent_id] = (1 - alpha) * R_self + alpha * R_nbr
        return perceived_R



    def get_performance_report(self) -> Dict:
        """获取治理绩效报告"""
        report = {
            "total_decisions": 0,
            "veto_rate": 0,
            "treasury_trend": self.treasury_history[-100:],
            "ministry_activity": {},
            "risk_metrics": self.risk_engine.get_metrics() if self.risk_engine else {},
            "systemic_risk": {},
            "liquidity": {}
        }

        for name, ministry in self.ministries.items():
            if hasattr(ministry, 'get_performance_metrics'):
                report["ministry_activity"][name] = ministry.get_performance_metrics()
            else:
                report["ministry_activity"][name] = {"status": "active"}

        if self.systemic_monitor and self.systemic_monitor.metrics_history:
            sm = self.systemic_monitor.metrics_history[-1]
            report["systemic_risk"] = {
                "overall": sm.overall_risk,
                "connectivity": sm.connectivity,
                "concentration": sm.concentration,
                "warnings": sm.warnings
            }

        return report
