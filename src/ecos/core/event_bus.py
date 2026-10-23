"""Event Bus - Redis Pub/Sub 事件总线"""

import json
import redis
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    基于 Redis Pub/Sub 的事件总线

    负责:
    1. Agent 间解耦通信
    2. 世界状态更新广播
    3. 风险警报推送
    4. 治理决策流水
    """

    # 预定义频道
    CHANNELS = {
        "world_update": "ecos:world:update",        # 世界状态更新
        "agent_action": "ecos:agent:action",        # Agent 行动
        "agent_perceive": "ecos:agent:perceive",    # Agent 感知
        "risk_alert": "ecos:risk:alert",            # 风险警报
        "governance_proposal": "ecos:gov:proposal", # 治理提案
        "governance_review": "ecos:gov:review",     # 治理审查
        "governance_execution": "ecos:gov:exec",    # 治理执行
        "market_event": "ecos:market:event",        # 市场事件
        "environment_change": "ecos:env:change",    # 环境变化
        "system_control": "ecos:system:control",    # 系统控制
    }

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        初始化事件总线

        Args:
            redis_url: Redis 连接地址
        """
        self.redis_url = redis_url
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None

        logger.info(f"EventBus initialized: {redis_url}")

    def publish(self, channel: str, event: Dict[str, Any]) -> bool:
        """
        发布事件到频道

        Args:
            channel: 频道名称（或使用 CHANNELS 常量）
            event: 事件数据（自动添加时间戳）

        Returns:
            True 发布成功，False 失败
        """
        if not isinstance(event, dict):
            logger.error("Event must be dict")
            return False

        # 自动添加时间戳
        event["_timestamp"] = datetime.now().isoformat()

        try:
            message = json.dumps(event, default=str)
            self.redis.publish(channel, message)
            logger.debug(f"Published to {channel}: {event.get('type', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Publish failed to {channel}: {e}")
            return False

    def subscribe(self, channel: str, callback: Callable[[Dict], None]) -> bool:
        """
        订阅频道

        Args:
            channel: 频道名称
            callback: 回调函数，接收 event dict

        Returns:
            True 订阅成功
        """
        try:
            self.pubsub.subscribe(**{channel: self._make_wrapper(callback)})
            if channel not in self.subscribers:
                self.subscribers[channel] = []
            self.subscribers[channel].append(callback)
            logger.info(f"Subscribed to channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"Subscribe failed for {channel}: {e}")
            return False

    def _make_wrapper(self, callback: Callable) -> Callable:
        """包装回调，解析 JSON"""
        def wrapper(message):
            try:
                data = json.loads(message["data"])
                callback(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Callback error: {e}")

        return wrapper

    def start_listening(self, block: bool = True):
        """
        启动监听线程（阻塞）

        Args:
            block: True 阻塞当前线程，False 启动后台线程
        """
        if self.running:
            logger.warning("EventBus already listening")
            return

        self.running = True

        def listen():
            logger.info("EventBus listener started")
            for message in self.pubsub.listen():
                if not self.running:
                    break
                if message["type"] == "message":
                    # 已通过 wrapper 处理
                    pass

        if block:
            listen()
        else:
            self.thread = threading.Thread(target=listen, daemon=True)
            self.thread.start()
            logger.info("EventBus listener thread started")

    def stop_listening(self):
        """停止监听"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.pubsub.close()
        logger.info("EventBus stopped")

    # --- 便捷方法（预定义频道）---

    def emit_world_update(self, world_state: Dict, node_id: str = None, change_type: str = "update"):
        """发出世界状态更新"""
        self.publish(self.CHANNELS["world_update"], {
            "type": "world_update",
            "world_state": world_state,
            "node_id": node_id,
            "change_type": change_type,
            "source": "ecos-core"
        })

    def emit_agent_action(self, agent_id: str, action: Dict, target: str = None):
        """发出 Agent 行动"""
        self.publish(self.CHANNELS["agent_action"], {
            "type": "agent_action",
            "agent_id": agent_id,
            "action": action,
            "target": target,
            "source": agent_id
        })

    def emit_agent_perception(self, agent_id: str, perception: Dict):
        """发出 Agent 感知结果"""
        self.publish(self.CHANNELS["agent_perceive"], {
            "type": "agent_perceive",
            "agent_id": agent_id,
            "perception": perception,
            "source": agent_id
        })

    def emit_risk_alert(self, risk_type: str, level: int, details: Dict, source: str = "risk-agent"):
        """发出风险警报"""
        self.publish(self.CHANNELS["risk_alert"], {
            "type": "risk_alert",
            "risk_type": risk_type,
            "level": level,  # 1-5
            "details": details,
            "source": source
        })

    def emit_governance_proposal(self, proposal: Dict):
        """发出治理提案（中书省）"""
        self.publish(self.CHANNELS["governance_proposal"], {
            "type": "governance_proposal",
            "proposal": proposal,
            "stage": "zhongshu",
            "source": "policy_generator"
        })

    def emit_governance_review(self, policy_id: str, decision: Dict, reviewer: str):
        """发出治理审查结果（门下省）"""
        self.publish(self.CHANNELS["governance_review"], {
            "type": "governance_review",
            "policy_id": policy_id,
            "decision": decision,
            "reviewer": reviewer,
            "stage": "menxia"
        })

    def emit_governance_execution(self, policy: Dict, resources: Dict):
        """发出治理执行指令（尚书省）"""
        self.publish(self.CHANNELS["governance_execution"], {
            "type": "governance_execution",
            "policy": policy,
            "resources": resources,
            "stage": "shangshu",
            "source": "executor"
        })

    def emit_market_event(self, event: Dict):
        """发出市场事件"""
        self.publish(self.CHANNELS["market_event"], {
            "type": "market_event",
            "event": event,
            "source": "market-feed"
        })

    def emit_environment_change(self, env_state: Dict):
        """发出环境变化（五运六气）"""
        self.publish(self.CHANNELS["environment_change"], {
            "type": "environment_change",
            "environment": env_state,
            "source": "economic-weather-engine"
        })

    def emit_system_control(self, command: str, params: Dict = None):
        """发出系统控制命令"""
        self.publish(self.CHANNELS["system_control"], {
            "type": "system_control",
            "command": command,  # "start", "stop", "pause", "resume"
            "params": params or {},
            "source": "operator"
        })

    # --- 订阅便捷方法 ---

    def on_world_update(self, callback: Callable[[Dict], None]):
        """订阅世界更新"""
        return self.subscribe(self.CHANNELS["world_update"], callback)

    def on_agent_action(self, callback: Callable[[Dict], None]):
        """订阅 Agent 行动"""
        return self.subscribe(self.CHANNELS["agent_action"], callback)

    def on_risk_alert(self, callback: Callable[[Dict], None]):
        """订阅风险警报"""
        return self.subscribe(self.CHANNELS["risk_alert"], callback)

    def on_governance_proposal(self, callback: Callable[[Dict], None]):
        """订阅治理提案"""
        return self.subscribe(self.CHANNELS["governance_proposal"], callback)

    def close(self):
        """关闭连接"""
        self.stop_listening()
        self.redis.close()
        logger.info("EventBus closed")
