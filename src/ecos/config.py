#!/usr/bin/env python3
"""Create central configuration for ECOS FSRS experiments"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Tuple

@dataclass
class FSRSConfig:
    """FSRS memory parameters"""
    w17: float = 1.8729   # Grade G=1 multiplier
    w18: float = 0.5425   # Grade G=2 multiplier
    w19: float = 0.0912   # Grade G=3 multiplier
    w20: float = 0.0658   # Grade G=4 multiplier (decay exponent)
    initial_stability: float = 45.0  # days (calibrated from R2)
    agent_type_multiplier: dict = None  # set by agent class

    def __post_init__(self):
        if self.agent_type_multiplier is None:
            self.agent_type_multiplier = {
                'retail': 1.0,
                'institution': 10.0,
                'market_maker': 15.0
            }

@dataclass
class ControlConfig:
    """Intervention policy parameters for grid search"""
    thresholds: List[float] = None
    severities: List[float] = None
    default_threshold: float = 0.30
    default_severity: float = 0.60
    optimal_threshold: float = 0.45   # from final grid search
    optimal_severity: float = 0.40   # from final grid search

    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = [0.25, 0.30, 0.35, 0.45, 0.55, 0.65]
        if self.severities is None:
            self.severities = [0.2, 0.4, 0.6, 0.8]

@dataclass
class EnvConfig:
    """ECOS environment settings"""
    n_agents: int = 30
    max_ticks: int = 300
    network_density: float = 0.47  # average for 30 agents
    use_fsrs: bool = True
    seed: int = 42

@dataclass
class RobustnessConfig:
    """Robustness analysis parameters"""
    network_densities: List[float] = None
    memory_stabilities: List[int] = None  # S values in days

    def __post_init__(self):
        if self.network_densities is None:
            self.network_densities = [0.05, 0.10, 0.20]
        if self.memory_stabilities is None:
            self.memory_stabilities = [30, 45, 60]

@dataclass
class ExperimentConfig:
    """Top-level experiment configuration"""
    fsrs: FSRSConfig = None
    control: ControlConfig = None
    env: EnvConfig = None
    robustness: RobustnessConfig = None
    n_episodes: int = 10
    random_seed: int = 42

    def __post_init__(self):
        if self.fsrs is None:
            self.fsrs = FSRSConfig()
        if self.control is None:
            self.control = ControlConfig()
        if self.env is None:
            self.env = EnvConfig()
        if self.robustness is None:
            self.robustness = RobustnessConfig()

# Global config instance
config = ExperimentConfig()

def get_grid_search_configs():
    """Generate all (threshold, severity) pairs for grid search"""
    cfgs = []
    for T in config.control.thresholds:
        for s in config.control.severities:
            cfgs.append({'threshold': T, 'severity': s})
    return cfgs

def get_robustness_configs():
    """Generate all (p, S) pairs for robustness analysis"""
    cfgs = []
    for p in config.robustness.network_densities:
        for S in config.robustness.memory_stabilities:
            cfgs.append({'p': p, 'S': S})
    return cfgs

def save_config(path: str = 'config.json'):
    """Save current config to JSON for reproducibility"""
    with open(path, 'w') as f:
        json.dump(asdict(config), f, indent=2)
    print(f"Config saved to {path}")

def load_config(path: str = 'config.json'):
    """Load config from JSON"""
    global config
    with open(path) as f:
        data = json.load(f)
    config = ExperimentConfig(
        fsrs=FSRSConfig(**data.get('fsrs', {})),
        control=ControlConfig(**data.get('control', {})),
        env=EnvConfig(**data.get('env', {})),
        robustness=RobustnessConfig(**data.get('robustness', {})),
        n_episodes=data.get('n_episodes', 10),
        random_seed=data.get('random_seed', 42)
    )
    print(f"Config loaded from {path}")
    return config

if __name__ == '__main__':
    # Quick sanity print
    print("=== ECOS FSRS Experiment Config ===")
    print(f"FSRS w17-w20: {config.fsrs.w17}, {config.fsrs.w18}, {config.fsrs.w19}, {config.fsrs.w20}")
    print(f"Initial stability: {config.fsrs.initial_stability} days")
    print(f"Grid search thresholds: {config.control.thresholds}")
    print(f"Grid search severities: {config.control.severities}")
    print(f"Optimal (T,s): ({config.control.optimal_threshold}, {config.control.optimal_severity})")
    print(f"Env: {config.env.n_agents} agents, {config.env.max_ticks} ticks")
    print(f"\nGrid configs: {len(get_grid_search_configs())}")
    print(f"Robustness configs: {len(get_robustness_configs())}")
    save_config()
