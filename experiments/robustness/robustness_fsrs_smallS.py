#!/usr/bin/env python3
"""
FSRS Robustness with small S_initial to ensure interventions trigger.
S_vals = [5, 10, 15] to make avg_R drop below thresholds within 200 ticks.
"""

import sys, os, argparse, json, time, numpy as np, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ecos.control.ecos_env import ECOSControlEnv

class RobustnessEnv(ECOSControlEnv):
    def __init__(self, n_agents=30, max_ticks=200, p_network=0.1, S_initial=10, use_fsrs=False):
        super().__init__(n_agents=n_agents, max_ticks=max_ticks,
                         agent_config={'use_fsrs': use_fsrs})
        self.p_network = p_network
        self.S_initial = S_initial
        self.use_fsrs = use_fsrs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # rebuild network
        self.world.graph.clear_edges()
        np.random.seed(seed if seed else np.random.randint(0, 10000))
        edges = 0
        for i in range(self.n_agents):
            for j in range(i+1, self.n_agents):
                if np.random.rand() < self.p_network:
                    self.world.add_edge(self.agents[i].agent_id, self.agents[j].agent_id, 'info_flow', weight=1.0)
                    self.world.add_edge(self.agents[j].agent_id, self.agents[i].agent_id, 'info_flow', weight=1.0)
                    edges += 1
        # Scale FSRS S
        if self.use_fsrs:
            base_template_avg = (5.0 + 3.0 + 2.0) / 3.0
            for a in self.agents:
                if hasattr(a, 'memory_fsrs') and a.memory_fsrs is not None:
                    scale = self.S_initial / base_template_avg
                    for lesson in a.memory_fsrs.memories.values():
                        lesson.S = lesson.initial_S = lesson.S * scale
        obs = self._compute_obs()
        return obs, {}

def evaluate_policy(env, threshold, severity, n_episodes=2):
    returns, interventions, zone_pcts = [], [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=ep)
        total_r = steps = n_int = zone_steps = 0
        while True:
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r; steps += 1
            if action[0] > 0.01: n_int += 1
            if 0.5 <= obs[0] <= 0.7: zone_steps += 1
            if term or trunc: break
        returns.append(total_r)
        interventions.append(n_int)
        zone_pcts.append(zone_steps / steps)
    return {
        'avg_return': float(np.mean(returns)),
        'std_return': float(np.std(returns)),
        'avg_interventions': float(np.mean(interventions)),
        'avg_zone_pct': float(np.mean(zone_pcts)*100)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--agents', type=int, default=300)
    parser.add_argument('--ticks', type=int, default=200)
    parser.add_argument('--episodes', type=int, default=2)
    parser.add_argument('--baseline-threshold', type=float, default=0.30)
    parser.add_argument('--baseline-severity', type=float, default=0.60)
    parser.add_argument('--optimal-threshold', type=float, default=0.65)
    parser.add_argument('--optimal-severity', type=float, default=0.80)
    args = parser.parse_args()

    print("="*70)
    print("FSRS ROBUSTNESS (small S_initial)")
    print("="*70)
    print(f"Baseline: T={args.baseline_threshold:.2f}, s={args.baseline_severity:.2f}")
    print(f"Optimal : T={args.optimal_threshold:.2f}, s={args.optimal_severity:.2f}")

    p_vals = [0.05, 0.10, 0.20]
    S_vals = [5, 10, 15]   # SMALL S for FSRS

    results = {}
    start = time.time()
    for p, S in itertools.product(p_vals, S_vals):
        cfg_key = f"p={p:.2f},S={S}"
        print(f"\n--- {cfg_key} ---")
        env = RobustnessEnv(n_agents=args.agents, max_ticks=args.ticks,
                            p_network=p, S_initial=S, use_fsrs=True)
        base = evaluate_policy(env, args.baseline_threshold, args.baseline_severity, args.episodes)
        opt  = evaluate_policy(env, args.optimal_threshold, args.optimal_severity, args.episodes)
        impr = opt['avg_return'] - base['avg_return']
        print(f"  Baseline: ret={base['avg_return']:.1f}, interv={base['avg_interventions']:.1f}/ep")
        print(f"  Optimal : ret={opt['avg_return']:.1f}, interv={opt['avg_interventions']:.1f}/ep")
        print(f"  Improv  : {impr:+.1f} ({impr/abs(base['avg_return'])*100:.0f}%)")
        results[cfg_key] = {'baseline': base, 'optimal': opt, 'improvement': impr,
                            'p_network': p, 'S_initial': S}

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed/60:.1f} min")
    out = {'experiments': results, 'timestamp': time.time(),
           'config': dict(agents=args.agents, ticks=args.ticks, episodes=args.episodes,
                          baseline_threshold=args.baseline_threshold, baseline_severity=args.baseline_severity,
                          optimal_threshold=args.optimal_threshold, optimal_severity=args.optimal_severity)}
    os.makedirs('reports/robustness', exist_ok=True)
    with open('reports/robustness/robustness_results_fsrs.json', 'w') as f:
        json.dump(out, f, indent=2)
    print("[Saved] reports/robustness/robustness_results_fsrs.json")

    # Summary table
    print("\n=== SUMMARY ===")
    print(f"{'Config':<12} {'Base Ret':>10} {'Opt Ret':>10} {'Improv':>12} {'Base Int':>9} {'Opt Int':>9}")
    for cfg, d in results.items():
        b = d['baseline']; o = d['optimal']; impr = d['improvement']
        print(f"{cfg:<12} {b['avg_return']:>10.1f} {o['avg_return']:>10.1f} {impr:>+12.1f} {b['avg_interventions']:>9.1f} {o['avg_interventions']:>9.1f}")

if __name__ == '__main__':
    main()
