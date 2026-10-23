#!/usr/bin/env python3
"""
R3: Stress Test Optimal Control Policy (1000 agents, 1000 ticks)

Test the best grid-search policy (threshold=0.55, severity=0.20) at scale.
Compare against baseline policy (threshold=0.3, severity=0.6).

Metrics:
  - Avg return, interventions, crisis steps
  - Avg_R stability (time in target zone 0.5-0.7)
  - Runtime performance (steps/sec)
"""

import sys, os, time, json, numpy as np

from ecos.control.ecos_env import ECOSControlEnv

def run_policy(env, threshold, severity, n_episodes=5, max_ticks=1000):
    """Run fixed-threshold policy for given episodes"""
    returns = []
    interventions = []
    crisis_steps = []
    in_zone = []  # fraction of steps avg_R in [0.5,0.7]
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=ep)
        total_r = steps = n_int = crisis = zone_steps = 0
        for t in range(max_ticks):
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
        in_zone.append(zone_steps / steps)
    return {
        'avg_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'avg_interventions': float(np.mean(interventions)),
        'avg_crisis': float(np.mean(crisis_steps)),
        'avg_zone_pct': float(np.mean(in_zone)*100),
        'min_return': float(np.min(returns)),
        'max_return': float(np.max(returns))
    }

def main():
    print("=" * 70)
    print("R3: STRESS TEST OPTIMAL CONTROL POLICY (1000 agents, 1000 ticks)")
    print("=" * 70)

    # Config
    n_agents = 1000
    max_ticks = 1000
    n_episodes = 3  # few episodes due to time

    print(f"\nConfig: {n_agents} agents, {max_ticks} ticks, {n_episodes} episodes each")

    # Create env (large)
    print("\n[Env] Creating environment...")
    env = ECOSControlEnv(n_agents=n_agents, max_ticks=max_ticks)

    # Baseline
    print("\n[Baseline] threshold=0.30, severity=0.60")
    start = time.time()
    baseline = run_policy(env, 0.30, 0.60, n_episodes=n_episodes, max_ticks=max_ticks)
    baseline_time = time.time() - start
    print(f"  Return: {baseline['avg_return']:.1f} ± {baseline['std_return']:.1f}")
    print(f"  Interventions: {baseline['avg_interventions']:.1f}/ep")
    print(f"  Crisis steps: {baseline['avg_crisis']:.1f}/ep")
    print(f"  Time in target zone: {baseline['avg_zone_pct']:.1f}%")
    print(f"  Runtime: {baseline_time:.1f}s")

    # Optimal
    print("\n[Optimal] threshold=0.55, severity=0.20")
    start = time.time()
    optimal = run_policy(env, 0.55, 0.20, n_episodes=n_episodes, max_ticks=max_ticks)
    optimal_time = time.time() - start
    print(f"  Return: {optimal['avg_return']:.1f} ± {optimal['std_return']:.1f}")
    print(f"  Interventions: {optimal['avg_interventions']:.1f}/ep")
    print(f"  Crisis steps: {optimal['avg_crisis']:.1f}/ep")
    print(f"  Time in target zone: {optimal['avg_zone_pct']:.1f}%")
    print(f"  Runtime: {optimal_time:.1f}s")

    # Comparison
    impr = optimal['avg_return'] - baseline['avg_return']
    print(f"\n[Result] Improvement: +{impr:.1f} ({impr/baseline['avg_return']*100:.0f}%)")
    if optimal['avg_crisis'] < baseline['avg_crisis']:
        print(f"  Crisis reduced: {baseline['avg_crisis']:.1f} → {optimal['avg_crisis']:.1f} steps/ep")
    if optimal['avg_zone_pct'] > baseline['avg_zone_pct']:
        print(f"  Time in target zone ↑: {baseline['avg_zone_pct']:.1f}% → {optimal['avg_zone_pct']:.1f}%")

    # Save
    out = {
        'baseline': baseline,
        'optimal': optimal,
        'improvement': impr,
        'config': dict(n_agents=n_agents, max_ticks=max_ticks, n_episodes=n_episodes),
        'timestamp': time.time()
    }
    os.makedirs("reports/control_stress", exist_ok=True)
    with open("reports/control_stress/stress_1000a_results.json", 'w') as f:
        json.dump(out, f, indent=2)
    print("\n[Saved] reports/control_stress/stress_1000a_results.json")

    # Also append to existing stress reports?
    print("\n[Done] R3 stress test complete.")

if __name__ == "__main__":
    main()
