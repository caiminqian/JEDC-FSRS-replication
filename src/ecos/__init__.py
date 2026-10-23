"""Economic Civilization OS (ECOS) - Multi-Agent Economic World Simulator"""

__version__ = "0.1.0-alpha"
__author__ = "OpenClaw"
__description__ = "A self-evolving multi-agent economic world simulation and governance system"

# Core components (Phase 1)
from .core import WorldStateGraph, EventBus, SimClock, Scheduler, Task, TaskPriority
from .agents import BaseAgent

# ECOS main class (Phase 2 - not yet implemented)
# from .main import ECOS

__all__ = [
    "WorldStateGraph",
    "EventBus",
    "SimClock",
    "Scheduler",
    "Task",
    "TaskPriority",
    "BaseAgent",
    # "ECOS",  # pending Phase 2
]
