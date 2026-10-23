#!/usr/bin/env python3
"""
R3: Control Optimization - Grid Search for Optimal Threshold Policy

Instead of RL (which failed), perform exhaustive grid search over:
  threshold ∈ [0.2, 0.8] (intervene when avg_R < threshold)
  severity  ∈ [0.1, 0.9] (intervention strength)

Evaluate each (threshold, severity) pair over N episodes.
Find parameters that maximize average return.

Expected: should easily beat baseline (threshold=0.3, sev=0.6 → return 175).
Optimal likely: threshold around 0.45-0.55, severity 0.4-0.5 (avoid overshoot).
"""

import sys, os, itertools, json, time

import numpy as np
from ecos.control.ecos_env import ECOSControlEnv

def evaluate_policy(threshold, severity, n_episodes=10, seed_offset=0):
    """Evaluate fixed-threshold policy"""
    env = ECOSControlEnv(
        n_agents=30,
        max_ticks=300,
        agent_config={'use_fsrs': True}  # FSRS only; no initial_stability override
    )
    returns = []
    interventions = []
    crisis_steps = []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed_offset + ep)
        total_r = steps = n_int = crisis = 0
        while True:
            # Fixed threshold policy
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r; steps += 1
            if action[0] > 0.01: n_int += 1
            if obs[0] < 0.25: crisis += 1
            if term or trunc: break
        returns.append(total_r)
        interventions.append(n_int)
        crisis_steps.append(crisis)
    return {
        'avg_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'avg_interventions': float(np.mean(interventions)),
        'avg_crisis': float(np.mean(crisis_steps))
    }

def main():
    print("=" * 70)
    print("R3: CONTROL OPTIMIZATION - GRID SEARCH OVER THRESHOLD POLICY")
    print("=" * 70)

    # Coarse grid (will refine later if needed)
    thresholds = [0.25, 0.35, 0.45, 0.55, 0.65]  # 5 values
    severities = [0.2, 0.4, 0.6, 0.8]                # 4 values
    # Ensure baseline included
    if 0.3 not in thresholds: thresholds.append(0.3)
    if 0.6 not in severities: severities.append(0.6)

    print(f"Thresholds: {thresholds}")
    print(f"Severities: {severities}")
    n_configs = len(thresholds) * len(severities)
    print(f"Total configurations: {n_configs}")
    print(f"Episodes per config: 10 → total episodes: {n_configs*10}")

    results = {}
    best_return = -np.inf
    best_cfg = None
    start = time.time()

    for i, (thr, sev) in enumerate(itertools.product(thresholds, severities)):
        cfg = f"thr={thr:.2f},sev={sev:.2f}"
        res = evaluate_policy(thr, sev, n_episodes=10, seed_offset=i)
        results[cfg] = res
        if res['avg_return'] > best_return:
            best_return = res['avg_return']
            best_cfg = cfg
        print(f"[{i+1:3d}/{n_configs}] {cfg} → return={res['avg_return']:7.1f} ±{res['std_return']:5.1f}, interv={res['avg_interventions']:.1f}/ep, crisis={res['avg_crisis']:.1f}  (best: {best_return:.1f})")

    elapsed = time.time() - start
    print(f"\n[Grid Search] Completed in {elapsed/60:.1f} minutes")
    print(f"Best config: {best_cfg}")
    print(f"Best return: {best_return:.1f}")

    # Compare to baseline
    baseline_cfg = "thr=0.30,sev=0.60"
    baseline_ret = results.get(baseline_cfg, {}).get('avg_return', None)
    if baseline_ret:
        impr = best_return - baseline_ret
        print(f"Baseline ({baseline_cfg}): {baseline_ret:.1f}")
        print(f"Improvement: {impr:+.1f}")
        if impr > 0:
            print("[SUCCESS] Grid search found better policy!")
        else:
            print("[WARN] No improvement over baseline")

    # Save results
    out = {
        'best_cfg': best_cfg,
        'best_return': best_return,
        'baseline_cfg': baseline_cfg,
        'baseline_return': baseline_ret,
        'all_results': results,
        'elapsed_seconds': elapsed,
        'timestamp': time.time()
    }
    # Save results with absolute path
    from pathlib import Path
    output_path = Path(__file__).parent.parent / 'models' / 'control_grid_search' / 'results_grid.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n[Results] saved to {output_path}")

if __name__ == "__main__":
    main()
