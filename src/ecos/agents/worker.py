"""Agent Worker - 分布式 Agent 进程

从 Redis 队列接收任务（perceive/decide/act），返回结果。
支持多策略：trend_follower, market_maker, arbitrage 等。
"""

import argparse
import json
import logging
import time
import uuid

import redis
from ecos.core.world_state import WorldStateGraph
from ecos.agents.trader.retail_agent import RetailAgent
from ecos.agents.trader.institution_agent import InstitutionAgent
from ecos.agents.trader.market_maker import MarketMakerAgent

logger = logging.getLogger(__name__)

# 连接 Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Agent 类型映射
AGENT_TYPES = {
    'retail': RetailAgent,
    'institution': InstitutionAgent,
    'market_maker': MarketMakerAgent,
}

class AgentWorker:
    """分布式 Agent 工作进程"""

    def __init__(self, strategy: str, agent_id: str = None):
        self.strategy = strategy
        self.agent_id = agent_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.agent = self._create_agent(strategy)
        self.world_cache = WorldStateGraph(name=f"world-{self.agent_id}")
        self.running = False

        logger.info(f"AgentWorker initialized: {self.agent_id} strategy={strategy}")

    def _create_agent(self, strategy: str):
        """根据策略创建 Agent"""
        agent_class = AGENT_TYPES.get(strategy)
        if not agent_class:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {list(AGENT_TYPES.keys())}")

        config = {
            'initial_balance': 50000,
            'fomo_factor': 0.8,
            'position_size_pct': 0.05
        }
        return agent_class(name=self.agent_id, config=config)

    def start(self):
        """启动 Worker，监听任务队列"""
        self.running = True
        queue_name = f"ecos:agent:task:{self.strategy}"

        logger.info(f"Listening on queue: {queue_name}")

        while self.running:
            try:
                # BLPOP 阻塞获取任务（超时 1 秒）
                task = redis_client.blpop(queue_name, timeout=1)
                if task:
                    _, task_data = task
                    self._process_task(task_data)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    def _process_task(self, task_json: str):
        """处理单个任务"""
        try:
            task = json.loads(task_json)
            task_id = task.get('task_id')
            tick = task.get('tick')
            action = task.get('action')  # 'perceive', 'decide', 'act'

            if action == 'perceive':
                world_snapshot = task.get('world_snapshot', {})
                # TODO: 重建 WorldStateGraph 从 snapshot（简化：直接用空图）
                # 实际应接收增量更新
                perception = self.agent.perceive(self.world_cache)
                result = {'perception': perception}

            elif action == 'decide':
                perception = task.get('perception', {})
                decision = self.agent.decide(perception)
                result = {'decision': decision}

            elif action == 'act':
                decision = task.get('decision', {})
                # world 需从主进程传递增量
                result = self.agent.act(decision, self.world_cache)

            else:
                result = {'error': f'Unknown action: {action}'}

            # 返回结果
            response = {
                'task_id': task_id,
                'agent_id': self.agent_id,
                'tick': tick,
                'action': action,
                'result': result,
                'timestamp': time.time()
            }
            redis_client.rpush(f"ecos:agent:result:{self.agent_id}", json.dumps(response))
            redis_client.expire(f"ecos:agent:result:{self.agent_id}", 60)

        except Exception as e:
            logger.error(f"Task processing failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="ECOS Agent Worker")
    parser.add_argument("--strategy", default="retail", choices=list(AGENT_TYPES.keys()),
                       help="Agent strategy type")
    parser.add_argument("--agent-id", help="Unique agent ID (auto-generated if omitted)")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    worker = AgentWorker(strategy=args.strategy, agent_id=args.agent_id)
    worker.start()

if __name__ == "__main__":
    main()
