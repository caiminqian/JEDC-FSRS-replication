"""Scheduler - 三省六部执行调度器"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class Task:
    """调度任务"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    schedule: Optional[str] = None  # cron 表达式或 None（立即）
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    timeout: Optional[int] = None  # 超时秒数
    max_retries: int = 0
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    result: Any = None
    status: str = "pending"  # pending, running, completed, failed, cancelled

    def __lt__(self, other: "Task") -> bool:
        """用于优先级排序"""
        return self.priority.value > other.priority.value  # 高优先级排在前面


class Scheduler:
    """
    调度器 - 尚书省执行调度

    功能:
    1. 任务队列管理（优先级队列）
    2. 依赖关系解析
    3. 超时控制
    4. 重试机制
    5. 并发执行控制
    """

    def __init__(self, max_workers: int = 10):
        """
        初始化调度器

        Args:
            max_workers: 最大并发工作线程数
        """
        self.max_workers = max_workers
        self.queue: List[Task] = []  # 待执行任务队列
        self.running: Dict[str, Task] = {}  # 正在执行的任务
        self.completed: Dict[str, Task] = {}  # 已完成任务
        self.failed: Dict[str, Task] = {}  # 失败任务
        self.running_count = 0
        self._tasks: set[asyncio.Task] = set()  # 持有 asyncio 任务句柄，防止被 GC 回收
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition()
        self._stop = False

        # 统计
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "avg_latency": 0.0
        }

        logger.info(f"Scheduler initialized: max_workers={max_workers}")

    async def submit(self, task: Task) -> str:
        """
        提交任务

        Args:
            task: Task 对象

        Returns:
            任务 ID
        """
        async with self._lock:
            self.queue.append(task)
            self.queue.sort()  # 按优先级排序
            self.stats["total_submitted"] += 1
            logger.debug(f"Task submitted: {task.id} ({task.name})")

        # 唤醒调度器
        async with self._condition:
            self._condition.notify()

        return task.id

    async def submit_func(self, name: str, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, **kwargs) -> str:
        """便捷方法：直接提交函数"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        return await self.submit(task)

    async def run(self):
        """启动调度器（主循环）"""
        logger.info("Scheduler started")
        self._stop = False

        while not self._stop:
            async with self._condition:
                # 等待有任务或停止信号
                while len(self.queue) == 0 and not self._stop:
                    await self._condition.wait()

                if self._stop:
                    break

                # 检查是否有可执行任务（满足依赖、未超并发）
                task = self._find_executable_task()
                if task and self.running_count < self.max_workers:
                    self.queue.remove(task)
                    t = asyncio.create_task(self._execute_task(task))
                    self._tasks.add(t)
                    t.add_done_callback(self._tasks.discard)
                else:
                    # 没有可执行任务，等待
                    await asyncio.sleep(0.01)

        logger.info("Scheduler stopped")

    async def _find_executable_task(self) -> Optional[Task]:
        """查找满足依赖条件的可执行任务"""
        for i, task in enumerate(self.queue):
            # 检查依赖
            if all(dep_id in self.completed for dep_id in task.dependencies):
                return task
        return None

    async def _execute_task(self, task: Task):
        """执行单个任务"""
        async with self._lock:
            self.running[task.id] = task
            self.running_count += 1
            task.status = "running"
            task.scheduled_at = datetime.now()

        start_time = time.time()
        try:
            # 执行（支持同步/异步函数）
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = await asyncio.to_thread(task.func, *task.args, **task.kwargs)

            # 成功
            task.result = result
            task.status = "completed"

            async with self._lock:
                self.completed[task.id] = task
                self.running_count -= 1
                self.stats["total_completed"] += 1

            logger.debug(f"Task completed: {task.id} ({task.name})")

        except Exception as e:
            # 失败
            task.result = str(e)
            task.status = "failed"

            async with self._lock:
                self.failed[task.id] = task
                self.running_count -= 1
                self.stats["total_failed"] += 1

            logger.error(f"Task failed: {task.id} ({task.name}): {e}")

            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = "pending"
                async with self._lock:
                    self.queue.append(task)
                    self.queue.sort()
                logger.info(f"Task retry: {task.id} (attempt {task.retry_count}/{task.max_retries})")

        finally:
            # 更新平均延迟
            elapsed = time.time() - start_time
            self.stats["avg_latency"] = (
                (self.stats["avg_latency"] * (self.stats["total_completed"] - 1) + elapsed) /
                self.stats["total_completed"]
                if self.stats["total_completed"] > 0 else elapsed
            )

    async def stop(self):
        """停止调度器"""
        self._stop = True
        async with self._condition:
            self._condition.notify_all()
        logger.info("Scheduler stopping...")

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        for store in [self.running, self.completed, self.failed]:
            if task_id in store:
                return store[task_id]
        for task in self.queue:
            if task.id == task_id:
                return task
        return None

    def get_stats(self) -> Dict:
        """获取调度器统计"""
        return {
            **self.stats,
            "queue_size": len(self.queue),
            "running": self.running_count,
            "completed_count": len(self.completed),
            "failed_count": len(self.failed)
        }
