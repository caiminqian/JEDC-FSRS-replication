"""礼部 (Ritual Ministry) - 舆情、宣传、仪式
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random


@dataclass
class PublicEvent:
    """公共事件"""
    event_id: str
    title: str
    category: str  # "ceremony", "campaign", "crisis"
    start_tick: int
    duration: int = 10
    impact: Dict[str, float] = field(default_factory=dict)  # 对不同 Agent 类型的影响
    description: str = ""


class RitualMinistry:
    """
    礼部 - 礼宾司
    
    职责:
    1. 组织国家庆典、仪式（提振信心）
    2. 宣传运动（引导舆论）
    3. 危机公关（应对负面事件）
    4. 发布官方声明
    5. 管理 Agent 声誉
    
    影响力:
    - 庆典 → 提升所有 Agent 风险偏好 (+0.2)
    - 宣传 → 引导资金流向特定市场
    - 危机 → 引发恐慌（HumanAgent FOMO 加剧）
    """
    
    def __init__(self):
        self.active_events: Dict[str, PublicEvent] = {}
        self.news_feed = []  # 官方新闻
        self.sentiment_index = 0.0  # 整体情绪指数 [-1, 1]
        self.event_counter = 0
        
    def schedule_ceremony(self, title: str, duration: int = 10) -> str:
        """
        安排庆典
        
        Returns:
            event_id
        """
        event_id = f"CER_{self.event_counter:04d}"
        self.event_counter += 1
        
        event = PublicEvent(
            event_id=event_id,
            title=title,
            category="ceremony",
            start_tick=0,  # 立即开始
            duration=duration,
            impact={
                "RetailAgent": 0.3,    # 散户情绪高涨
                "InstitutionAgent": 0.1,
                "MarketMakerAgent": 0.0,
                "RiskAgent": -0.1,      # 风险厌恶降低
                "MacroAgent": 0.1,
            },
            description=f"国家庆典: {title} - 提振经济信心"
        )
        self.active_events[event_id] = event
        self._broadcast_news(f"[礼部] 举办庆典: {title}")
        return event_id
    
    def launch_campaign(self, target_sector: str, message: str) -> str:
        """
        发起宣传运动
        
        Args:
            target_sector: 目标领域（如 "BTC", "科技"）
            message: 宣传口号
            
        Returns:
            campaign_id
        """
        campaign_id = f"CAMP_{self.event_counter:04d}"
        self.event_counter += 1
        
        event = PublicEvent(
            event_id=campaign_id,
            title=f"宣传: {target_sector}",
            category="campaign",
            start_tick=0,
            duration=20,
            impact={
                "RetailAgent": 0.5,    # 强烈引导散户
                "AnalystAgent": -0.2,  # 分析员保持独立
            },
            description=message
        )
        self.active_events[campaign_id] = event
        self._broadcast_news(f"[礼部] 宣传运动: {message}")
        return campaign_id
    
    def handle_crisis(self, crisis_type: str, severity: float) -> str:
        """
        危机公关
        
        Args:
            crisis_type: "market_crash", "scandal", "regulation_violation"
            severity: 严重程度 0-1
            
        Returns:
            crisis_id
        """
        crisis_id = f"CRISIS_{self.event_counter:04d}"
        self.event_counter += 1
        
        # 危机影响：降低市场情绪
        impact = {
            "RetailAgent": -0.5 * severity,
            "HumanAgent": -0.7 * severity,  # 人类恐慌更严重
            "MarketMakerAgent": -0.2 * severity,
        }
        
        event = PublicEvent(
            event_id=crisis_id,
            title=f"危机: {crisis_type}",
            category="crisis",
            start_tick=0,
            duration=5,
            impact=impact,
            description=f"紧急事件: {crisis_type}，相关部门正在处理"
        )
        self.active_events[crisis_id] = event
        self._broadcast_news(f"[礼部] 危机应对: {crisis_type}")
        
        return crisis_id
    
    def _broadcast_news(self, message: str):
        """发布官方新闻"""
        self.news_feed.append({
            "timestamp": datetime.now().isoformat(),
            "source": "礼部",
            "message": message
        })
        # 发布到 Event Bus
        # self.event_bus.publish("official_news", message)
    
    def update(self, current_tick: int):
        """每 tick 更新事件状态"""
        expired = []
        for event_id, event in self.active_events.items():
            if current_tick - event.start_tick >= event.duration:
                expired.append(event_id)
        
        for event_id in expired:
            del self.active_events[event_id]
            print(f"  [礼部] 事件结束: {self.active_events[event_id].title}")
    
    def get_current_sentiment_modifier(self, agent_type: str) -> float:
        """
        获取当前对某类 Agent 的情绪修正系数
        
        Returns:
            修正值 [-1, 1]，加到 Agent 的情绪/决策权重上
        """
        total_impact = 0.0
        for event in self.active_events.values():
            total_impact += event.impact.get(agent_type, 0.0)
        return total_impact
    
    def get_status(self) -> Dict:
        return {
            "active_events": len(self.active_events),
            "sentiment_index": self.sentiment_index,
            "news_count": len(self.news_feed),
            "recent_news": self.news_feed[-5:] if self.news_feed else []
        }


__all__ = ["RitualMinistry", "PublicEvent"]
