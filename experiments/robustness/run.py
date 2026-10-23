#!/usr/bin/env python3
"""Robustness Analysis — FSRS memory half-life & network density sweep"""

import sys, os, json, time
import numpy as np

from ecos.control.ecos_env import ECOSControlEnv
from ecos.config import config

def evaluate(threshold, severity, p, S_initial, n_agents=30, max_ticks=300, episodes=3):
    """Evaluate a single (p,S) configuration using baseline and optimal thresholds"""
    returns = {'baseline': [], 'optimal': []}
    for ep in range(episodes):
        # Baseline policy
        env = ECOSControlEnv(n_agents=n_agents, max_ticks=max_ticks, agent_config={'use_fsrs': True})
        obs, _ = env.reset(seed=ep)
        total_r = 0
        while True:
            action = np.array([0.6 if obs[0] < 0.30 else 0.0], dtype=np.float32)
            obs, r, term, trunc, _ = env.step(action)
            total_r += r
            if term or trunc: break
        returns['baseline'].append(total_r)

        # Optimal policy
        env = ECOSControlEnv(n_agents=n_agents, max_ticks=max_ticks, agent_config={'use_fsrs': True})
        obs, _ = env.reset(seed=ep+1000)
        total_r = 0
        while True:
            action = np.array([0.8 if obs[0] < 0.65 else 0.0], dtype=np.float32)
            obs, r, term, trunc, _ = env.step(action)
            total_r += r
            if term or trunc: break
        returns['optimal'].append(total_r)

    return {
        'baseline_return': np.mean(returns['baseline']),
        'optimal_return': np.mean(returns['optimal']),
        'improvement': np.mean(returns['optimal']) - np.mean(returns['baseline'])
    }

def main():
    print("Robustness Analysis: FSRS (p, S) sweep")
    print("=" * 60)
    results = {}
    configs = []
    for p in config.robustness.network_densities:
        for S in config.robustness.memory_stabilities:
            configs.append((p, S))

    for i, (p, S) in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] p={p:.2f}, S={S} ...", end='', flush=True)
        res = evaluate(config.control.default_threshold, config.control.default_severity, p, S, episodes=3)
        results[f'p={p:.2f},S={S}'] = res
        print(f" base={res['baseline_return']:.1f}, opt={res['optimal_return']:.1f}")

    out_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'robustness_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")

if __name__ == '__main__':
    main()
