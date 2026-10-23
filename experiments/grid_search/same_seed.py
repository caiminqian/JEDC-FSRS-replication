import sys, json, numpy as np
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
from ecos.control.ecos_env import ECOSControlEnv

def run(thr, sev, seed_offset):
    env = ECOSControlEnv(n_agents=30, max_ticks=300,
                         agent_config={'use_fsrs': True})
    rets, ints, cris, zones = [], [], [], []
    for ep in range(10):
        obs, _ = env.reset(seed=seed_offset + ep)
        total_r = steps = n_int = crisis = zone = 0
        while True:
            action = np.array([sev if obs[0] < thr else 0.0], dtype=np.float32)
            obs, r, term, trunc, info = env.step(action)
            total_r += r
            steps += 1
            if action[0] > 0.01:
                n_int += 1
            if obs[0] < 0.25:
                crisis += 1
            if 0.5 <= obs[0] <= 0.7:
                zone += 1
            if term or trunc:
                break
        rets.append(total_r)
        ints.append(n_int)
        cris.append(crisis)
        zones.append(zone / steps * 100 if steps else 0)
    out = {"thr": thr, "sev": sev, "seed_offset": seed_offset,
           "mean_return": float(np.mean(rets)), "std_return": float(np.std(rets)),
           "mean_interv": float(np.mean(ints)), "mean_crisis": float(np.mean(cris)),
           "mean_zone_pct": float(np.mean(zones)),
           "per_ep_return": [float(round(float(x), 2)) for x in rets]}
    print("SAMESEED " + json.dumps(out))
    return out

results = []
for so in (10, 110):
    results.append(run(0.45, 0.40, so))
    results.append(run(0.30, 0.60, so))
with open(r"C:\Windows\Temp\jedc_pack\same_seed.json", "w") as f:
    json.dump(results, f, indent=2)
print("SAMESEED_DONE")
