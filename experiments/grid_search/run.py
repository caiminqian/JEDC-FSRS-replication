#!/usr/bin/env python3
"""
Grid Search Experiment — Entry Point
Original: scripts/grid_search_control.py
"""

import sys, os, itertools, json, time
import numpy as np

from ecos.control.ecos_env import ECOSControlEnv
from ecos.agents.trader.human_agent import HumanAgent
from ecos.config import config

def evaluate_policy(threshold, severity, n_agents=30, max_ticks=300, n_episodes=10, use_fsrs=True):
    results = {'returns': [], 'interventions': [], 'crisis': [], 'zone_pct': []}
    for ep in range(n_episodes):
        env = ECOSControlEnv(n_agents=n_agents, max_ticks=max_ticks, agent_config={'use_fsrs': use_fsrs})
        obs, _ = env.reset(seed=ep)
        total_r = steps = n_int = zone = crisis = 0
        while True:
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r; steps += 1
            if info['intervened']: n_int += 1
            if 0.5 <= obs[0] <= 0.7: zone += 1
            if obs[0] < 0.25: crisis += 1
            if term or trunc: break
        results['returns'].append(total_r)
        results['interventions'].append(n_int)
        results['crisis'].append(crisis)
        results['zone_pct'].append(zone/steps*100)
    return {
        'avg_return': np.mean(results['returns']),
        'std_return': np.std(results['returns']),
        'avg_interventions': np.mean(results['interventions']),
        'avg_zone_pct': np.mean(results['zone_pct']),
        'avg_crisis': np.mean(results['crisis'])
    }

def main():
    print("R3: CONTROL OPTIMIZATION - GRID SEARCH (FSRS)")
    print("=" * 60)
    thresholds = config.control.thresholds
    severities = config.control.severities
    n_eps = config.n_episodes

    results = {}
    best_return = -np.inf
    best_cfg = None
    start = time.time()

    for i, (T, s) in enumerate(itertools.product(thresholds, severities), 1):
        print(f"[{i}/{len(thresholds)*len(severities)}] T={T:.2f}, s={s:.2f} ...", end='', flush=True)
        res = evaluate_policy(T, s, n_episodes=n_eps, use_fsrs=True)
        results[f'thr={T},sev={s}'] = res
        if res['avg_return'] > best_return:
            best_return = res['avg_return']
            best_cfg = (T, s)
        print(f" ret={res['avg_return']:.1f}")

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed/60:.1f} min")
    print(f"Best: T={best_cfg[0]}, s={best_cfg[1]}, return={best_return:.1f}")

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(out_dir, exist_ok=True)
    out = {
        'best_cfg': f'thr={best_cfg[0]},sev={best_cfg[1]}',
        'best_return': best_return,
        'baseline_cfg': f'thr={config.control.default_threshold},sev={config.control.default_severity}',
        'baseline_return': None,  # compute below
        'all_results': results
    }
    # Compute baseline
    base_res = evaluate_policy(config.control.default_threshold, config.control.default_severity, n_episodes=n_eps)
    out['baseline_return'] = base_res['avg_return']
    out['improvement'] = best_return - base_res['avg_return']

    with open(os.path.join(out_dir, 'results_grid.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_dir}/results_grid.json")

if __name__ == '__main__':
    main()
