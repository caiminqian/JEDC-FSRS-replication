"""Tick-based FSRS Memory Engine (ECOS Integrated Version)

替换 datetime 时间戳为 tick 整数，适配 ECOS 离散时间模拟。
"""

import math
from typing import Dict, Optional
from dataclasses import dataclass, field


# FSRS-6 预训练核心参数 (Anki 数据训练)
FSRS_DEFAULT_PARAMS = {
    "w17": 1.8729,
    "w18": 0.5425,
    "w19": 0.0912,
    "w20": 0.0658,
}


@dataclass
class FSRS_Economic_Memory:
    """
    Tick-based FSRS 经济记忆单元
    
    时间单位: 1 tick = 1 模拟日 (ECOS 标准)
    """
    
    lesson_id: str
    lesson_name: str
    
    # 核心状态
    S: float = 1.0                    # 稳定性 (天)
    last_shock_tick: int = 0          # 上次冲击发生的 tick (整数)
    
    # 元数据
    difficulty: float = 5.0
    category: str = "risk"
    
    # FSRS 参数
    w17: float = FSRS_DEFAULT_PARAMS["w17"]
    w18: float = FSRS_DEFAULT_PARAMS["w18"]
    w19: float = FSRS_DEFAULT_PARAMS["w19"]
    w20: float = FSRS_DEFAULT_PARAMS["w20"]
    
    _factor: float = field(init=False, repr=False)
    
    def __post_init__(self):
        self._recalculate_factor()
    
    def _recalculate_factor(self):
        """计算衰减因子: factor = (target_R^(-1/w20) - 1)"""
        target_R = 0.9  # FSRS 默认复习后检索率
        self._factor = math.pow(target_R, -1.0 / self.w20) - 1.0
    
    def get_retrievability(self, current_tick: int) -> float:
        """
        计算风险警惕性 R(t) - Tick 版本
        
        公式: R = (1 + factor * Δt / S)^(-w20)
        其中 Δt = current_tick - last_shock_tick (天数)
        """
        t = current_tick - self.last_shock_tick
        if t <= 0:
            return 1.0
        
        R = math.pow(1.0 + self._factor * (t / self.S), -self.w20)
        return max(0.0, min(1.0, R))
    
    def process_market_shock(self, shock_tick: int, shock_grade: int = 3) -> Dict[str, float]:
        """
        处理市场冲击 (复习)
        
        Args:
            shock_tick: 冲击发生的 tick
            shock_grade: 冲击烈度 G ∈ {1,2,3,4}
                G=1: 系统性崩溃 (≥50% 跌幅)
                G=2: 深度股灾 (≥20% 跌幅)
                G=3: 标准熊市 (≥10% 跌幅)
                G=4: 轻微回调 (≥5% 跌幅)
        
        Returns:
            Dict: {new_S, growth_factor, grade, exponent}
        """
        old_S = self.S
        
        # FSRS 核心: S' = S * exp(w17 * (G - 3 + w18) * S^(-w19))
        grade_offset = shock_grade - 3 + self.w18
        s_modifier = math.pow(self.S, -self.w19)  # 边际递减因子
        exponent = self.w17 * grade_offset * s_modifier
        
        self.S = self.S * math.exp(exponent)
        self.S = max(0.1, min(self.S, 36500))  # 边界: 0.1天 ~ 100年
        self.last_shock_tick = shock_tick
        
        growth_factor = self.S / old_S if old_S > 0 else 1.0
        
        return {
            "old_S": old_S,
            "new_S": self.S,
            "growth_factor": growth_factor,
            "grade": shock_grade,
            "grade_offset": grade_offset,
            "s_modifier": s_modifier,
            "exponent": exponent
        }
    
    def estimate_time_to_forget(self, threshold_R: float = 0.5, current_tick: int = None) -> int:
        """
        估计衰减到阈值所需 ticks
        
        解方程: threshold_R = (1 + factor * t / S)^(-w20)
        → t = (threshold_R^(-1/w20) - 1) * S / factor
        """
        if current_tick is None:
            current_tick = self.last_shock_tick
        
        t_elapsed = current_tick - self.last_shock_tick
        R_now = self.get_retrievability(current_tick)
        if R_now < threshold_R:
            return 0
        
        t_needed = (math.pow(threshold_R, -1.0 / self.w20) - 1.0) * self.S / self._factor
        return max(0, int(t_needed))
    
    def to_dict(self) -> Dict:
        return {
            "lesson_id": self.lesson_id,
            "lesson_name": self.lesson_name,
            "S": self.S,
            "last_shock_tick": self.last_shock_tick,
            "difficulty": self.difficulty,
            "category": self.category,
            "params": {
                "w17": self.w17, "w18": self.w18,
                "w19": self.w19, "w20": self.w20,
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FSRS_Economic_Memory":
        params = data.get("params", FSRS_DEFAULT_PARAMS)
        obj = cls(
            lesson_id=data["lesson_id"],
            lesson_name=data["lesson_name"],
            S=data["S"],
            difficulty=data.get("difficulty", 5.0),
            category=data.get("category", "risk"),
            w17=params.get("w17", FSRS_DEFAULT_PARAMS["w17"]),
            w18=params.get("w18", FSRS_DEFAULT_PARAMS["w18"]),
            w19=params.get("w19", FSRS_DEFAULT_PARAMS["w19"]),
            w20=params.get("w20", FSRS_DEFAULT_PARAMS["w20"]),
        )
        obj.last_shock_tick = data["last_shock_tick"]
        return obj


class FSRSMemoryBank:
    """
    FSRS 记忆银行 - 管理多条市场教训
    """
    
    # 预定义教训模板 (S 初始值基于 tick-based 校准)
    LESSONS = {
        "leverage_risk": {
            "name": "高杠杆导致爆仓",
            "category": "risk",
            "initial_S": 5.0,    # 散户初始记忆弱
            "difficulty": 6.0
        },
        "liquidity_crisis": {
            "name": "流动性枯竭无法退出",
            "category": "risk",
            "initial_S": 3.0,    # 抽象概念更难记
            "difficulty": 7.0
        },
        "bull_market_complacency": {
            "name": "长期牛市过度自信",
            "category": "strategy",
            "initial_S": 2.0,    # 牛市期间最易遗忘
            "difficulty": 4.0
        },
        "panic_selling": {
            "name": "恐慌性抛售在地板价",
            "category": "behavior",
            "initial_S": 4.0,
            "difficulty": 5.0
        },
        "regulation_change": {
            "name": "政策突变风险",
            "category": "regulation",
            "initial_S": 15.0,   # 监管教训相对持久
            "difficulty": 8.0
        }
    }
    
    def __init__(self, agent_id: str, agent_type: str = "retail"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        
        # Agent 类型乘数
        s_multiplier = {
            "retail": 1.0,        # 散户: 初始 S=1 (记忆差)
            "institution": 10.0,  # 机构: 基础风控
            "market_maker": 15.0  # 做市商: 流动性提供者最稳定
        }.get(agent_type, 1.0)
        
        self.memories: Dict[str, FSRS_Economic_Memory] = {}
        
        # 默认加载核心教训
        default_lessons = ["leverage_risk", "liquidity_crisis", "bull_market_complacency"]
        for key in default_lessons:
            if key in self.LESSONS:
                tpl = self.LESSONS[key]
                init_S = tpl["initial_S"] * s_multiplier
                self.memories[key] = FSRS_Economic_Memory(
                    lesson_id=key,
                    lesson_name=tpl["name"],
                    S=init_S,
                    difficulty=tpl["difficulty"],
                    category=tpl["category"]
                )
    
    def get_risk_awareness(self, current_tick: int = 0) -> Dict[str, float]:
        """
        计算综合风险警惕性 (Tick-based)
        
        Returns:
            {overall_R, by_category, critical_lessons, mean_S}
        """
        if not self.memories:
            return {"overall_R": 0.5, "by_category": {}, "critical_lessons": {}, "mean_S": 0}
        
        Rs = []
        by_category = {}
        critical = []
        S_vals = []
        
        for key, mem in self.memories.items():
            R = mem.get_retrievability(current_tick)
            Rs.append(R)
            S_vals.append(mem.S)
            by_category.setdefault(mem.category, []).append(R)
            if R < 0.3:
                critical.append(key)
        
        total_w = sum(m.S for m in self.memories.values())
        overall_R = sum(Rs[i] * list(self.memories.values())[i].S for i in range(len(Rs))) / total_w if total_w > 0 else 0.5
        
        return {
            "overall_R": overall_R,
            "by_category": {c: sum(v)/len(v) for c, v in by_category.items()},
            "critical_lessons": critical,
            "mean_S": sum(S_vals) / len(S_vals) if S_vals else 0,
            "S_distribution": S_vals
        }
    
    def process_shock(self, shock_tick: int, shock_grade: int = 3) -> Dict:
        """
        全局市场冲击 - 对所有记忆单元应用复习
        
        Returns:
            {shock_grade, total_S_change, avg_S_before, avg_S_after, details}
        """
        if not self.memories:
            return {}
        
        total_before = sum(m.S for m in self.memories.values())
        details = {}
        
        for key, mem in self.memories.items():
            details[key] = mem.process_market_shock(shock_tick, shock_grade)
        
        total_after = sum(m.S for m in self.memories.values())
        
        return {
            "shock_grade": shock_grade,
            "affected_memories": len(self.memories),
            "total_S_change": total_after - total_before,
            "avg_S_before": total_before / len(self.memories),
            "avg_S_after": total_after / len(self.memories),
            "details": details
        }
    
    def get_behavioral_bias(self, current_tick: int = 0) -> Dict[str, float]:
        """
        基于 FSRS 状态推导行为偏差
        
        杠杆: leverage = 1 + (1 - R) * (max_leverage - 1)
        """
        awareness = self.get_risk_awareness(current_tick)
        R = awareness["overall_R"]
        mean_S = awareness["mean_S"]
        
        max_leverage = 20.0
        leverage = 1.0 + (1.0 - R) * (max_leverage - 1.0)
        
        # S 影响: S>10 增加保守倾向
        S_effect = max(0, (mean_S - 10) / 100)
        panic_factor = min(1.0, 0.3 + R * 0.7 + S_effect)
        
        return {
            "overall_R": R,
            "leverage_tendency": leverage,
            "greed_index": 1.0 - R,
            "fear_index": R,
            "mean_S": mean_S,
            "S_stability": "high" if mean_S > 50 else "medium" if mean_S > 10 else "low",
            "panic_factor": panic_factor
        }
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "memories": {k: v.to_dict() for k, v in self.memories.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "FSRSMemoryBank":
        bank = cls(agent_id=data["agent_id"], agent_type=data.get("agent_type", "retail"))
        for key, mem_data in data["memories"].items():
            bank.memories[key] = FSRS_Economic_Memory.from_dict(mem_data)
        return bank
