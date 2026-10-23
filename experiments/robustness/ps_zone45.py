import sys, json, numpy as np
sys.path.insert(0, r"C:\Users\Administrator\Desktop\JEDC-FSRS-v43-replication\src")
from ecos.control.ecos_env import ECOSControlEnv

# Correct p/S sweep (v47). Fixes run.py: p and S are actually applied.
# p: network density, applied by rebuilding info_flow edges after reset
#    with common random numbers (RandomState(seed), rand < p) so networks
#    are nested across p for a given seed.
# S: common initial stability for all three FSRS lessons, set after reset.
#    This is NOT the default bank (5/3/2 for retail); it is the paper's
#    claimed S parameterisation, implemented explicitly and documented.
# Policy: fixed reference T=0.30, s=0.60 for all configs (no optimal claim).
# Seeds 1,2,3 (avoid seed=0, which ECOSControlEnv.reset treats as falsy).

def run_one(p, S, seed):
    env = ECOSControlEnv(n_agents=30, max_ticks=300,
                         agent_config={'use_fsrs': True})
    obs, _ = env.reset(seed=seed)
    # Rebuild network at density p
    g = env.world.graph
    for u, v, k in list(g.edges(keys=True)):
        g.remove_edge(u, v, k)
    rng = np.random.RandomState(seed)
    ids = [a.agent_id for a in env.agents]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if rng.rand() < p:
                env.world.add_edge(ids[i], ids[j], 'info_flow', weight=1.0)
                env.world.add_edge(ids[j], ids[i], 'info_flow', weight=1.0)
    # Set common initial S
    for a in env.agents:
        if getattr(a, 'memory_fsrs', None) is not None:
            for mem in a.memory_fsrs.memories.values():
                mem.S = float(S)
    obs = env._compute_obs()
    total_r = steps = n_int = crisis = zone = 0
    while True:
        action = np.array([0.60 if obs[0] < 0.30 else 0.0], dtype=np.float32)
        obs, r, term, trunc, info = env.step(action)
        total_r += float(r)
        steps += 1
        if action[0] > 0.01:
            n_int += 1
        if obs[0] < 0.25:
            crisis += 1
        if 0.5 <= obs[0] <= 0.7:
            zone += 1
        if term or trunc:
            break
    return total_r, n_int, crisis, zone / steps * 100 if steps else 0

results = {}
for p in (0.05,):
    for S in (45,):
        rets, ints, cris, zones = [], [], [], []
        for seed in (1, 2, 3):
            r, ni, cr, zo = run_one(p, S, seed)
            rets.append(r)
            ints.append(ni)
            cris.append(cr)
            zones.append(zo)
        out = {"p": p, "S": S, "seeds": [1, 2, 3],
               "mean_return": float(np.mean(rets)),
               "std_return": float(np.std(rets)),
               "mean_interv": float(np.mean(ints)),
               "mean_crisis": float(np.mean(cris)),
               "mean_zone_pct": float(np.mean(zones)),
               "per_ep_return": [float(round(x, 2)) for x in rets]}
        results[f"p={p},S={S}"] = out
        print("PS " + json.dumps(out))
        print("PSZONE per_ep_zone=" + str([round(x,1) for x in zones]))
with open(r"C:\Windows\Temp\jedc_pack\ps_zone45.json", "w") as f:
    json.dump(results, f, indent=2)
print("PS_DONE")
