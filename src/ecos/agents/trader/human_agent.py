"""Human Agent - 人类交易员 (支持 EE & FSRS 双引擎, Tick-based)"""

import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from .base_trader import BaseTraderAgent, TradingSignal
from ..cognitive_memory import CognitiveMemoryBank, EconomicMemory
from ..fsrs_memory import FSRSMemoryBank

# Simulation start time (for EE datetime conversion)
SIM_START = datetime.now(timezone.utc)

class HumanAgent(BaseTraderAgent):
    """
    人类交易员 Agent - 情绪化 + 行为偏差 + 认知记忆
    
    配置参数:
        use_fsrs (bool): False=EE, True=FSRS
        fsrs_agent_type (str): "retail" | "institution" | "market_maker"
    """
    
    def __init__(self, name: str, config: dict = None, rng: random.Random = None):
        default_config = {
            "initial_balance": 25000,
            "max_positions": 8,
            "fomo_factor": 0.8,            # 追涨系数
            "panic_factor": 0.9,           # 恐慌系数
            "overconfidence_threshold": 5,  # 连续盈利后过度自信阈值
            "loss_aversion": 2.0,          # 损失厌恶倍数
            "trade_frequency": 0.7,        # 每 tick 交易概率
            "emotional_state": "neutral",
            "recent_win_streak": 0,
            "recent_loss_streak": 0,
            # 记忆引擎选择
            "use_fsrs": True,               # 默认 FSRS (10年 retention 100% vs EE 91%)
            "fsrs_agent_type": "retail",   # FSRS 模式下的 Agent 类型
            # EE 参数 (仅 use_fsrs=False 时生效)
            "ee_difficulty_factor": 1.0,  # 默认 1.0, 可校准
            "sm2_initial_ef": 2.5,          # SM-2 初始 EF
        }
        if config:
            default_config.update(config)
        super().__init__(name=name, config=default_config)
        # RNG for reproducible randomness
        import random
        self.rng = rng or random
        self.agent_type = "HumanAgent"
        
        # 选择记忆引擎
        self.use_fsrs = default_config.get("use_fsrs", False)
        
        if self.use_fsrs:
            # FSRS 引擎 (幂律衰减)
            fsrs_type = default_config.get("fsrs_agent_type", "retail")
            self.memory_fsrs = FSRSMemoryBank(
                agent_id=self.agent_id,
                agent_type=fsrs_type
            )
            self.cognitive_memory = None
        else:
            # EE 引擎 (指数衰减)
            self.cognitive_memory = CognitiveMemoryBank(
                agent_id=self.agent_id,
                initial_lessons=["leverage_risk", "liquidity_crisis", "bull_market_complacency"]
            )
            # 应用 difficulty_factor 校准 (全局乘数)
            difficulty_multiplier = default_config.get("ee_difficulty_factor", 1.0)
            for mem in self.cognitive_memory.memories.values():
                mem.difficulty *= difficulty_multiplier
            self.memory_fsrs = None
        
        # 内部状态
        self._perceived_R: Optional[float] = None  # 传染效应后的感知 R
    
    def perceive(self, world: Any) -> Dict[str, Any]:
        """感知世界 (HumanAgent 感知范围较小，噪声大)"""
        # 计算组合总 P&L = 当前总资产 - 初始资金
        initial = self.config.get("initial_balance", 10000.0)
        current_total = self.get_total_value(world) if hasattr(self, 'get_total_value') else self.balance
        portfolio_pnl = current_total - initial
        perception = {
            "timestamp": SIM_START,
            "market_sentiment": self.rng.choice(["bullish", "bearish", "neutral"]),
            "recent_volatility": self.rng.uniform(0.01, 0.05),
            "portfolio_pnl": portfolio_pnl,
        }
        return perception
    
    def decide(self, perception: Dict) -> Dict:
        """决策 - 情绪驱动 + 认知偏差"""
        
        # ===== 认知行为决策（基于记忆引擎）=====
        if self.use_fsrs and self.memory_fsrs:
            # FSRS 引擎
            awareness = self.memory_fsrs.get_risk_awareness(current_tick=self.sim_tick if hasattr(self, 'sim_tick') else 0)
            risk_R = awareness["overall_R"]
            bias = self.memory_fsrs.get_behavioral_bias(current_tick=self.sim_tick if hasattr(self, 'sim_tick') else 0)
        else:
            # EE 引擎 (使用传染后的感知 R，若存在)
            if hasattr(self, '_perceived_R') and self._perceived_R is not None:
                perceived_R = self._perceived_R
                risk_R = perceived_R
                bias = {
                    "leverage_tendency": 1.0 + (1.0 - perceived_R) * 19.0,
                    "greed_index": 1.0 - perceived_R,
                    "fear_index": perceived_R
                }
                delattr(self, '_perceived_R')
            else:
                # 将 tick 转换为 EE 需要的 datetime
                sim_time = SIM_START + timedelta(days=self.sim_tick if hasattr(self, 'sim_tick') else 0)
                awareness = self.cognitive_memory.get_risk_awareness(current_time=sim_time)
                risk_R = awareness["overall_R"]
                bias = self.cognitive_memory.get_behavioral_bias(current_time=sim_time)
        
        # 动态调整行为参数
        self.config["fomo_factor"] = 0.5 + (1.0 - risk_R) * 0.5
        self.config["panic_factor"] = bias.get("panic_factor", 0.3 + risk_R * 0.7)
        self.config["trade_frequency"] = 0.3 + (1.0 - risk_R) * 0.7
        
        # 情绪状态
        if risk_R < 0.3:
            self.config["emotional_state"] = "panicked"
        elif risk_R < 0.6:
            self.config["emotional_state"] = "anxious"
        else:
            self.config["emotional_state"] = "confident"
        
        # 生成交易决策
        action = "hold"
        position_size = 0.05  # 默认仓位 5%
        
        if self.rng.random() < self.config["trade_frequency"]:
            # 决定是否交易
            if risk_R > 0.7:  # 恐惧主导 → 买入
                action = "buy"
                position_size = 0.05 + (1.0 - risk_R) * 0.20
            elif risk_R < 0.3:  # 贪婪主导 → 卖出 or 追涨
                action = "sell"
                position_size = 0.05 + (1.0 - risk_R) * 0.20
            else:
                action = self.rng.choice(["buy", "sell"])
        
        # 杠杆决策 (基于行为偏差)
        leverage = bias.get("leverage_tendency", 1.0)
        leverage = max(1.0, min(leverage, 20.0))
        
        decision = {
            "action": action,
            "symbol": "BTC",  # 简化，只交易 BTC
            "quantity": position_size,
            "leverage": leverage,
            "order_type": "market",
            "risk_R": round(risk_R, 4),
            "S": round(awareness.get("mean_S", 0) if self.use_fsrs else 0, 2),
            "emotional_state": self.config["emotional_state"]
        }
        
        return decision
    
    def act(self, decision: Dict, world: Any) -> Dict:
        """执行交易 (简化版)"""
        result = {
            "executed": False,
            "order_id": None,
            "price": None,
            "quantity": 0,
            "pnl": 0.0
        }
        
        # 简化为虚拟执行
        if decision["action"] in ["buy", "sell"]:
            result["executed"] = True
            result["symbol"] = decision["symbol"]
            result["quantity"] = decision.get("quantity", 0.05)
            result["leverage"] = decision.get("leverage", 1.0)
        
        return result
    
    def learn(self, experience: Dict):
        """学习 - HumanAgent 不进行强化学习，仅记录"""
        pass
    
    def process_market_shock(self, shock_tick: int = None, severity: float = 1.0, 
                            quality: int = 5, shock_grade: int = None):
        """
        外部调用：市场冲击触发记忆复习
        
        Args:
            shock_tick: 冲击发生的 tick (必须提供)
            severity: 冲击烈度 [0,1] (EE 用)
            quality: 学习质量 0-5 (SM-2 用)
            shock_grade: FSRS Grade (1-4, 优先使用)
        """
        if self.use_fsrs and self.memory_fsrs:
            # FSRS 模式
            if shock_grade is None:
                # 根据 severity 推断 Grade
                if severity >= 0.8:
                    shock_grade = 1
                elif severity >= 0.5:
                    shock_grade = 2
                elif severity >= 0.2:
                    shock_grade = 3
                else:
                    shock_grade = 4
            result = self.memory_fsrs.process_shock(shock_tick, shock_grade)
        else:
            # EE 模式
            shock_time = SIM_START + timedelta(days=shock_tick)
            result = self.cognitive_memory.process_shock(
                shock_time=shock_time,
                severity=severity,
                quality=quality
            )
        
        self.config["emotional_state"] = "anxiety"
        return result

    def get_risk_awareness(self, **kwargs) -> Dict:
        """
        统一获取风险意识（适配两种引擎）

        Args:
            EE模式: 接受 current_time (datetime)
            FSRS模式:  接受 current_tick (int)

        Returns:
            {"overall_R": float, "by_category": dict, ...}
        """
        if self.use_fsrs:
            tick = kwargs.get('tick', kwargs.get('current_tick', 0))
            return self.memory_fsrs.get_risk_awareness(current_tick=tick)
        else:
            time = kwargs.get('time', kwargs.get('current_time', datetime.now(timezone.utc)))
            return self.cognitive_memory.get_risk_awareness(current_time=time)

    def get_lesson_retrievability(self, lesson_id: str, **kwargs) -> float:
        """
        获取单个教训记忆的 retrievability R

        Args:
            lesson_id: 例如 "leverage_risk"
            EE: current_time (datetime)
            FSRS: current_tick (int)

        Returns:
            R ∈ [0, 1]
        """
        if self.use_fsrs:
            tick = kwargs.get('tick', kwargs.get('current_tick', 0))
            mem = self.memory_fsrs.memories.get(lesson_id)
            if mem is None:
                return 0.0
            return mem.get_retrievability(current_tick=tick)
        else:
            time = kwargs.get('time', kwargs.get('current_time', datetime.now(timezone.utc)))
            mem = self.cognitive_memory.memories.get(lesson_id)
            if mem is None:
                return 0.0
            return mem.get_retrievability(current_time=time)
    
    def get_cognitive_state(self) -> Dict:
        """获取认知状态 (监控/调试)"""
        if self.use_fsrs and self.memory_fsrs:
            current_tick = self.sim_tick if hasattr(self, 'sim_tick') else 0
            return {
                "memory_engine": "fsrs",
                "risk_awareness": self.memory_fsrs.get_risk_awareness(current_tick),
                "behavioral_bias": self.memory_fsrs.get_behavioral_bias(current_tick),
                "memory_details": self.memory_fsrs.to_dict()
            }
        else:
            current_tick = self.sim_tick if hasattr(self, 'sim_tick') else 0
            sim_time = SIM_START + timedelta(days=current_tick)
            return {
                "memory_engine": "ee",
                "risk_awareness_R": self.cognitive_memory.get_risk_awareness(current_time=sim_time),
                "behavioral_bias": self.cognitive_memory.get_behavioral_bias(),
                "memory_details": self.cognitive_memory.to_dict()
            }