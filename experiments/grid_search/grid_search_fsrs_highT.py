#!/usr/bin/env python3
"""FSRS-specific grid search over HIGH thresholds (0.65-0.95) and severities.

FSRS agents maintain avg_R > 0.7 under low thresholds, so optimal policy
requires higher T to trigger interventions. This script searches:
  thresholds: 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95
  severities: 0.2, 0.4, 0.6, 0.8
  S_initial: 45 (calibrated)
  30 agents, 300 ticks, 10 episodes each
"""

import sys, os, json, time, numpy as np, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ecos.control.ecos_env import ECOSControlEnv

def evaluate_policy(env, threshold, severity, n_episodes=10):
    returns, interventions, crisis_steps, zone_pcts = [], [], [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=ep)
        total_r = steps = n_int = crisis = zone_steps = 0
        while True:
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r; steps += 1
            if action[0] > 0.01: n_int += 1
            if obs[0] < 0.25: crisis += 1
            if 0.5 <= obs[0] <= 0.7: zone_steps += 1
            if term or trunc: break
        returns.append(total_r)
        interventions.append(n_int)
        crisis_steps.append(crisis)
        zone_pcts.append(zone_steps / steps)
    return {
        'avg_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'avg_interventions': float(np.mean(interventions)),
        'avg_crisis': float(np.mean(crisis_steps)),
        'avg_zone_pct': float(np.mean(zone_pcts)*100)
    }

def main():
    print("=" * 70)
    print("FSRS GRID SEARCH (High Thresholds)")
    print("=" * 70)

    # High-threshold grid for FSRS
    thresholds = [0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
    severities = [0.2, 0.4, 0.6, 0.8]
    S_initial = 45  # calibrated stability

    print(f"Thresholds: {thresholds}")
    print(f"Severities: {severities}")
    print(f"S_initial: {S_initial}")
    n_configs = len(thresholds) * len(severities)
    print(f"Total configs: {n_configs}, 10 episodes each → {n_configs*10} episodes")

    results = {}
    best_return = -np.inf
    best_cfg = None
    start = time.time()

    for i, (thr, sev) in enumerate(itertools.product(thresholds, severities)):
        cfg = f"thr={thr:.2f},sev={sev:.2f}"
        env = ECOSControlEnv(
            n_agents=30,
            max_ticks=300,
            agent_config={'use_fsrs': True, 'initial_stability': S_initial}
        )
        res = evaluate_policy(env, thr, sev, n_episodes=10)
        results[cfg] = res
        if res['avg_return'] > best_return:
            best_return = res['avg_return']
            best_cfg = cfg
        print(f"[{i+1:3d}/{n_configs}] {cfg} → ret={res['avg_return']:7.1f} ±{res['std_return']:5.1f}, interv={res['avg_interventions']:.1f}/ep  (best: {best_return:.1f})")

    elapsed = time.time() - start
    print(f"\n[FSRS Grid Search] Completed in {elapsed/60:.1f} minutes")
    print(f"Best config: {best_cfg}")
    print(f"Best return: {best_return:.1f}")

    baseline_cfg = "thr=0.30,sev=0.60"
    baseline_ret = results.get(baseline_cfg, {}).get('avg_return', None)
    if baseline_ret is not None:
        impr = best_return - baseline_ret
        print(f"Baseline ({baseline_cfg}): {baseline_ret:.1f}")
        print(f"Improvement: {impr:+.1f} ({impr/abs(baseline_ret)*100:.0f}%)")

    out = {
        'best_cfg': best_cfg,
        'best_return': best_return,
        'baseline_cfg': baseline_cfg,
        'baseline_return': baseline_ret,
        'all_results': results,
        'elapsed_seconds': elapsed,
        'timestamp': time.time(),
        'config': {'S_initial': S_initial, 'agents': 30, 'ticks': 300, 'episodes': 10}
    }
    output_path = os.path.join(os.path.dirname(__file__), 'models', 'control_grid_search', 'results_grid_fsrs_highT.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n[Saved] {output_path}")

if __name__ == "__main__":
    main()
