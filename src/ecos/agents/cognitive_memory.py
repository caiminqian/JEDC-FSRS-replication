"""EE 经济记忆引擎 - 将人类认知衰退模型注入经济智能体

参考: SuperMemo EE algorithm (https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-of-work)
核心公式: R = exp(-t / S)
  - R: Retrievability (可提取率/记忆清晰度) [0, 1]
  - t: time since last repetition (自上次复习的天数)
  - S: Stability (记忆稳定性/抗遗忘能力, 单位: 天)

经济学映射:
  - "记忆卡片" → "市场教训" (如: "高杠杆危险")
  - R (可提取率) → Risk Awareness (风险警惕性)
  - S (稳定性) → Institutionalization (制度化深度)
  - Repetition (复习) → Market Shock (市场冲击/回撤)

关键洞察:
  - 长期牛市 → R 指数衰退 → Agent 风险警惕性下降 → 杠杆率飙升 → 危机
  - 市场崩盘 → 强制复习 → R 瞬间恢复 + S 增长 → 系统重置
"""

import math
from typing import Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class EconomicMemory:
    """EE 经济记忆单元
    
    每个单元对应一个"市场教训"或"风险策略"
    例如: "避免高杠杆交易"、"警惕流动性枯竭"、"不要追涨杀跌"
    """
    lesson_id: str
    lesson_name: str
    S: float = 45.0  # 稳定性 (days) - 校准后 (5-event grid: S_initial=45)
    last_shock_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    difficulty: float = 5.0  # 学习难度 (D) - 越难掌握的教训，S 增长越快
    category: str = "risk"  # 类别: risk, strategy, regulation
    
    # SM-2 参数
    EF: float = 2.5  # E-Factor (项目难度/易学性，初始 2.5)
    interval_days: int = 0  # 下次复习间隔（天）
    repetition_count: int = 0  # 已复习次数
    last_quality: int = -1  # 上次学习质量评分
    
    # 内部状态
    _initial_S: float = field(default=10.0, init=False, repr=False)
    
    def get_retrievability(self, current_time: Optional[datetime] = None) -> float:
        """
        计算当前可提取率 R (风险警惕性)
        
        Args:
            current_time: 当前时间 (默认: datetime.now(timezone.utc))
            
        Returns:
            R ∈ [0, 1]: 1.0 = 记忆犹新, 0.0 = 完全遗忘
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        t = (current_time - self.last_shock_time).total_seconds() / 86400  # 转换为天数
        
        if t <= 0:
            return 1.0
        
        # EE 核心衰减函数: R = exp(-t / S)
        # 解释: S 越大，衰减越慢；t 越大，R 越小
        R = math.exp(-t / self.S)
        return max(0.0, min(1.0, R))
    
    def process_market_shock(self, shock_time: Optional[datetime] = None, 
                            severity: float = 1.0, 
                            quality: int = 5) -> Dict[str, float]:
        """
        处理市场冲击（复习事件） + SM-2 质量评分
        
        当市场发生暴跌/黑天鹅时，触发记忆巩固机制:
        1. R 瞬间恢复至 100% (last_shock_time 更新)
        2. S 获得指数级增长 (EE: 越在快忘记时复习，S 提升越大)
        3. 根据学习质量 q (0-5) 调整 EF (E-Factor)
        4. difficulty 下降（教训已内化）
        
        Args:
            shock_time: 冲击发生时间
            severity: 冲击烈度 [0, 1]
            quality: 学习质量评分 q ∈ {0,1,2,3,4,5} (5=完美掌握, 0=完全遗忘)
            
        Returns:
            Dict with new_S, new_EF, consolidation_factor, quality
        """
        if shock_time is None:
            shock_time = datetime.now(timezone.utc)
        
        current_R = self.get_retrievability(shock_time)
        
        # --- EE: S 增长 ---
        forgetting_degree = 1.0 - current_R
        difficulty_factor = max(0.5, self.difficulty / 5.0)
        consolidation_factor = 1.0 + forgetting_degree * severity * difficulty_factor
        new_S = self.S * consolidation_factor
        
        # --- SM-2: EF 调整 ---
        # EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
        # q 越高，EF 减小（项目变易学）；q 越低，EF 增加（项目变难）
        old_EF = self.EF
        delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_EF = max(1.3, self.EF + delta)  # EF 最小 1.3
        
        # 更新难度
        new_difficulty = max(1.0, self.difficulty - severity * 0.5 * (quality / 5.0))
        
        # 更新状态
        self.S = new_S
        self.EF = new_EF
        self.last_shock_time = shock_time
        self.difficulty = new_difficulty
        self.repetition_count += 1
        self.last_quality = quality
        
        # 计算下次复习间隔（SM-2 公式）
        if self.repetition_count == 1:
            self.interval_days = 1
        elif self.repetition_count == 2:
            self.interval_days = 6
        else:
            # I(n) = I(n-1) * EF，向上取整
            self.interval_days = max(1, int(self.interval_days * self.EF + 0.5))
        
        return {
            "previous_S": self.S / consolidation_factor if consolidation_factor > 1 else self.S,
            "new_S": new_S,
            "new_EF": new_EF,
            "consolidation_factor": consolidation_factor,
            "new_difficulty": new_difficulty,
            "R_after_shock": 1.0,
            "repetition_count": self.repetition_count,
            "next_interval_days": self.interval_days,
            "quality": quality
        }
    
    def estimate_time_to_forget(self, threshold_R: float = 0.5) -> int:
        """
        估计记忆衰减到阈值所需天数
        
        用于宏观监控: 如果全市场平均 R 在 50% 以下，预警风险
        """
        if self.get_retrievability() < threshold_R:
            return 0  # 已经低于阈值
        
        # 解方程: threshold_R = exp(-t / S)
        # → t = -S * ln(threshold_R)
        t_days = -self.S * math.log(threshold_R)
        return max(0, int(t_days))
    
    def to_dict(self) -> Dict:
        """序列化（用于持久化）"""
        return {
            "lesson_id": self.lesson_id,
            "lesson_name": self.lesson_name,
            "S": self.S,
            "last_shock_time": self.last_shock_time.isoformat(),
            "difficulty": self.difficulty,
            "category": self.category,
            "initial_S": self._initial_S,
            "EF": self.EF,
            "interval_days": self.interval_days,
            "repetition_count": self.repetition_count,
            "last_quality": self.last_quality
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EconomicMemory":
        """反序列化"""
        obj = cls(
            lesson_id=data["lesson_id"],
            lesson_name=data["lesson_name"],
            S=data["S"],
            difficulty=data.get("difficulty", 5.0),
            category=data.get("category", "risk")
        )
        obj.last_shock_time = datetime.fromisoformat(data["last_shock_time"])
        obj._initial_S = data.get("initial_S", data["S"])
        obj.EF = data.get("EF", 2.5)
        obj.interval_days = data.get("interval_days", 0)
        obj.repetition_count = data.get("repetition_count", 0)
        obj.last_quality = data.get("last_quality", -1)
        return obj


class CognitiveMemoryBank:
    """Agent 的认知记忆银行 - 管理多个 EconomicMemory 单元
    
    每个 Agent 拥有一个记忆银行，包含多个"市场教训"记忆单元。
    例如:
      - memory_01: "2008 年金融危机教训" (S=50, 极高稳定性)
      - memory_02: "2020 年疫情回调" (S=15, 中等)
      - memory_03: "上周的小波动" (S=2, 极易遗忘)
    """
    
    # 预定义的核心市场教训模板（S 已校准至 45.0）
    LESSONS = {
        "leverage_risk": {
            "name": "高杠杆导致爆仓",
            "category": "risk",
            "initial_S": 45.0,
            "difficulty": 6.0
        },
        "liquidity_crisis": {
            "name": "流动性枯竭无法退出",
            "category": "risk",
            "initial_S": 45.0,
            "difficulty": 7.0
        },
        "bull_market_complacency": {
            "name": "长期牛市导致过度自信",
            "category": "strategy",
            "initial_S": 45.0,
            "difficulty": 5.0
        },
        "panic_selling": {
            "name": "恐慌性抛售在地板价",
            "category": "behavior",
            "initial_S": 45.0,
            "difficulty": 4.5
        },
        "regulation_change": {
            "name": "政策突变风险",
            "category": "regulation",
            "initial_S": 45.0,
            "difficulty": 8.0  # 政策教训很难忘记
        }
    }
    
    def __init__(self, agent_id: str, initial_lessons: List[str] = None):
        """
        初始化记忆银行
        
        Args:
            agent_id: Agent 唯一标识
            initial_lessons: 初始加载的教训列表 (key 来自 LESSONS)
        """
        self.agent_id = agent_id
        self.memories: Dict[str, EconomicMemory] = {}
        
        # 默认加载核心风险教训
        default_lessons = ["leverage_risk", "liquidity_crisis", "bull_market_complacency"]
        lessons_to_load = initial_lessons or default_lessons
        
        for lesson_key in lessons_to_load:
            if lesson_key in self.LESSONS:
                template = self.LESSONS[lesson_key]
                memory = EconomicMemory(
                    lesson_id=lesson_key,
                    lesson_name=template["name"],
                    S=template["initial_S"],
                    difficulty=template["difficulty"],
                    category=template["category"]
                )
                self.memories[lesson_key] = memory
    
    def get_risk_awareness(self, current_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        计算当前综合风险警惕性
        
        返回:
            {
                "overall_R": 加权平均警惕性,
                "by_category": {category: avg_R},
                "critical_lessons": {lesson: R}  # R < 0.3 的严重警告
            }
        """
        if not self.memories:
            return {"overall_R": 0.5, "by_category": {}, "critical_lessons": {}}
        
        Rs = {}
        by_category = {}
        critical = {}
        
        for lesson_key, memory in self.memories.items():
            R = memory.get_retrievability(current_time)
            Rs[lesson_key] = R
            
            cat = memory.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(R)
            
            # 严重警告: R < 0.3 (记忆严重衰退)
            if R < 0.3:
                critical[lesson_key] = R
        
        # 计算加权平均 R
        # 权重: 稳定性 S 越高的记忆，权重越大（越重要）
        total_weight = sum(m.S for m in self.memories.values())
        overall_R = sum(Rs[k] * self.memories[k].S for k in Rs) / total_weight if total_weight > 0 else 0.5
        
        # 按类别平均
        avg_by_category = {cat: sum(vals)/len(vals) for cat, vals in by_category.items()}
        
        return {
            "overall_R": overall_R,
            "by_category": avg_by_category,
            "critical_lessons": critical
        }
    
    def process_shock(self, shock_time: Optional[datetime] = None, severity: float = 1.0,
                      categories: Optional[List[str]] = None, quality: int = 5) -> Dict:
        """
        市场冲击触发集体记忆复习
        
        Args:
            shock_time: 冲击时间
            severity: 烈度 [0, 1]
            categories: 受影响的记忆类别 (None = 全部)
            
        Returns:
            {total_consolidation, affected_memories, new_avg_S}
        """
        if shock_time is None:
            shock_time = datetime.now(timezone.utc)
        
        affected = {}
        total_S_before = sum(m.S for m in self.memories.values())
        count = 0
        
        for lesson_key, memory in self.memories.items():
            if categories and memory.category not in categories:
                continue
            
            result = memory.process_market_shock(shock_time, severity, quality)
            affected[lesson_key] = result
            count += 1
        
        total_S_after = sum(m.S for m in self.memories.values())
        
        return {
            "shock_severity": severity,
            "affected_memories": count,
            "total_S_change": total_S_after - total_S_before,
            "avg_S_before": total_S_before / len(self.memories) if self.memories else 0,
            "avg_S_after": total_S_after / len(self.memories) if self.memories else 0,
            "quality": quality,  # 本次复习的质量评分
        }
    
    def add_lesson(self, lesson_key: str, name: str, category: str = "custom",
                   initial_S: float = 5.0, difficulty: float = 5.0) -> EconomicMemory:
        """添加新的教训记忆"""
        if lesson_key in self.memories:
            return self.memories[lesson_key]
        
        memory = EconomicMemory(
            lesson_id=lesson_key,
            lesson_name=name,
            S=initial_S,
            difficulty=difficulty,
            category=category
        )
        self.memories[lesson_key] = memory
        return memory
    
    def get_behavioral_bias(self, current_time: Optional[datetime] = None) -> Dict[str, float]:
        """
        根据记忆状态，推导出行为偏差倾向
        
        返回: {greedy_index, fear_index, leverage_tendency, ...}
        """
        awareness = self.get_risk_awareness(current_time)
        overall_R = awareness["overall_R"]
        
        # 杠杆倾向: R 越低，越倾向于高杠杆 (1x → 10x)
        leverage_tendency = 1.0 + (1.0 - overall_R) * 9.0
        
        # 贪婪指数: 记忆衰退 → 贪婪
        greed_index = max(0, 1.0 - overall_R)
        
        # 恐惧指数: 记忆清晰 → 恐惧
        fear_index = max(0, overall_R - 0.5) * 2.0  # 放大到 [0, 1]
        
        # 追涨杀跌倾向 (FOMO): R 低 + greed 高
        fomo_tendency = greed_index * (1.0 - overall_R)
        
        return {
            "overall_R": overall_R,
            "leverage_tendency": leverage_tendency,
            "greed_index": greed_index,
            "fear_index": fear_index,
            "fomo_tendency": fomo_tendency,
            "risk_awareness": overall_R
        }
    
    def to_dict(self) -> Dict:
        """序列化全部记忆"""
        return {
            "agent_id": self.agent_id,
            "memories": {k: v.to_dict() for k, v in self.memories.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CognitiveMemoryBank":
        """反序列化"""
        bank = cls(agent_id=data["agent_id"], initial_lessons=[])
        for lesson_key, mem_data in data["memories"].items():
            bank.memories[lesson_key] = EconomicMemory.from_dict(mem_data)
        return bank
