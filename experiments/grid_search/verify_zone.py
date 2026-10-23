import sys, numpy as np
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
from ecos.control.ecos_env import ECOSControlEnv

def zone_eval(threshold, severity, seed_offset):
    env = ECOSControlEnv(n_agents=30, max_ticks=300, agent_config={'use_fsrs': True})
    zone_pcts = []
    returns = []
    for ep in range(10):
        obs, _ = env.reset(seed=seed_offset + ep)
        total_r = steps = zone = 0
        while True:
            action = np.array([severity if obs[0] < threshold else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r
            steps += 1
            if 0.5 <= obs[0] <= 0.7:
                zone += 1
            if term or trunc:
                break
        zone_pcts.append(zone / steps * 100 if steps else 0)
        returns.append(total_r)
    print(f"ZONE thr={threshold} sev={severity} seed_offset={seed_offset} "
          f"mean_zone={np.mean(zone_pcts):.2f}% per_ep={['%.1f' % x for x in zone_pcts]} "
          f"mean_return={np.mean(returns):.2f}")

zone_eval(0.45, 0.40, 9)
zone_eval(0.30, 0.60, 22)
print("ZONE_DONE")
