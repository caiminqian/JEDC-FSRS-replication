"""尚书省 (Department of Works) - 执行调度部门
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from .types import Task, Edict, EdictStatus
from .secretariat import Secretariat
from .chancellery import Chancellery


class DepartmentOfWorks:
    """
    尚书省 - 尚书令（首席行政官）领导
    
    职责:
    1. 接收门下省通过的诏书
    2. 将诏书分解为具体任务
    3. 分配给六部执行
    4. 跟踪任务进度
    5. 资源调配（人力、财力）
    
    六部归尚书省管辖：
    - 吏部 (Personnel)  - 人事
    - 户部 (Finance)    - 财政
    - 礼部 (Ritual)     - 礼仪/宣传
    - 兵部 (Military)   - 军事/市场干预
    - 刑部 (Justice)    - 司法
    - 工部 (Works)      - 工程/基建
    """
    
    def __init__(self, world, agents, event_bus):
        self.world = world
        self.agents = agents
        self.event_bus = event_bus
        self.task_queue: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.ministries = None  # 六部实例，由 CentralGovernment 注入
        
    def set_ministries(self, ministries: Dict[str, any]):
        """注入六部实例"""
        self.ministries = ministries
    
    def dispatch(self, edict: Edict) -> List[Task]:
        """
        分发诏书为任务
        
        根据诏书类型，分配给对应部门：
        - 货币政策 → 户部 + 兵部（执行）
        - 财政政策 → 户部（税收/支出）
        - 市场干预 → 兵部（平准基金）
        - 人事管理 → 吏部
        - 司法 → 刑部
        - 基建 → 工部
        """
        tasks = []
        
        if edict.edict_type.value == "monetary":
            tasks.append(self._create_monetary_task(edict))
            tasks.append(self._create_liquidity_task(edict))
            
        elif edict.edict_type.value == "fiscal":
            tasks.append(self._create_tax_task(edict))
            tasks.append(self._create_spending_task(edict))
            
        elif edict.edict_type.value == "intervene":
            tasks.append(self._create_stabilization_task(edict))
            tasks.append(self._create_surveillance_task(edict))
            
        elif edict.edict_type.value == "agent_manage":
            tasks.append(self._create_audit_task(edict))
            
        # 标记诏书为已分发
        edict.status = EdictStatus.DISPATCHED
        edict.tasks = [t.task_id for t in tasks]
        
        return tasks
    
    def _create_monetary_task(self, edict: Edict) -> Task:
        """创建货币政策执行任务"""
        return Task(
            task_id=f"MON_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="adjust_interest_rates",
            params={
                "rate_delta": edict.content.get("rate_change", "0%"),
                "effective_immediately": True
            },
            assigned_to="finance_ministry",
            priority=4
        )
    
    def _create_liquidity_task(self, edict: Edict) -> Task:
        """流动性调节任务"""
        return Task(
            task_id=f"LIQ_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="inject_liquidity",
            params={
                "amount": 1e6,  # 100万
                "target": "all_markets"
            },
            assigned_to="military_ministry",
            priority=3
        )
    
    def _create_tax_task(self, edict: Edict) -> Task:
        """税收任务"""
        tax_increase = edict.content.get("tax_increase", "0%")
        return Task(
            task_id=f"TAX_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="adjust_tax_rates",
            params={
                "increase_pct": tax_increase,
                "applicable_agents": "all_trading_agents"
            },
            assigned_to="finance_ministry",
            priority=4
        )
    
    def _create_spending_task(self, edict: Edict) -> Task:
        """财政支出任务"""
        spending_cut = edict.content.get("spending_cut", "0%")
        return Task(
            task_id=f"SPEND_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="adjust_budget",
            params={
                "cut_pct": spending_cut,
                "exemptions": edict.content.get("exemptions", [])
            },
            assigned_to="finance_ministry",
            priority=3
        )
    
    def _create_stabilization_task(self, edict: Edict) -> Task:
        """市场稳定任务（兵部平准）"""
        violations = edict.content.get("violations", {})
        return Task(
            task_id=f"STAB_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="market_stabilization",
            params={
                "target_markets": list(violations.keys()),
                "intervention_type": "liquidity_injection",
                "amount_per_market": 5e5
            },
            assigned_to="military_ministry",
            priority=5  # 最高优先级
        )
    
    def _create_surveillance_task(self, edict: Edict) -> Task:
        """加强监控任务"""
        return Task(
            task_id=f"SURV_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="increase_surveillance",
            params={
                "monitoring_interval": "1 tick",
                "alert_threshold": "low"
            },
            assigned_to="justice_ministry",
            priority=2
        )
    
    def _create_audit_task(self, edict: Edict) -> Task:
        """绩效审计任务（吏部）"""
        return Task(
            task_id=f"AUDIT_TASK_{edict.edict_id[-8:]}",
            edict_id=edict.edict_id,
            action="performance_audit",
            params={
                "period": "100 ticks",
                "metrics": ["total_pnl", "sharpe_ratio", "max_drawdown"]
            },
            assigned_to="personnel_ministry",
            priority=2
        )
    
    def execute_task(self, task: Task) -> Dict:
        """
        执行单个任务（由尚书省执行引擎调用）
        
        实际执行时，会将任务分派给对应部门的 Agent
        """
        if task.status != "pending":
            return {"status": "skipped", "reason": "already processed"}
        
        # 标记为执行中
        task.status = "running"
        
        # 根据 assigned_to 调用对应部门
        ministry_name = task.assigned_to.replace("_ministry", "")
        if self.ministries and ministry_name in self.ministries:
            ministry = self.ministries[ministry_name]
            # 调用部门的 execute_task 方法（需各部位实现）
            if hasattr(ministry, "execute_task"):
                result = ministry.execute_task(task)
            else:
                result = {"status": "completed", "note": f"{ministry_name} processed"}
        else:
            result = {"status": "completed", "note": "default execution"}
        
        task.status = "completed" if result.get("status") == "completed" else "failed"
        self.completed_tasks.append(task)
        
        return result
    
    def get_pending_tasks(self, priority: Optional[int] = None) -> List[Task]:
        """获取待执行任务（可筛选优先级）"""
        tasks = [t for t in self.task_queue.values() if t.status == "pending"]
        if priority:
            tasks = [t for t in tasks if t.priority >= priority]
        return sorted(tasks, key=lambda t: -t.priority)
    
    def get_status(self) -> Dict:
        return {
            "tasks_total": len(self.task_queue),
            "tasks_pending": sum(1 for t in self.task_queue.values() if t.status == "pending"),
            "tasks_completed": len(self.completed_tasks),
            "high_priority_pending": len([t for t in self.task_queue.values() if t.priority >= 4 and t.status == "pending"])
        }


__all__ = ["DepartmentOfWorks"]
