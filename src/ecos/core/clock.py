"""Simulation Clock - 全局时钟（支持真实时间与模拟时间）"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from threading import Thread, Event
import logging

logger = logging.getLogger(__name__)


class SimClock:
    """
    模拟时钟

    支持三种模式:
    1. 真实时间 (speed=1.0) - 与真实时间同步
    2. 加速模拟 (speed>1.0) - 时间流速加快
    3. 步进模式 (step_mode=True) - 手动推进每个 tick
    """

    def __init__(self, speed: float = 1.0, start_time: Optional[datetime] = None):
        """
        初始化时钟

        Args:
            speed: 时间流速倍率（1.0 = 实时，10.0 = 10倍速）
            start_time: 起始时间（默认当前时间）
        """
        self.speed = speed
        self.current_time = start_time or datetime.now()
        self._start_real_time = time.time()
        self._start_sim_time = self.current_time
        self.running = False
        self.paused = False
        self._pause_event = Event()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

        # 统计
        self.ticks = 0
        self.tick_interval = 1.0  # 每个 tick 的间隔（秒）

        logger.info(f"SimClock initialized: speed={speed}x, start_time={self.current_time}")

    def start(self):
        """启动时钟（后台线程）"""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self._pause_event.set()

        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("SimClock started")

    def stop(self):
        """停止时钟"""
        self.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("SimClock stopped")

    def pause(self):
        """暂停时钟"""
        self.paused = True
        self._pause_event.clear()
        logger.info("SimClock paused")

    def resume(self):
        """恢复时钟"""
        self.paused = False
        self._pause_event.set()
        logger.info("SimClock resumed")

    def tick(self) -> datetime:
        """
        推进一个 tick（步进模式）

        Returns:
            当前时间
        """
        self._advance_time()
        self.ticks += 1
        return self.current_time

    def _run(self):
        """时钟后台线程"""
        next_tick = time.time()

        while self.running and not self._stop_event.is_set():
            # 等待直到下一个 tick
            self._pause_event.wait()

            now = time.time()
            if now >= next_tick:
                self.tick()
                next_tick += self.tick_interval / self.speed

            # 短暂休眠避免 CPU 占用
            time.sleep(0.001)

    def _advance_time(self):
        """根据速度推进时间"""
        if self.speed == 1.0:
            # 实时模式
            self.current_time = datetime.now()
        else:
            # 加速/减速模式
            elapsed_real = time.time() - self._start_real_time
            elapsed_sim = elapsed_real * self.speed
            self.current_time = self._start_sim_time + timedelta(seconds=elapsed_sim)

    def now(self) -> datetime:
        """获取当前模拟时间"""
        if not self.running:
            return self.current_time
        self._advance_time()
        return self.current_time

    def sleep(self, seconds: float):
        """
        模拟睡眠（根据速度调整）

        Args:
            seconds: 真实秒数
        """
        if self.speed == 1.0:
            time.sleep(seconds)
        else:
            # 在加速模式下，睡眠时间缩短
            time.sleep(seconds / self.speed)

    def set_speed(self, speed: float):
        """调整时间流速"""
        self.speed = speed
        logger.info(f"Clock speed set to {speed}x")

    def get_elapsed(self) -> timedelta:
        """获取已运行的模拟时间"""
        return self.now() - self._start_sim_time

    def get_stats(self) -> Dict:
        """获取时钟统计"""
        return {
            "running": self.running,
            "paused": self.paused,
            "speed": self.speed,
            "current_time": self.current_time.isoformat(),
            "ticks": self.ticks,
            "elapsed": str(self.get_elapsed())
        }
