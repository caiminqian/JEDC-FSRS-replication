"""Base Agent - 所有智能体的基类"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentMemory:
    """Agent 短期记忆"""
    observations: List[Dict] = field(default_factory=list)
    actions: List[Dict] = field(default_factory=list)
    rewards: List[float] = field(default_factory=list)
    maxlen: int = 1000

    def add_observation(self, obs: Dict):
        self.observations.append({"timestamp": datetime.now().isoformat(), **obs})
        if len(self.observations) > self.maxlen:
            self.observations.pop(0)

    def add_action(self, action: Dict, reward: float = 0.0):
        self.actions.append({"timestamp": datetime.now().isoformat(), **action})
        self.rewards.append(reward)
        if len(self.actions) > self.maxlen:
            self.actions.pop(0)
            self.rewards.pop(0)

    def get_recent(self, n: int = 10) -> List[Dict]:
        """获取最近的记忆"""
        return self.observations[-n:]

    def get_average_reward(self, last_n: int = 100) -> float:
        """计算最近的平均奖励"""
        if not self.rewards:
            return 0.0
        n = min(last_n, len(self.rewards))
        return sum(self.rewards[-n:]) / n


class BaseAgent(ABC):
    """
    Agent 基类

    生命周期:
    1. perceive(world_state) -> perception
    2. decide(perception) -> decision
    3. act(decision) -> result
    4. learn(result) -> update internal state
    """

    def __init__(
        self,
        agent_id: str = None,
        name: str = None,
        config: Dict = None
    ):
        """
        初始化 Agent

        Args:
            agent_id: 唯一标识（自动生成如果未提供）
            name: 显示名称
            config: 配置字典（初始资金、风险偏好等）
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.config = config or {}

        # 状态
        self.balance: float = self.config.get("initial_balance", 10000.0)
        self.position: Dict[str, float] = {}  # symbol -> size
        self.risk_profile: str = self.config.get("risk_profile", "moderate")  # conservative/moderate/aggressive
        self.active: bool = True
        self.generation: int = 0  # 进化代数
        self.parent_id: Optional[str] = None  # 父 Agent（用于遗传）

        # 记忆
        self.memory = AgentMemory()

        # 统计
        self.stats = {
            "decisions": 0,
            "actions": 0,
            "rewards": 0.0,
            "errors": 0,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Agent created: {self.name} ({self.agent_id[:8]}...)")

    @abstractmethod
    def perceive(self, world_state: Dict) -> Dict:
        """
        感知世界状态（提取相关信息）

        Args:
            world_state: 完整的世界状态图

        Returns:
            感知结果（Agent 视角的世界）
        """
        pass

    @abstractmethod
    def decide(self, perception: Dict) -> Dict:
        """
        基于感知做出决策

        Args:
            perception: 感知后的世界

        Returns:
            决策（如买入/卖出/数量）
        """
        pass

    @abstractmethod
    def act(self, decision: Dict, world: "WorldStateGraph") -> Dict:
        """
        执行行动并更新世界

        Args:
            decision: 决策结果
            world: 世界状态图（可修改）

        Returns:
            执行结果（含 reward）
        """
        pass

    def learn(self, experience: Dict):
        """
        学习（从经验中更新策略）

        Args:
            experience: 经验字典 (state, action, reward, next_state)
        """
        # 默认实现：存储到记忆
        self.memory.add_action(
            action=experience.get("action", {}),
            reward=experience.get("reward", 0.0)
        )
        self.stats["rewards"] += experience.get("reward", 0.0)

    def reset(self):
        """重置 Agent 状态（保留学习参数）"""
        self.balance = self.config.get("initial_balance", 10000.0)
        self.position.clear()
        self.memory = AgentMemory()
        logger.info(f"Agent reset: {self.name}")

    def get_info(self) -> Dict:
        """获取 Agent 信息（用于监控/治理）"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.__class__.__name__,
            "balance": self.balance,
            "position": self.position,
            "active": self.active,
            "generation": self.generation,
            "parent_id": self.parent_id,
            "risk_profile": self.risk_profile,
            "stats": self.stats,
            "avg_reward": self.memory.get_average_reward()
        }

    def get_dna(self) -> Dict:
        """获取 Agent 的 DNA（用于遗传/进化）"""
        return {
            "class": self.__class__.__name__,
            "config": self.config,
            "generation": self.generation,
            "parent_id": self.parent_id
        }

    def clone(self) -> "BaseAgent":
        """克隆 Agent（用于进化）"""
        child = self.__class__(
            agent_id=str(uuid.uuid4()),
            name=f"{self.name}_gen{self.generation + 1}",
            config=self.config.copy()
        )
        child.balance = self.balance * 0.5  # 分割资金
        child.parent_id = self.agent_id
        child.generation = self.generation + 1
        return child

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.agent_id[:8]}) balance={self.balance:.2f}>"
