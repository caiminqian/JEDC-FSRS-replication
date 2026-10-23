"""ECOS Governance Layer - 共享数据类型 (依赖无关，避免循环导入)

本模块只定义纯数据结构 (Enum / dataclass)，不依赖 governance 包内其他子模块，
供 central_government / secretariat / chancellery / department_ofworks 共享使用。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EdictType(Enum):
    """诏书类型"""
    MONETARY_POLICY = "monetary"
    FISCAL_POLICY = "fiscal"
    TRADE_ORDER = "trade_order"
    AGENT_MANAGE = "agent_manage"
    MARKET_INTERVENE = "intervene"
    TAXATION = "taxation"


class EdictStatus(Enum):
    """诏书状态"""
    DRAFT = "draft"
    REVIEW_PASSED = "reviewed"
    VETOED = "vetoed"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Edict:
    """诏书 - 三省六部的决策输出"""
    edict_id: str
    edict_type: EdictType
    title: str
    content: Dict
    issuer: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: EdictStatus = EdictStatus.DRAFT
    reviewer_votes: List[str] = field(default_factory=list)
    veto_reason: Optional[str] = None
    tasks: List[str] = field(default_factory=list)


@dataclass
class Task:
    """执行任务"""
    task_id: str
    edict_id: str
    action: str
    params: Dict
    assigned_to: str
    priority: int = 1
    due_tick: Optional[int] = None
    status: str = "pending"


__all__ = ["EdictType", "EdictStatus", "Edict", "Task"]
