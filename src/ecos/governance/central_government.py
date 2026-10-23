"""ECOS Governance Layer - 三省六部架构
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


from .types import Edict, Task, EdictType, EdictStatus


class CentralGovernment:
    """
    中央政府核心协调器
    
    三权分立：
    1. 中书省 (Secretariat) - 起草诏书
    2. 门下省 (Chancellery) - 审查封驳
    3. 尚书省 (DepartmentOfWorks) - 执行诏书
    
    六部归尚书省管辖：
    - 吏部 (Personnel)   - 人事
    - 户部 (Finance)     - 财政
    - 礼部 (Ritual)      - 舆情
    - 兵部 (Military)    - 市场干预
    - 刑部 (Justice)     - 司法
    - 工部 (Works)       - 基建
    """
    
    def __init__(self, name: str = "ECOS Central Government"):
        self.name = name
        self.secretariat = None
        self.chancellery = None
        self.department_of_works = None
        self.ministries = {}
        self.edicts: Dict[str, Edict] = {}
        self.task_queue: Dict[str, Task] = {}
        self.tick_counter = 0
        
    def setup(self, world, agents, event_bus):
        """初始化三省六部"""
        from .secretariat import Secretariat
        from .chancellery import Chancellery
        from .department_ofworks import DepartmentOfWorks
        from .ministries import (
            PersonnelMinistry, FinanceMinistry, RitualMinistry,
            MilitaryMinistry, JusticeMinistry, WorksMinistry
        )
        
        self.secretariat = Secretariat(world=world, agents=agents, event_bus=event_bus)
        self.chancellery = Chancellery(world=world, risk_agents=[a for a in agents if a.__class__.__name__=="RiskAgent"])
        self.department_of_works = DepartmentOfWorks(world=world, agents=agents, event_bus=event_bus)
        
        self.ministries = {
            "personnel": PersonnelMinistry(agents),
            "finance": FinanceMinistry(initial_treasury=1e6, agents=agents),
            "ritual": RitualMinistry(),
            "military": MilitaryMinistry(world),
            "justice": JusticeMinistry(),
            "works": WorksMinistry(world),
        }
        
        self.department_of_works.set_ministries(self.ministries)
        logger.info(f"[{self.name}] Central Government established")
    
    def on_tick(self, tick: int, analysis_report: Dict):
        """每 tick 政府运作流程（上朝）"""
        self.tick_counter = tick
        
        # 每 10 ticks 上朝一次
        if tick % 10 != 0:
            return
        
        logger.info(f"\n{'='*60}")
        logger.info(f"  Emperor's Court - Tick {tick}")
        logger.info(f"{'='*60}")
        
        # Step 1: 中书省拟诏
        draft_edicts = self.secretariat.draft_edicts(analysis_report, tick)
        # 归档草案
        for e in draft_edicts:
            self.edicts[e.edict_id] = e
        logger.info(f"[中书省] Drafted {len(draft_edicts)} edicts")
        
        # Step 2: 门下省审议
        passed_edicts = []
        for edict in draft_edicts:
            passed, reason = self.chancellery.review_edict(edict)
            if passed:
                passed_edicts.append(edict)
                logger.info(f"  [通过] {edict.title}")
            else:
                logger.info(f"  [驳回] {edict.title}: {reason}")
        
        # Step 3: 尚书省执行
        for edict in passed_edicts:
            tasks = self.department_of_works.dispatch(edict)
            self.task_queue.update({t.task_id: t for t in tasks})
            logger.info(f"  [执行] {edict.title} -> {len(tasks)} tasks")
        
        # Step 4: 六部日常工作
        self._run_ministries(tick)
    
    def _run_ministries(self, tick: int):
        """六部日常工作"""
        # 吏部：每 50 ticks 考核
        if tick % 50 == 0:
            fires, hires = self.ministries["personnel"].audit()
            if fires or hires:
                logger.info(f"  [吏部] Fired {len(fires)}, Hired {len(hires)}")
        
        # 户部：税收
        tax_revenue = self.ministries["finance"].collect_taxes()
        if tax_revenue > 0:
            logger.info(f"  [户部] Tax revenue: {tax_revenue:,.0f}")
        
        # 兵部：市场稳定
        if tick % 100 == 0:
            intervention = self.ministries["military"].stabilize_market()
            if intervention:
                logger.info(f"  [兵部] Market intervention: {intervention}")
        
        # 刑部：违规处理
        violations = self.ministries["justice"].review_cases()
        if violations:
            logger.info(f"  [刑部] Processed {len(violations)} violations")
        
        # 工部：基建进度
        self.ministries["works"].update_projects(tick)
    
    def get_status(self) -> Dict:
        return {
            "edicts_total": len(self.edicts),
            "tasks_pending": sum(1 for t in self.task_queue.values() if t.status == "pending"),
            "treasury": self.ministries["finance"].treasury if "finance" in self.ministries else 0,
        }


__all__ = ["CentralGovernment", "Edict", "Task", "EdictType", "EdictStatus"]
