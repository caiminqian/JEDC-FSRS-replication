import sys, json, itertools, time
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
import numpy as np
from ecos.control.ecos_env import ECOSControlEnv

# v48 rerun: identical to grid_search_control.py except S override.
# After every reset, set every FSRS lesson's initial stability to 45.0
# (the paper's calibrated S0), then recompute the observation.
# This is the parameterisation ps_sweep.py used; the original grid ran
# the default bank (5/3/2) and never set S.

def set_s45(env):
    for a in env.agents:
        if getattr(a, 'memory_fsrs', None) is not None:
            for mem in a.memory_fsrs.memories.values():
                mem.S = 45.0

def evaluate_policy(threshold, severity, n_episodes=10, seed_offset=0):
    env = ECOSControlEnv(n_agents=30, max_ticks=300,
                         agent_config={'use_fsrs': True})
    returns, interventions, crisis_steps, zones = [], [], [], []
    for ep in range(n_episodes):
        obs, _ = env.reset(seed=seed_offset + ep)
        set_s45(env)
        obs = env._compute_obs()
        total_r = steps = n_int = crisis = zone = 0
        while True:
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += float(r); steps += 1
            if action[0] > 0.01: n_int += 1
            if obs[0] < 0.25: crisis += 1
            if 0.5 <= obs[0] <= 0.7: zone += 1
            if term or trunc: break
        returns.append(total_r); interventions.append(n_int)
        crisis_steps.append(crisis); zones.append(zone / steps * 100 if steps else 0)
    return {'avg_return': float(np.mean(returns)),
            'std_return': float(np.std(returns)),
            'avg_interventions': float(np.mean(interventions)),
            'avg_crisis': float(np.mean(crisis_steps)),
            'mean_zone_pct': float(np.mean(zones)),
            'per_ep_return': [float(round(float(x), 2)) for x in returns]}

def main():
    thresholds = [0.25, 0.35, 0.45, 0.55, 0.65]
    severities = [0.2, 0.4, 0.6, 0.8]
    if 0.3 not in thresholds: thresholds.append(0.3)
    if 0.6 not in severities: severities.append(0.6)
    results = {}
    start = time.time()
    for i, (thr, sev) in enumerate(itertools.product(thresholds, severities)):
        cfg = f"thr={thr:.2f},sev={sev:.2f}"
        res = evaluate_policy(thr, sev, n_episodes=10, seed_offset=i)
        results[cfg] = res
        print(f"[{i+1}/24] {cfg} -> return={res['avg_return']:.2f} +-{res['std_return']:.2f}, interv={res['avg_interventions']:.1f}, crisis={res['avg_crisis']:.1f}, zone={res['mean_zone_pct']:.2f}", flush=True)
    out = {'S': 45.0, 'n_agents': 30, 'max_ticks': 300,
           'episodes_per_config': 10, 'all_results': results,
           'elapsed_seconds': time.time() - start}
    with open(r"C:\Windows\Temp\jedc_pack\grid_s45.json", "w") as f:
        json.dump(out, f, indent=2)
    print("GRID_S45_DONE")

if __name__ == "__main__":
    main()
