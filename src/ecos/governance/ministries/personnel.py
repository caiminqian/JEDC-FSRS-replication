"""吏部 (Personnel Ministry) - Agent 人事管理
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import random

from ecos.agents import BaseAgent


@dataclass
class AgentRecord:
    """Agent 人事档案"""
    agent_id: str
    name: str
    agent_type: str
    hire_date: str
    performance_score: float = 0.0
    violations: int = 0
    status: str = "active"  # active/suspended/fired
    last_evaluation: Optional[str] = None


class PersonnelMinistry:
    """
    吏部 - 负责人事任免、考核、晋升
    
    职责:
    1. 招聘新 Agent（根据经济需求）
    2. 定期考核 Agent 绩效
    3. 解雇低绩效/违规 Agent
    4. 晋升优秀 Agent（增加资本、权限）
    5. 维护 Agent 花名册
    """
    
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.records: Dict[str, AgentRecord] = {}
        self.hiring_pool = []  # 待招聘的 Agent 类
        
        # 初始化档案
        for agent in agents:
            self.records[agent.agent_id] = AgentRecord(
                agent_id=agent.agent_id,
                name=agent.name,
                agent_type=agent.__class__.__name__,
                hire_date=datetime.now().isoformat(),
                performance_score=0.0
            )
    
    def audit(self, period: int = 100) -> tuple:
        """
        定期审计 (每 period ticks)
        
        Returns:
            (fired_list, hired_list)
        """
        fired = []
        hired = []
        
        for agent_id, record in list(self.records.items()):
            agent = next((a for a in self.agents if a.agent_id == agent_id), None)
            if not agent:
                continue
            
            # 计算绩效分
            score = self._evaluate_performance(agent)
            record.performance_score = score
            
            # 解雇条件
            if score < -100 or record.violations >= 3:
                self._fire_agent(agent, record)
                fired.append(agent.name)
                self.agents.remove(agent)
                del self.records[agent_id]
            
            # 晋升（优秀 Agent 增加资本）
            elif score > 500:
                self._promote_agent(agent)
        
        # 根据经济需求招聘新 Agent
        if len(self.agents) < 50:  # 维持最小规模
            new_agents = self._recruit(count=2)
            hired.extend([a.name for a in new_agents])
            self.agents.extend(new_agents)
            for a in new_agents:
                self.records[a.agent_id] = AgentRecord(
                    agent_id=a.agent_id,
                    name=a.name,
                    agent_type=a.__class__.__name__,
                    hire_date=datetime.now().isoformat(),
                    performance_score=0.0
                )
        
        return fired, hired
    
    def _evaluate_performance(self, agent: BaseAgent) -> float:
        """评估 Agent 绩效 (综合得分)"""
        stats = agent.stats
        rewards = stats.get("rewards", 0)
        errors = stats.get("errors", 0)
        decisions = stats.get("decisions", 0)
        
        # 基础分：总盈亏
        score = rewards * 0.1
        
        # 交易次数奖励（活跃度）
        score += decisions * 0.5
        
        # 错误惩罚
        score -= errors * 10
        
        # Sharpe 比率（简化）
        avg_reward = agent.memory.get_average_reward()
        score += avg_reward * 0.5
        
        return score
    
    def _fire_agent(self, agent: BaseAgent, record: AgentRecord):
        """解雇 Agent"""
        record.status = "fired"
        record.last_evaluation = datetime.now().isoformat()
        print(f"  [吏部] 解雇: {agent.name} (绩效={record.performance_score:.1f})")
    
    def _promote_agent(self, agent: BaseAgent):
        """晋升 Agent（增加资本）"""
        bonus = 10000  # 晋升奖金
        agent.balance += bonus
        agent.generation += 1
        print(f"  [吏部] 晋升: {agent.name} +${bonus:,.0f} (Gen {agent.generation})")
    
    def _recruit(self, count: int = 1) -> List[BaseAgent]:
        """招聘新 Agent（从 hiring_pool 随机选择类型）"""
        from ecos.agents import RetailAgent, InstitutionAgent, MarketMakerAgent, RiskAgent, MacroAgent, AnalystAgent, HumanAgent
        
        pool = [RetailAgent, InstitutionAgent, MarketMakerAgent, RiskAgent, MacroAgent, AnalystAgent, HumanAgent]
        weights = [0.4, 0.2, 0.1, 0.1, 0.1, 0.05, 0.05]  # 招聘概率
        
        new_agents = []
        for _ in range(count):
            AgentClass = random.choices(pool, weights=weights)[0]
            name = f"New_{AgentClass.__name__}_{datetime.now().strftime('%H%M%S')}"
            agent = AgentClass(name=name)
            new_agents.append(agent)
        
        return new_agents
    
    def get_roster(self) -> List[Dict]:
        """获取现任花名册"""
        roster = []
        for record in self.records.values():
            roster.append({
                "name": record.name,
                "type": record.agent_type,
                "status": record.status,
                "score": record.performance_score,
                "hire_date": record.hire_date
            })
        return sorted(roster, key=lambda x: -x["score"])
    
    def get_stats(self) -> Dict:
        return {
            "total_agents": len(self.records),
            "active": sum(1 for r in self.records.values() if r.status == "active"),
            "avg_performance": sum(r.performance_score for r in self.records.values()) / max(1, len(self.records))
        }

    def evaluate_all_agents(self) -> Dict[str, AgentRecord]:
        """
        批量考核所有 Agent（供 GovernanceManager 调用）
        """
        for agent in self.agents:
            score = self._evaluate_performance(agent)
            record = self.records.get(agent.agent_id)
            if record:
                record.performance_score = score
                # 自动状态更新
                if score < 20:
                    record.status = "suspended"
                elif score > 80:
                    record.status = "active"
        
        return self.records

    def get_performance_metrics(self) -> Dict:
        """获取人事绩效指标"""
        return self.get_stats()
