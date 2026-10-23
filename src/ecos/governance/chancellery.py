"""门下省 (Chancellery) - 风险审查与诏书否决
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
from .types import Edict, EdictType, EdictStatus


class Chancellery:
    """
    门下省 - 门下侍中（副宰相）领导
    
    职责:
    1. 审查中书省诏书的合规性与风险
    2. 行使否决权（封驳）
    3. 向皇帝提供修正建议
    
    审查维度:
    - 财政风险（成本过高）
    - 市场风险（引发剧烈波动）
    - 合规风险（违反现有法律）
    - 政治风险（社会影响）
    """
    
    def __init__(self, world, risk_agents: List):
        self.world = world
        self.risk_agents = risk_agents
        self.veto_count = 0
        self.approved_count = 0
        self.veto_history = []
    
    def review_edict(self, edict: Edict) -> Tuple[bool, str]:
        passed, reason = True, "无异议"
        
        if edict.edict_type == EdictType.MONETARY_POLICY:
            passed, reason = self._review_monetary(edict)
        elif edict.edict_type == EdictType.FISCAL_POLICY:
            passed, reason = self._review_fiscal(edict)
        elif edict.edict_type == EdictType.MARKET_INTERVENE:
            passed, reason = self._review_intervention(edict)
        elif edict.edict_type == EdictType.AGENT_MANAGE:
            passed, reason = self._review_personnel(edict)
        
        # 更新状态
        if passed:
            edict.status = EdictStatus.REVIEW_PASSED
            edict.reviewer_votes.append("passed")
        else:
            edict.status = EdictStatus.VETOED
            edict.veto_reason = reason
            edict.reviewer_votes.append("veto")
        
        return passed, reason
    
    def _review_monetary(self, edict: Edict) -> Tuple[bool, str]:
        """审查货币政策"""
        content = edict.content
        rate_change = content.get("rate_change", "0%")
        
        # 风险检查
        risks = []
        
        # 1. 通胀检查
        # TODO: 从 world 获取当前通胀
        inflation = 0.03  # 假设 3%
        if "+" in rate_change and inflation > 0.05:
            risks.append(f"通胀已 {inflation*100:.1f}%，加息可能加剧经济衰退")
        
        # 2. 流动性检查
        # TODO: 检查市场流动性
        
        # 3. 随机否决（模拟门下省的保守倾向）
        if random.random() < 0.1:  # 10% 概率否决
            self.veto_count += 1
            return False, f"门下省封驳：政策过于激进，建议缓行"
        
        self.approved_count += 1
        return True, "审查通过"
    
    def _review_fiscal(self, edict: Edict) -> Tuple[bool, str]:
        """审查财政政策"""
        content = edict.content
        
        # 检查赤字
        spending = content.get("spending_increase", "0%")
        if "%" in spending:
            increase = float(spending.strip("%")) / 100
            if increase > 0.15:
                return False, f"支出增加 {increase*100:.0f}% 过高，可能导致财政危机"
        
        return True, "审查通过"
    
    def _review_intervention(self, edict: Edict) -> Tuple[bool, str]:
        """审查市场干预"""
        # 市场干预需要更高的审查标准
        if random.random() < 0.3:  # 30% 概率否决（防止滥用干预）
            return False, "门下省认为当前市场波动在正常范围，无需干预"
        return True, "干预合理"
    
    def _review_personnel(self, edict: Edict) -> Tuple[bool, str]:
        """审查人事诏书"""
        # 吏部事务通常通过
        return True, "人事审查通过"
    
    def collective_veto(self, edict: Edict, votes: List[str]) -> bool:
        """
        集体否决机制
        
        Args:
            edict: 诏书
            votes: 门下省官员投票 ["approve", "veto", ...]
            
        Returns:
            True if vetoed by majority
        """
        veto_count = sum(1 for v in votes if v == "veto")
        if veto_count / len(votes) > 0.5:
            edict.status = EdictStatus.VETOED
            edict.veto_reason = "多数官员反对"
            self.veto_history.append({
                "edict_id": edict.edict_id,
                "timestamp": datetime.now().isoformat(),
                "votes": votes
            })
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {
            "edicts_reviewed": self.approved_count + self.veto_count,
            "approved": self.approved_count,
            "vetoed": self.veto_count,
            "veto_rate": self.veto_count / max(1, (self.approved_count + self.veto_count))
        }


__all__ = ["Chancellery"]
