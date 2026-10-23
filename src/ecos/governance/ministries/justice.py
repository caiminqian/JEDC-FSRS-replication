"""刑部 (Justice Ministry) - 司法与处罚
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


@dataclass
class Violation:
    """违规行为记录"""
    violation_id: str
    agent_id: str
    agent_name: str
    violation_type: str    # "market_manipulation", "insider_trading", "circuit_breaker_violation"
    tick: int
    severity: int          # 1-5
    evidence: Dict
    status: str = "pending"  # pending/investigating/sentenced/cleared


@dataclass
class Sentence:
    """处罚判决"""
    sentence_id: str
    violation_id: str
    agent_id: str
    penalty_type: str      # "fine", "suspension", "confiscation", "ban"
    penalty_amount: float = 0.0
    duration_ticks: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class JusticeMinistry:
    """
    刑部 - 大理寺
    
    职责:
    1. 调查违规行为（从 RegulatorAgent 接收报告）
    2. 审理案件
    3. 判决处罚（罚款、暂停交易、冻结资产、驱逐）
    4. 维护市场秩序
    
    处罚类型:
    - 罚款（国库收入）
    - 暂停交易（禁止下单 N 个 ticks）
    - 没收资产（部分或全部）
    - 永久禁入（驱逐出系统）
    """
    
    def __init__(self):
        self.violations: Dict[str, Violation] = {}
        self.sentences: List[Sentence] = []
        self.fines_collected = 0.0
        self.suspended_agents: Dict[str, int] = {}  # agent_id -> suspension_end_tick
        self.violation_counter = 0
        
    def receive_violation_report(self, report: Dict):
        """
        接收违规报告（来自 RegulatorAgent）
        
        Args:
            report: {
                "tick": 123,
                "symbol": "BTC",
                "type": "price_spike",
                "agent_involved": ["Agent_001", ...],
                "evidence": {...}
            }
        """
        for agent_name in report.get("agents_involved", []):
            violation = Violation(
                violation_id=f"VIOL_{self.violation_counter:04d}",
                agent_id=agent_name,  # 简化：name 作为 ID
                agent_name=agent_name,
                violation_type=report.get("type", "unknown"),
                tick=report.get("tick", 0),
                severity=self._assess_severity(report),
                evidence=report.get("evidence", {})
            )
            self.violations[violation.violation_id] = violation
            self.violation_counter += 1
            
            # 立即审理（简化为自动判决）
            sentence = self._sentence_violation(violation)
            self.sentences.append(sentence)
            self._execute_sentence(sentence)
    
    def _assess_severity(self, report: Dict) -> int:
        """评估违规严重程度 (1-5)"""
        vtype = report.get("type", "")
        if vtype == "price_spike":
            pct_change = report.get("pct_change", 0)
            if pct_change > 0.3: return 5
            elif pct_change > 0.2: return 4
            elif pct_change > 0.15: return 3
            else: return 2
        elif vtype == "wash_trading":
            return 5  # 对敲是严重违规
        elif vtype == "unusual_volume":
            return 2
        return 1
    
    def _sentence_violation(self, violation: Violation) -> Sentence:
        """判决"""
        severity = violation.severity
        
        if severity >= 4:
            penalty_type = "fine"
            penalty_amount = 1e5  # 10 万罚款
            duration = 0
        elif severity >= 3:
            penalty_type = "suspension"
            penalty_amount = 0
            duration = 20  # 停权 20 ticks
        else:
            penalty_type = "warning"
            penalty_amount = 0
            duration = 0
        
        return Sentence(
            sentence_id=f"SENT_{violation.violation_id[-4:]}",
            violation_id=violation.violation_id,
            agent_id=violation.agent_id,
            penalty_type=penalty_type,
            penalty_amount=penalty_amount,
            duration_ticks=duration
        )
    
    def _execute_sentence(self, sentence: Sentence):
        """执行处罚"""
        agent_id = sentence.agent_id
        
        if sentence.penalty_type == "fine":
            # TODO: 从 agent 余额扣除
            self.fines_collected += sentence.penalty_amount
            print(f"  [刑部] 罚款: {agent_id} ${sentence.penalty_amount:,.0f}")
        
        elif sentence.penalty_type == "suspension":
            self.suspended_agents[agent_id] = sentence.duration_ticks
            print(f"  [刑部] 停权: {agent_id} {sentence.duration_ticks} ticks")
        
        elif sentence.penalty_type == "warning":
            print(f"  [刑部] 警告: {agent_id}")
    
    def update(self, current_tick: int):
        """更新状态（检查停权到期）"""
        expired = []
        for agent_id, remaining in self.suspended_agents.items():
            if remaining <= 0:
                expired.append(agent_id)
            else:
                self.suspended_agents[agent_id] = remaining - 1
        
        for agent_id in expired:
            del self.suspended_agents[agent_id]
            print(f"  [刑部] 停权结束: {agent_id}")
    
    def is_agent_suspended(self, agent_id: str) -> bool:
        """检查 Agent 是否被停权"""
        return agent_id in self.suspended_agents
    
    def detect_anomalies(self, world_state: Dict) -> List[Dict]:
        """
        从世界状态中检测异常行为（自动违规检测）

        Returns:
            anomalies 列表
        """
        anomalies = []
        agents_data = world_state.get("agents", [])
        
        for agent_node in agents_data:
            agent_id = agent_node.get("agent_id", "")
            pnl = agent_node.get("stats", {}).get("rewards", 0)
            trades = agent_node.get("stats", {}).get("trades", 0)
            
            # 检测大额盈利（市场操纵嫌疑）
            if pnl > 50000:
                anomalies.append({
                    "agent_id": agent_id,
                    "violation": "unusual_profit",
                    "severity": 4,
                    "tick": world_state.get("tick", 0)
                })
            # 检测高频交易
            if trades > 100:
                anomalies.append({
                    "agent_id": agent_id,
                    "violation": "excessive_trading",
                    "severity": 2,
                    "tick": world_state.get("tick", 0)
                })
        
        # 将异常转换为违规报告
        for anomaly in anomalies:
            self.receive_violation_report({
                "tick": anomaly["tick"],
                "type": anomaly["violation"],
                "agents_involved": [anomaly["agent_id"]],
                "severity": anomaly["severity"]
            })
        
        return anomalies

    def enforce_penalty(self, agent_id: str, violation_type: str) -> Sentence:
        """
        对指定 agent 执行处罚
        """
        severity_map = {
            "market_manipulation": 5,
            "insider_trading": 5,
            "unusual_profit": 4,
            "excessive_trading": 2,
            "circuit_breaker_violation": 3
        }
        severity = severity_map.get(violation_type, 1)
        
        violation = Violation(
            violation_id=f"VIOL_AUTO_{self.violation_counter:04d}",
            agent_id=agent_id,
            agent_name=agent_id,
            violation_type=violation_type,
            tick=0,
            severity=severity,
            evidence={}
        )
        
        sentence = self._sentence_violation(violation)
        self._execute_sentence(sentence)
        self.sentences.append(sentence)
        self.violations[violation.violation_id] = violation
        self.violation_counter += 1
        
        return sentence

    def get_performance_metrics(self) -> Dict:
        """获取司法绩效指标"""
        return {
            "violations_processed": len(self.violations),
            "fines_collected": self.fines_collected,
            "suspensions_active": len(self.suspended_agents)
        }

    def review_cases(self) -> List[Violation]:
        """审查待处理的违规案件（返回 pending 状态的违规）"""
        pending = [v for v in self.violations.values() if v.status == "pending"]
        # 标记为调查中
        for v in pending:
            v.status = "investigating"
        return pending
    
    def get_statistics(self) -> Dict:
        return {
            "total_violations": len(self.violations),
            "total_sentences": len(self.sentences),
            "fines_collected": self.fines_collected,
            "currently_suspended": len(self.suspended_agents),
            "recent_violations": list(self.violations.values())[-10:]
        }


__all__ = ["JusticeMinistry", "Violation", "Sentence"]
