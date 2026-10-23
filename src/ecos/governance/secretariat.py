"""中书省 (Secretariat) - 策略生成部门
"""

from typing import Dict, List, Optional
from datetime import datetime
import random
from ..core.event_bus import EventBus
from .types import Edict, EdictType, EdictStatus


class Secretariat:
    """
    中书省 - 皇帝的政策顾问团
    
    职责:
    1. 接收 Analysts 的分析报告
    2. 结合 MacroAgent 的宏观判断
    3. 生成经济政策诏书（货币政策、财政政策）
    4. 发布市场干预指令
    
    权力:
    - 起草所有国家法令
    - 提名尚书省长官
    - 建议六部工作重点
    """
    
    def __init__(self, world, agents, event_bus: EventBus):
        self.world = world
        self.agents = agents
        self.event_bus = event_bus
        self.policy_db = []   # 政策历史
        
    def draft_edicts(self, analysis_report: Dict, tick: int) -> List[Edict]:
        edicts = []
        
        # 1. 货币政策（每 tick 根据周期）
        macro = analysis_report.get("macro_cycle", {})
        cycle = macro.get("current_cycle", "expansion")
        
        if cycle == "overheat":
            edicts.append(self._create_monetary_tightening(cycle))
        elif cycle == "recession":
            edicts.append(self._create_monetary_easing(cycle))
        else:
            # 其他周期也生成中性政策
            edicts.append(Edict(
                edict_id=f"MON_{tick:04d}",
                edict_type=EdictType.MONETARY_POLICY,
                title=f"货币政策维持 - {cycle}",
                content={"status": "unchanged", "rate": "5.0%"},
                issuer="中书省"
            ))
        
        # 2. 财政政策（每 20 ticks）
        if tick % 20 == 0:
            treasury = analysis_report.get("treasury", 1e6)
            if treasury < 5e5:
                edicts.append(self._create_fiscal_austerity())
            elif treasury > 2e6:
                edicts.append(self._create_fiscal_stimulus())
            else:
                edicts.append(Edict(
                    edict_id=f"FIS_{tick:04d}",
                    edict_type=EdictType.FISCAL_POLICY,
                    title="财政预算执行",
                    content={"status": "normal", "deficit": "0%"},
                    issuer="中书省"
                ))
        
        # 3. 市场监控（每 tick 都检查）
        violations = analysis_report.get("violations", {})
        total_violations = sum(violations.values())
        if total_violations > 50:
            edicts.append(self._create_market_intervention(violations))
        
        # 4. 人事管理（每 50 ticks）
        if tick % 50 == 0:
            edicts.append(self._create_performance_review())
        
        return edicts
    
    def _create_monetary_tightening(self, cycle: str) -> Edict:
        """紧缩货币政策"""
        return Edict(
            edict_id=f"MON_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.MONETARY_POLICY,
            title=f"紧缩货币政策 - {cycle}期",
            content={
                "rate_change": "+0.25%",          # 加息 25bp
                "reserve_ratio": "+0.5%",          # 提高准备金率
                "expected_impact": "减少流动性，抑制通胀",
                "duration": "until inflation < 3%"
            },
            issuer="中书省 (Secretariat)"
        )
    
    def _create_monetary_easing(self, cycle: str) -> Edict:
        """宽松货币政策"""
        return Edict(
            edict_id=f"EASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.MONETARY_POLICY,
            title=f"宽松货币政策 - {cycle}期",
            content={
                "rate_change": "-0.25%",          # 降息 25bp
                "reserve_ratio": "-0.5%",          # 降低准备金率
                "expected_impact": "增加流动性，刺激经济",
                "duration": "until GDP growth > 3%"
            },
            issuer="中书省 (Secretariat)"
        )
    
    def _create_fiscal_austerity(self) -> Edict:
        """财政紧缩"""
        return Edict(
            edict_id=f"AUST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.FISCAL_POLICY,
            title="财政紧缩令",
            content={
                "tax_increase": "5%",            # 增税 5%
                "spending_cut": "10%",           # 削减支出 10%
                "exemptions": ["基础设施", "国防"],
                "reason": "国库不足，需控制赤字"
            },
            issuer="中书省 (Secretariat)"
        )
    
    def _create_fiscal_stimulus(self) -> Edict:
        """财政刺激"""
        return Edict(
            edict_id=f"STIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.FISCAL_POLICY,
            title="财政刺激计划",
            content={
                "tax_cut": "10%",               # 减税 10%
                "spending_increase": "20%",     # 增加支出 20%
                "target_sectors": ["科技", "基建", "绿色能源"],
                "funding": "发行国债"
            },
            issuer="中书省 (Secretariat)"
        )
    
    def _create_market_intervention(self, violations: Dict) -> Edict:
        """市场干预诏书"""
        return Edict(
            edict_id=f"INT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.MARKET_INTERVENE,
            title="市场干预令",
            content={
                "violations": violations,
                "actions": [
                    "兵部平准基金入场",
                    "暂停违规 Agent 交易权限",
                    "增加市场流动性"
                ],
                "duration": "10 ticks"
            },
            issuer="中书省 (Secretariat) - 紧急"
        )
    
    def _create_performance_review(self) -> Edict:
        """Agent 绩效审查诏书"""
        return Edict(
            edict_id=f"REV_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            edict_type=EdictType.AGENT_MANAGE,
            title="Agent 绩效评估令",
            content={
                "review_period": "100 ticks",
                "action": "吏部执行考核",
                "metrics": ["PnL", "Sharpe", "最大回撤", "合规记录"]
            },
            issuer="中书省 (Secretariat)"
        )


# 测试
if __name__ == "__main__":
    import json
    world = None  # placeholder
    agents = []
    from ecos.core.event_bus import EventBus
    eb = EventBus()
    
    secretariat = Secretariat(world, agents, eb)
    
    # 模拟分析报告
    report = {
        "macro_cycle": {"current_cycle": "过热"},
        "treasury": 4e5,
        "violations": {"BTC": 50, "ETH": 45, "XMR": 30},
    }
    
    edicts = secretariat.draft_edicts(report, tick=100)
    print(f"Drafted {len(edicts)} edicts:")
    for e in edicts:
        print(f"  [{e.edict_type.value}] {e.title}")
        print(f"    Content: {e.content}")
