#!/usr/bin/env python3
"""
R3 Robustness Experiments - FSRS Edition with Optimal Policy from High-T Grid Search

Tests optimal policy across network density (p) and memory half-life (S) under FSRS.

Configurations:
  p_network ∈ {0.05, 0.10, 0.20}
  S_initial ∈ {30, 45, 60} (days)  — retail agents get S_initial; institution/maker get ×10/×15

For each (p, S):
  1. Create RobustnessEnv with custom p and S
  2. Evaluate baseline policy (fixed threshold T=0.75, s=0.60)  — chosen to trigger under FSRS
  3. Evaluate optimal policy (loaded from fsrs_optimal_params.json if present, else use placeholders)
  4. Save all metrics

Output: reports/robustness/robustness_results_fsrs.json
"""

import sys, os, argparse, json, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ecos.control.ecos_env import ECOSControlEnv
from ecos.agents.trader.human_agent import HumanAgent

class RobustnessEnv(ECOSControlEnv):
    """ECOSEnv with adjustable network density (p_network) and memory S_initial (FSRS)"""
    def __init__(self, n_agents=30, max_ticks=300, p_network=0.1, S_initial=45, use_fsrs=False):
        super().__init__(n_agents=n_agents, max_ticks=max_ticks,
                         agent_config={'use_fsrs': use_fsrs})
        self.p_network = p_network
        self.S_initial = S_initial
        self.use_fsrs = use_fsrs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Inject custom p_network (rebuild edges) and S_initial (scale FSRS memories)
        self.world.graph.clear_edges()
        np.random.seed(seed if seed else np.random.randint(0, 10000))
        edges = 0
        for i in range(self.n_agents):
            for j in range(i+1, self.n_agents):
                if np.random.rand() < self.p_network:
                    self.world.add_edge(self.agents[i].agent_id, self.agents[j].agent_id, 'info_flow', weight=1.0)
                    self.world.add_edge(self.agents[j].agent_id, self.agents[i].agent_id, 'info_flow', weight=1.0)
                    edges += 1
        # Adjust FSRS S for each agent by type
        if self.use_fsrs:
            base_template_avg = (5.0 + 3.0 + 2.0) / 3.0
            for a in self.agents:
                if hasattr(a, 'memory_fsrs') and a.memory_fsrs is not None:
                    multiplier = {'retail':1.0, 'institution':10.0, 'market_maker':15.0}.get(a.agent_type, 1.0)
                    scale = self.S_initial / base_template_avg  # target avg_S = multiplier * S_initial after scaling
                    for lesson in a.memory_fsrs.memories.values():
                        lesson.S = lesson.initial_S = lesson.S * scale
        obs = self._compute_obs()
        return obs, {}

def evaluate_policy(env, threshold, severity, n_episodes=5):
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--agents', type=int, default=300)
    parser.add_argument('--ticks', type=int, default=200)
    parser.add_argument('--episodes', type=int, default=2)
    parser.add_argument('--baseline-threshold', type=float, default=0.75, help='Baseline threshold (FSRS needs high T)')
    parser.add_argument('--baseline-severity', type=float, default=0.60)
    parser.add_argument('--optimal-threshold', type=float, default=None, help='Optimal T from grid search')
    parser.add_argument('--optimal-severity', type=float, default=None, help='Optimal s from grid search')
    parser.add_argument('--load-optimal', action='store_true', help='Load optimal params from fsrs_optimal_params.json')
    args = parser.parse_args()

    print("=" * 70)
    print("FSRS ROBUSTNESS EXPERIMENTS (with optimal policy from high-T grid search)")
    print("=" * 70)
    print(f"Config: {args.agents} agents, {args.ticks} ticks, {args.episodes} episodes")

    # Determine optimal params
    if args.load_optimal:
        opt_param_path = os.path.join(os.path.dirname(__file__), '..', 'fsrs_optimal_params.json')
        opt_param_path = os.path.abspath(opt_param_path)
        if os.path.exists(opt_param_path):
            with open(opt_param_path) as f:
                opt = json.load(f)
            opt_thr = opt['threshold']
            opt_sev = opt['severity']
            print(f"Loaded optimal: T={opt_thr:.2f}, s={opt_sev:.2f}")
        else:
            print("WARNING: Optimal params file not found; using fallback T=0.80,s=0.80")
            opt_thr, opt_sev = 0.80, 0.80
    else:
        opt_thr = args.optimal_threshold if args.optimal_threshold is not None else 0.80
        opt_sev = args.optimal_severity if args.optimal_severity is not None else 0.80

    baseline_cfg = (args.baseline_threshold, args.baseline_severity)
    optimal_cfg = (opt_thr, opt_sev)

    print(f"Baseline policy: T={baseline_cfg[0]:.2f}, s={baseline_cfg[1]:.2f}")
    print(f"Optimal  policy: T={optimal_cfg[0]:.2f}, s={optimal_cfg[1]:.2f}")

    # Parameter grid (use paper's S values)
    p_vals = [0.05, 0.10, 0.20]
    S_vals = [30, 45, 60]

    results = {}
    start_total = time.time()

    for p in p_vals:
        for S in S_vals:
            cfg_key = f"p={p:.2f},S={S}"
            print(f"\n--- Config: {cfg_key} ---")
            env = RobustnessEnv(n_agents=args.agents, max_ticks=args.ticks,
                                p_network=p, S_initial=S, use_fsrs=True)
            baseline = evaluate_policy(env, baseline_cfg[0], baseline_cfg[1], n_episodes=args.episodes)
            print(f"  Baseline: return={baseline['avg_return']:.1f}, interv={baseline['avg_interventions']:.1f}/ep, zone={baseline['avg_zone_pct']:.1f}%")
            optimal = evaluate_policy(env, optimal_cfg[0], optimal_cfg[1], n_episodes=args.episodes)
            print(f"  Optimal:  return={optimal['avg_return']:.1f}, interv={optimal['avg_interventions']:.1f}/ep, zone={optimal['avg_zone_pct']:.1f}%")
            improvement = optimal['avg_return'] - baseline['avg_return']
            print(f"  Improvement: +{improvement:.1f} ({improvement/abs(baseline['avg_return'])*100:.0f}%)")
            results[cfg_key] = {
                'baseline': baseline,
                'optimal': optimal,
                'improvement': improvement,
                'p_network': p,
                'S_initial': S
            }

    elapsed = time.time() - start_total
    print(f"\n[All configs] Completed in {elapsed/60:.1f} minutes")

    out = {
        'experiments': results,
        'timestamp': time.time(),
        'config': dict(agents=args.agents, ticks=args.ticks, episodes=args.episodes,
                       baseline_threshold=baseline_cfg[0], baseline_severity=baseline_cfg[1],
                       optimal_threshold=optimal_cfg[0], optimal_severity=optimal_cfg[1])
    }
    os.makedirs("reports/robustness", exist_ok=True)
    with open("reports/robustness/robustness_results_fsrs.json", 'w') as f:
        json.dump(out, f, indent=2)
    print("\n[Saved] reports/robustness/robustness_results_fsrs.json")

    # Print summary table
    print("\n=== SUMMARY ===")
    print(f"{'Config':<15} {'Base Ret':>10} {'Opt Ret':>10} {'Improve':>12} {'Base Int':>10} {'Opt Int':>10}")
    for cfg, data in results.items():
        b = data['baseline']
        o = data['optimal']
        impr = data['improvement']
        print(f"{cfg:<15} {b['avg_return']:>10.1f} {o['avg_return']:>10.1f} {impr:>+12.1f} {b['avg_interventions']:>10.1f} {o['avg_interventions']:>10.1f}")

if __name__ == "__main__":
    main()
