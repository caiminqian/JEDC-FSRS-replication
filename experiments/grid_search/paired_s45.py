import sys, json
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
import numpy as np
from ecos.control.ecos_env import ECOSControlEnv

# v48 paired rerun at S=45: same design as same_seed.py (seed sets 10, 110,
# 10 episodes each, configs (0.45,0.40) vs (0.30,0.60)) plus the S override:
# after every reset set every FSRS lesson's S to 45.0, recompute obs.

def set_s45(env):
    for a in env.agents:
        if getattr(a, 'memory_fsrs', None) is not None:
            for mem in a.memory_fsrs.memories.values():
                mem.S = 45.0

def run(thr, sev, seed_offset):
    env = ECOSControlEnv(n_agents=30, max_ticks=300,
                         agent_config={'use_fsrs': True})
    rets, ints, cris, zones = [], [], [], []
    for ep in range(10):
        obs, _ = env.reset(seed=seed_offset + ep)
        set_s45(env)
        obs = env._compute_obs()
        total_r = steps = n_int = crisis = zone = 0
        while True:
            action = np.array([sev if obs[0] < thr else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += float(r); steps += 1
            if action[0] > 0.01: n_int += 1
            if obs[0] < 0.25: crisis += 1
            if 0.5 <= obs[0] <= 0.7: zone += 1
            if term or trunc: break
        rets.append(total_r); ints.append(n_int); cris.append(crisis)
        zones.append(zone / steps * 100 if steps else 0)
    out = {"thr": thr, "sev": sev, "S": 45.0, "seed_offset": seed_offset,
           "mean_return": float(np.mean(rets)), "std_return": float(np.std(rets)),
           "mean_interv": float(np.mean(ints)), "mean_crisis": float(np.mean(cris)),
           "mean_zone_pct": float(np.mean(zones)),
           "per_ep_return": [float(round(float(x), 2)) for x in rets]}
    print("PAIRED_S45 " + json.dumps(out), flush=True)
    return out

results = []
for so in (10, 110):
    results.append(run(0.45, 0.40, so))
    results.append(run(0.30, 0.60, so))
with open(r"C:\Windows\Temp\jedc_pack\paired_s45.json", "w") as f:
    json.dump(results, f, indent=2)
print("PAIRED_S45_DONE")
